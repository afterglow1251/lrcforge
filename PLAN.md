# Plan — `lrcforge`: audio → karaoke LRC generator

> Status: **pending approval** (planning only — no files created, no code written yet).
> Standalone Python project under `~/Desktop/not_work/lrcforge/`. Swift `Sonar` app only consumes the `.lrc` (out of scope).

**Locked decisions:** no lyrics DB — always transcribe (with an optional `--lyrics-file` escape hatch); priority languages **UA / RU / EN** → default aligner **MMS** (multilingual); surface is **FastAPI + a minimal static frontend from M0**, CLI shares the same core.

---

## RALPLAN-DR summary

**Principles**
1. **Types are the contract.** Every pipeline stage is a `Protocol` with pydantic I/O models. No `Any` crosses a module boundary.
2. **Fakes-first.** The whole pipeline — including the web UI — runs end-to-end with *zero* ML models via DI swaps. Models are pluggable details.
3. **Honest output.** Transcribed text is a draft: it carries a confidence and a `needs_review` flag through to the LRC. Never presented as ground truth.
4. **Apple-Silicon-native where it pays.** Prefer MPS/MLX paths, always keep a CPU fallback.
5. **Reproducible envs.** `uv` lockfile, pinned torch stack, heavy ML deps isolatable behind an optional extra.

**Decision drivers (top 3)**
1. The accuracy ceiling is **singing transcription** — quality is the whole point, so the UI must make alignment quality *visible* (karaoke preview) to iterate fast.
2. **Dependency fragility** of the torch/ML stack must be contained so it never blocks the typed core or the web loop.
3. **Testability without GPUs/models** — DI fakes are mandatory for a fast feedback loop.

**Viable options (areas with real choices)**

| Area | Options | Decision |
|---|---|---|
| Forced alignment | A) **MMS / ctc-forced-aligner** (multilingual, good UA/RU) B) WhisperX (English-strong, per-language wav2vec2) C) torchaudio `forced_align` (max control) | **A (MMS) default** for UA/RU/EN; B swappable behind the `ForcedAligner` port. |
| ASR runtime (Apple Silicon) | A) **mlx-whisper** (Apple GPU via MLX) B) faster-whisper (CTranslate2, CPU int8, no MPS) C) openai-whisper (reference, slow) | Abstract behind `Transcriber` port. **mlx-whisper** default on Apple Silicon, faster-whisper elsewhere. |
| Long-running work over HTTP | A) **async job + progress stream (SSE)** B) synchronous request | **A** — processing is minutes/track; sync would time out. |
| Frontend | A) **static page (vanilla JS / htmx) served by FastAPI, no build step** B) React/Vite SPA | **A now** (fast, zero toolchain); B only if we later want something fancier. |

---

## 1. Project name & layout

Proposed name: **`lrcforge`** (alt: `karaline`, `versestamp`). Package `lrcforge`.

```
lrcforge/
  pyproject.toml            # uv-managed; core deps + [ml] extra
  uv.lock
  README.md
  src/lrcforge/
    domain/                 # pure types, zero heavy imports
      audio.py              # AudioRef, VocalStem
      language.py           # LanguageResult
      lyrics.py             # LyricsDraft, LyricLine, LyricWord, LyricsSource
      alignment.py          # AlignedWord, AlignedLine, AlignedLyrics
      lrc.py                # LrcDocument, LrcMetadata
      progress.py           # Stage, ProgressEvent
      errors.py             # domain exception hierarchy
    ports/                  # Protocol interfaces (the DI seams)
      audio_loader.py       # AudioLoader
      separator.py          # SourceSeparator
      language_detector.py  # LanguageDetector
      lyrics_provider.py    # LyricsProvider  (Transcription | UserFile)
      aligner.py            # ForcedAligner
      lrc_writer.py         # LrcWriter
      progress.py           # ProgressReporter
    adapters/               # concrete impls (heavy imports live ONLY here)
      audio/ffmpeg_loader.py
      separation/demucs_separator.py
      language/whisper_lid.py, voxlingua_lid.py
      lyrics/transcription_provider.py, userfile_provider.py
      alignment/mms_aligner.py, whisperx_aligner.py
      transcription/mlx_transcriber.py, faster_whisper_transcriber.py
      lrc/enhanced_lrc_writer.py
      progress/sse_reporter.py, log_reporter.py
      fakes/                # FakeSeparator, FakeTranscriber, FakeAligner, ... (tests + M0)
    pipeline/
      orchestrator.py       # AlignPipeline — injects all ports, emits progress
    jobs/
      store.py              # in-memory JobStore (job_id -> status/progress/result)
      worker.py             # single-worker thread executor (serialize ML jobs)
    di/
      providers.py          # dishka Provider classes
      container.py          # make_container(config)
    config.py               # pydantic-settings Settings (device, model sizes, paths)
    cli/app.py              # cyclopts CLI (thin over AlignPipeline)
    service/
      api.py                # FastAPI: POST /jobs, GET /jobs/{id}, GET /jobs/{id}/events (SSE)
      static/index.html     # drag-drop upload + progress + karaoke preview (audio + LRC highlight)
  tests/
    unit/                   # orchestration via fakes — no models
    golden/                 # LRC formatting golden files
    integration/            # @pytest.mark.integration — real models, small clip
    conftest.py             # container-with-fakes fixture
```

Layering rule (enforced by import-linter): `domain` ← `ports` ← `pipeline` ← `adapters`/`jobs`/`di`/`cli`/`service`. Heavy libs (torch, demucs, whisper*) may be imported **only** under `adapters/`.

---

## 2. Domain type model (pydantic v2, `frozen=True`)

Audio samples are **not** carried inside pydantic models (raw numpy buffers don't belong in serializable domain types). Instead `AudioRef`/`VocalStem` hold a path + metadata; the actual array is loaded lazily by adapters. Keeps domain types cheap, serializable, and JSON-safe for the web layer.

```python
# audio.py
class AudioRef(BaseModel):        # a decodable audio file + probed metadata
    path: Path
    sample_rate: int
    channels: int
    duration_s: float
class VocalStem(BaseModel):
    audio: AudioRef               # path to the isolated-vocals wav (or original if separated_by="none")
    separated_by: str             # "demucs:htdemucs" | "none"

# language.py
class LanguageResult(BaseModel):
    lang: str                     # ISO-639-1: "uk" | "ru" | "en" | ...
    confidence: float
    per_window: list[WindowVote]

# lyrics.py
class LyricsSource(StrEnum): ASR = "asr"; USER = "user"
class LyricWord(BaseModel): text: str
class LyricLine(BaseModel): words: list[LyricWord]; raw: str
class LyricsDraft(BaseModel):
    lines: list[LyricLine]
    lang: str
    source: LyricsSource
    confidence: float | None      # None for USER-supplied text
    needs_review: bool            # True when source == ASR

# alignment.py
class AlignedWord(BaseModel): text: str; start: float; end: float; score: float | None
class AlignedLine(BaseModel): words: list[AlignedWord]; start: float; end: float
class AlignedLyrics(BaseModel):
    lines: list[AlignedLine]
    lang: str
    source: LyricsSource
    needs_review: bool
    word_level: bool              # per-word timings trustworthy?

# lrc.py
class LrcMetadata(BaseModel): language: str; tool: str; source: LyricsSource; needs_review: bool
class LrcDocument(BaseModel):
    metadata: LrcMetadata
    def render(self, *, enhanced: bool) -> str: ...   # [mm:ss.xx] line-level or A2 <mm:ss.xx> word-level

# progress.py
class Stage(StrEnum): LOAD="load"; SEPARATE="separate"; DETECT_LANG="detect_lang"; TRANSCRIBE="transcribe"; ALIGN="align"; WRITE="write"; DONE="done"
class ProgressEvent(BaseModel): stage: Stage; pct: float; message: str
```

Timestamp monotonicity validated via model validators.

---

## 3. Ports (the DI seams)

```python
class AudioLoader(Protocol):
    def probe(self, path: Path) -> AudioRef: ...
class SourceSeparator(Protocol):
    def separate(self, audio: AudioRef) -> VocalStem: ...
class LanguageDetector(Protocol):
    def detect(self, stem: VocalStem) -> LanguageResult: ...
class LyricsProvider(Protocol):
    def fetch(self, stem: VocalStem, lang: str) -> LyricsDraft: ...
class ForcedAligner(Protocol):
    def align(self, stem: VocalStem, draft: LyricsDraft) -> AlignedLyrics: ...
class LrcWriter(Protocol):
    def to_document(self, aligned: AlignedLyrics) -> LrcDocument: ...
class ProgressReporter(Protocol):
    def emit(self, event: ProgressEvent) -> None: ...
```

`LyricsProvider` selection is trivial now (no DB): default `TranscriptionLyricsProvider` (Whisper), or `UserFileLyricsProvider` when `--lyrics-file` / an uploaded text is present. Both feed the same aligner; the seam stays because there are ≥2 real impls + fake.

---

## 4. Orchestration

```python
class AlignPipeline:
    def __init__(self, loader, separator, detector, lyrics, aligner, writer, progress): ...
    def run(self, path: Path, opts: RunOptions) -> LrcDocument:
        self.progress.emit(ProgressEvent(Stage.LOAD, 0, "probing"))
        audio  = self.loader.probe(path)
        stem   = self.separator.separate(audio) if opts.separate else VocalStem(audio, "none")
        lang   = opts.forced_lang or self.detector.detect(stem).lang
        draft  = self.lyrics.fetch(stem, lang)          # transcription, unless a user text was supplied
        aligned= self.aligner.align(stem, draft)
        return self.writer.to_document(aligned)
```

Every stage emits a `ProgressEvent`; the CLI prints them, the web pushes them over SSE. `needs_review` originates in `LyricsDraft` (ASR ⇒ True, user-supplied ⇒ False), rides through `AlignedLyrics`, lands in `LrcMetadata` and the karaoke UI (a "draft" badge).

---

## 5. dishka wiring, jobs & the web loop

- **`ModelsProvider` (`Scope.APP`, singletons):** Demucs model, Whisper/MLX model, MMS aligner model, LID model. Loaded once — multi-GB, slow init. Provided lazily.
- **`AdaptersProvider` (`Scope.APP`):** binds each `Protocol` to its concrete adapter, reading `Settings` for device/impl choice (mlx vs faster-whisper, mms vs whisperx).
- **`PipelineProvider` (`Scope.REQUEST`):** builds `AlignPipeline` per job. **The job outlives its HTTP request**, so the REQUEST scope is entered **manually inside the worker** (`with container(scope=Scope.REQUEST) as job_ctx: pipe = job_ctx.get(AlignPipeline)`), keyed to the job — NOT via the fastapi request lifecycle. The `dishka.integrations.fastapi` helper is used only for the lightweight `POST /jobs` / `GET /jobs/{id}` handlers.
- **Jobs:** `POST /jobs` stores a job, hands the blocking pipeline to a **single-worker thread** (`jobs/worker.py`) so torch never blocks the event loop and jobs serialize. `GET /jobs/{id}` returns status/result; `GET /jobs/{id}/events` is an SSE stream. In-memory store — local single-user tool, no Celery/Redis.
- **Two concurrency hazards to handle explicitly (Architect):** (1) the worker thread → async-SSE **progress bridge** — push `ProgressEvent`s across the boundary via `asyncio.run_coroutine_threadsafe` / a janus-style queue (this is the trickiest piece, not "SSE solved"); (2) `JobStore` is written by the worker and read by async handlers → **guard with a lock** (data race otherwise).
- **Memory:** three `Scope.APP` model singletons (Demucs + Whisper large-v3 ≈1.5–3 GB + MMS) resident together can exceed a 16 GB Mac. Lazy load defers first touch, not retention — consider unload-between-stages or document the RAM floor.

**Tests:** `make_test_container()` overrides `AdaptersProvider` with a `FakesProvider`. Orchestration + job + SSE tests run in milliseconds, no torch import (Principle 2). The **static frontend itself runs against the fakes container** — full drag-drop → progress → dummy karaoke loop with no models.

---

## 6. Dependencies & tooling

**Core (always):** `python>=3.12`, `pydantic>=2`, `pydantic-settings`, `cyclopts`, `dishka`, `fastapi`, `uvicorn`, `sse-starlette`, `numpy`, `soundfile`/`av` (decode), `structlog`, `platformdirs`.
**Dev:** `uv`, `ruff`, `mypy` (strict) or `pyright`, `pytest`, `hypothesis`, `import-linter`, `syrupy` (golden), `httpx` (API tests).
**ML extras — split so the default path never has to satisfy whisperx's pins (Architect):**
- `[ml]` (default): `torch`, `torchaudio`, `demucs`, `ctc-forced-aligner` (MMS).
- `[mlx]`: `mlx-whisper` (Apple GPU, non-torch → isolates the ASR runtime from the torch conflict).
- `[whisperx]`: `whisperx` isolated (the most aggressively version-pinned offender — opt-in for the bake-off only).
- optional `[lid]`: `speechbrain` (VoxLingua LID).
The default install (`[ml]` + `[mlx]`) co-resolves to demucs + torchaudio + ctc-forced-aligner — tractable; whisperx never enters unless explicitly selected.

**Risky pins to call out explicitly:**
- `torch`/`torchaudio` versions are **coupled** and pinned indirectly by `demucs` and `whisperx` → classic resolution conflict. Pin all in `uv.lock`; if they can't co-resolve, isolate the aligner impl or run ML in a separate venv/process.
- Model weight downloads on first run (Demucs, Whisper large-v3 ≈ 1.5–3 GB, MMS). Cache dir via `platformdirs`; document offline pre-fetch.
- **Apple Silicon:** Demucs on MPS. CTranslate2 (faster-whisper) has **no MPS** → CPU int8, or mlx-whisper (GPU). WhisperX alignment on MPS partial → CPU fallback. Expect **minutes/track** — the SSE progress UI exists precisely because of this.
- Licensing: Whisper MIT, Demucs MIT (htdemucs weights research-only), MMS/wav2vec2 vary (some CC-BY-NC). Fine for personal/experimental; flag NC before any distribution.

---

## 7. CLI & web surface

**CLI (same core):**
```
lrcforge align  song.mp3 -o song.lrc [--lang auto|uk|ru|en] [--word-level/--line-level]
                [--device auto|cpu|mps] [--model large-v3] [--no-separation] [--lyrics-file words.txt]
lrcforge lang   song.mp3            # detect language + confidence
lrcforge serve  [--port 8000]       # launch the FastAPI + static UI
```
**Web:** `POST /jobs` (multipart audio, optional lyrics text + opts) → `job_id`; `GET /jobs/{id}` → status + LRC when done; `GET /jobs/{id}/events` → SSE progress. Static `index.html`: drag-drop a file → live per-stage progress → **karaoke preview** (`<audio>` + synced line/word highlight from the produced LRC) → download `.lrc`. The preview is the quality-inspection tool.

---

## 8. Phased milestones (risk-first ordering — per Architect review)

> **Chosen sequencing:** spike → typed core → real models → web last. The one genuine unknown (is singing-ASR usable on UA/RU?) is answered on day 1, *before* the architecture is built around it. The web/jobs/SSE surface lands with real alignment (M5), where the karaoke preview finally previews real timings rather than fake evenly-spaced ones.

- **M-spike — viability (day 1, throwaway, NOT in `src/`).** Flat script, real models: `ffmpeg decode → demucs → mlx-whisper → ctc-forced-aligner (MMS) → write LRC`. Run on one UA + one RU + one EN clip. Sole deliverable: a judgment on whether transcription+alignment quality clears a usable bar. Throw the code away; keep the answer + the three reference clips (they become alignment-eval fixtures). This also shakes out the torch/demucs/aligner install conflict early.
- **M0 — Typed core + CLI on fakes, zero ML.** uv/ruff/mypy/pytest/import-linter; frozen domain types; all ports; fakes; a plain `Scope.APP` dishka composition root (no REQUEST scope yet). Verify: `lrcforge align fixture.wav` emits a valid LRC on fakes; mypy strict + import-linter green.
- **M1 — Real LRC writer + real audio probe/decode.** Golden tests for standard + A2 formatting from fixed `AlignedLyrics`. Still fake ML.
- **M2 — Demucs separation** behind the port (productionize the spike). Verify stem isolates vocals; visible via `lrcforge separate`.
- **M3 — Language ID** (windowed vote). Verify correct lang on the UA/RU/EN clips.
- **M4 — Transcription** (mlx-whisper) behind the port → rough LRC via CLI. `needs_review=True` propagates.
- **M5 — Forced alignment (MMS)** → word-level A2 **+ the web/jobs/SSE/dishka-REQUEST loop lands here** (FastAPI, job store, worker thread, SSE progress, static karaoke preview). Now the preview shows *real* timings. **Aligner eval uses `--lyrics-file` with a known-correct reference** to separate ASR error from alignment error; MMS-vs-WhisperX bake-off on that controlled basis.
- **M6 (opt) — polish:** batch mode, stem/model caching, live cancel (`DELETE /jobs/{id}`), nicer UI.

---

## 9. Testing strategy

- **Unit (default, fast):** orchestration + job/worker + SSE via dishka fakes; no torch import.
- **Types:** mypy strict as a CI gate; import-linter enforces layering (no heavy imports outside `adapters`).
- **Golden:** LRC rendering (standard + enhanced) via syrupy.
- **Property (hypothesis):** timestamp monotonicity; LRC parse↔render round-trip.
- **API:** httpx against the fakes container — job lifecycle + SSE event sequence.
- **Integration (`@pytest.mark.integration`, opt-in):** one small real clip through real models — assert detected language, monotonic timestamps, loose WER ceiling. Excluded from the default run.

---

## 10. Risks & open questions

1. **Singing-ASR accuracy is the hard ceiling** — unknown songs yield error-laden text; presented as a draft (`needs_review`). A manual edit/tap-sync step (cf. Linear AFT-31) is the real completion of the flow — the karaoke preview is where you'd spot what to fix.
2. **LID on code-switching / instrumental intros** — mitigated by windowed voting, still imperfect.
3. **Alignment drift** on remixes, repeats, ad-libs, non-lyric vocals.
4. **torch/torchaudio/demucs/whisperx co-resolution** — the single biggest engineering risk; may force process/venv isolation of the aligner.
5. **Processing time** — minutes/track on Apple Silicon; the SSE progress UI and (later) caching address the UX.
6. **Aligner default** MMS vs WhisperX for UA/RU — settle empirically in M5 via the karaoke preview.

**Resolved:** no lyrics DB (always transcribe; `--lyrics-file` optional escape hatch). Priority languages UA/RU/EN ⇒ MMS default aligner. Surface = FastAPI + static frontend from M0.
