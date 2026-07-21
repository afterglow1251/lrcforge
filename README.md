# lrcforge

Audio → karaoke `.lrc` generator: `song.mp3` → `song.lrc` with a detected language tag
and word/line-level timestamps. Pipeline: **Demucs** vocal separation → **language ID** →
**Whisper** transcription (no lyrics DB — always transcribe; optional `--lyrics-file`) →
**MMS forced alignment** → LRC. Standalone tool; the Swift `Sonar` app just consumes the
`.lrc`. Priority languages **UA / RU / EN**.

See [`PLAN.md`](PLAN.md) for the design, [`spike/`](spike/) for the throwaway viability
spike, and [`DEPLOY.md`](DEPLOY.md) for deployment + Sonar integration.

## Status

The full pipeline is built (M0–M5): typed ports/adapters core, real ML adapters (Demucs,
faster-whisper/mlx LID + transcription, MMS aligner), a cyclopts CLI, and a FastAPI service
with a karaoke-preview web UI (jobs + SSE progress).

> **The real ML adapters are written but not yet exercised against real models/audio** —
> that validation is the M-spike (run `spike/` on a few real UA/RU/EN tracks). Everything
> is unit-tested via zero-model fakes; the quality of real transcription/alignment is the
> open question the spike answers.

## Dev setup

```sh
cd ~/Desktop/not_work/lrcforge
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e ".[dev,service]"     # add ,ml,mlx for real inference (heavy)
```

## Verify (all gates, no models)

```sh
ruff check . && mypy && lint-imports && pytest      # ruff · mypy --strict · import-linter · pytest
lrcforge align x.wav --fake                          # dummy LRC via fakes (no models)
```

## Use

```sh
# CLI (needs the ML extras + ffmpeg installed for real runs)
lrcforge align song.mp3 -o song.lrc [--lang uk] [--no-separation] [--line]
lrcforge lang  song.mp3                               # detect language
lrcforge align song.mp3 --fake                        # zero-model smoke of the plumbing

# Web service + karaoke-preview UI
lrcforge serve                       # http://127.0.0.1:8000  (real pipeline)
lrcforge serve --fake                # UI/plumbing demo, no models
```

Config via env (prefix `LRCFORGE_`): `DEVICE`, `TRANSCRIBER` (faster|mlx), `FASTER_MODEL`,
`LID_MODEL`, `ALIGNER`. See `DEPLOY.md`.

## Architecture (ports & adapters)

- `domain/` — frozen pydantic types with constrained scalars (no ML/web imports; enforced
  by import-linter).
- `ports/` — `Protocol` seams: AudioLoader, SourceSeparator, LanguageDetector,
  LyricsProvider, ForcedAligner, LrcWriter, ProgressReporter.
- `adapters/` — concrete impls; the only place heavy ML libs may be imported (lazy, so the
  fakes path never pulls torch). `adapters/fakes/` powers the zero-model path + tests.
- `pipeline/` — `AlignPipeline`: the single orchestration path, emits a progress event per
  stage.
- `jobs/` — thread-safe JobStore, JobExecutor (enters the dishka REQUEST scope per job),
  threaded/inline runners.
- `di/` — dishka composition roots: `build_container` (CLI, APP scope) and `build_web_container`
  (web, REQUEST-scoped pipeline + progress).
- `service/` — FastAPI (`/jobs`, SSE `/jobs/{id}/events`) + the static karaoke-preview page.
- `cli/` — cyclopts CLI (`align`, `lang`, `serve`).
