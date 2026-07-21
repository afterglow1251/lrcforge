# Deploying lrcforge

## The honest caveat about free tiers

lrcforge runs **torch + Demucs + faster-whisper + MMS forced alignment** and downloads
**multi-GB model weights** on first use. A track takes **minutes** of CPU. That means:

- **render.com free tier (and most free tiers) will not work** — 512 MB RAM, no persistent
  disk, short build windows, and spin-down on idle. The models won't even load.
- A **paid instance** (≈2 GB+ RAM, persistent disk for the weight cache) is required for
  real transcription/alignment. Even then, CPU inference is slow — fine for "play with it",
  not for high throughput.
- For a **UI-only demo**, deploy in `--fake` mode (zero models, instant dummy LRC): set the
  container command to `lrcforge serve --host 0.0.0.0 --port 8000 --fake`.

Realistically this service is best run **locally on your Mac** (where mlx-whisper can use the
GPU) rather than on a cheap cloud box. Deploy is provided for completeness.

## Docker (any host)

```sh
docker build -t lrcforge .
docker run -p 8000:8000 lrcforge          # real pipeline (CPU, small models)
# open http://localhost:8000
```

## render.com

`render.yaml` is a Docker blueprint (`plan: standard` — not free). Point a new Blueprint
at the repo. Override `LRCFORGE_FASTER_MODEL` / `LRCFORGE_DEVICE` via env if needed.

## Configuration (env, prefix `LRCFORGE_`)

| var | default | notes |
|---|---|---|
| `LRCFORGE_DEVICE` | `auto` | `cpu` / `mps` / `cuda` |
| `LRCFORGE_TRANSCRIBER` | `faster` | `faster` (portable) or `mlx` (Apple GPU) |
| `LRCFORGE_FASTER_MODEL` | `large-v3` | use `small`/`medium` on constrained hosts |
| `LRCFORGE_LID_MODEL` | `small` | language-ID model size |
| `LRCFORGE_ALIGNER` | `mms` | forced aligner |

## Sonar integration (next step)

Sonar (the Swift app) consumes `.lrc`. Two shapes:
1. **Batch/CLI:** run `lrcforge align song.mp3 -o song.lrc` and drop the `.lrc` next to the
   track — Sonar already reads sidecar `.lrc`.
2. **Service:** Sonar POSTs the audio to `/jobs`, streams progress over SSE, then fetches the
   `.lrc`. Same contract the web UI uses.
