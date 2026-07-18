# lrcforge

Audio → karaoke `.lrc` generator: `song.mp3` → `song.lrc` with a detected language tag
and word/line-level timestamps. Pipeline: **Demucs** vocal separation → **language ID** →
**Whisper** transcription (no lyrics DB — always transcribe; optional `--lyrics-file`) →
**forced alignment** (MMS default) → LRC. Standalone tool; the Swift `Sonar` app just
consumes the `.lrc`.

See [`PLAN.md`](PLAN.md) for the full design, and [`spike/`](spike/) for the throwaway
viability spike (run that first — it answers whether singing-ASR is usable on UA/RU/EN).

## Status: M0 — typed core + CLI on fakes, zero ML

The whole pipeline runs end-to-end with **no ML models** via DI-swapped fakes. This lets
the orchestration, types, and CLI be built and tested in milliseconds. Real models
(Demucs, LID, Whisper, MMS aligner) get swapped in one stage at a time (M2–M5).

## Dev setup

```sh
cd ~/Desktop/not_work/lrcforge
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Verify (M0 gate)

```sh
mypy               # strict, incl. pydantic plugin
lint-imports       # import-linter: heavy ML imports confined to adapters/
pytest             # unit tests via fakes (no models)
lrcforge align fixture.wav      # prints a valid LRC (fakes)
python -m lrcforge lang x.wav   # -> "uk (1.00)"
```

## Architecture (ports & adapters)

- `domain/` — frozen pydantic types. No ML/web imports (enforced by import-linter).
- `ports/` — `Protocol` seams: `AudioLoader`, `SourceSeparator`, `LanguageDetector`,
  `LyricsProvider`, `ForcedAligner`, `LrcWriter`, `ProgressReporter`.
- `adapters/` — concrete impls; the only place heavy ML libs may be imported.
  `adapters/fakes/` powers M0 and the tests.
- `pipeline/` — `AlignPipeline`: the single orchestration path, emits a progress event
  per stage.
- `di/` — dishka composition root (M0: one `Scope.APP` container binding fakes).
- `cli/` — cyclopts CLI (`align`, `lang`).

The FastAPI + static karaoke-preview web surface and the dishka `REQUEST` scope land at
M5, together with real forced alignment (see `PLAN.md §8`).
