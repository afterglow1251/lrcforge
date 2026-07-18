# lrcforge — spike (throwaway)

One question this answers: **is singing transcription good enough on UA/RU/EN to make a usable karaoke `.lrc`?**

Not production. No types, no DI, no web. Once we know the answer, delete this folder and keep the reference clips as alignment-eval fixtures. Then M0 (typed core) begins.

## Setup (Apple Silicon)

```sh
# ffmpeg is needed to decode mp3/m4a (Demucs + Whisper use it)
brew install ffmpeg

cd ~/Desktop/not_work/lrcforge/spike
uv venv --python 3.12
source .venv/bin/activate
uv pip install "demucs" "mlx-whisper"
```

- `demucs` pulls `torch` + `torchaudio` (a few hundred MB) and the htdemucs weights on first run.
- `mlx-whisper` is **Apple-Silicon only** (Metal via MLX). `whisper-large-v3` weights (~3 GB) download on first transcribe.
- First run is slow (model downloads + separation). Later runs reuse cached models.

> This install is also the first real test of the torch/demucs dependency resolution the plan flags as risk #1. If it fights, note the error — that's signal for M0.

## Run

Pick one UA, one RU, one EN track (ideally a remix / something without existing synced lyrics):

```sh
python spike.py ~/Music/some_ukrainian_remix.mp3        # word-level A2 LRC
python spike.py ~/Music/track.mp3 --no-sep              # skip Demucs, compare
python spike.py ~/Music/track.mp3 --lang uk             # force language
python spike.py ~/Music/track.mp3 --line                # line-level only
```

Output: a `.lrc` next to the input, plus the lines printed to stdout and per-stage timing to stderr.

## How to judge (this is the actual deliverable)

For each clip, eyeball / listen and answer:

1. **Text accuracy** — are the words mostly right, or garbage? (This is the ceiling. If it's garbage on UA/RU, that's the finding — we adjust scope before building.)
2. **With vs. without Demucs** (`--no-sep`) — how much does separation help?
3. **Timing plausibility** — do the word/line timestamps roughly track the vocal?
4. **Language detection** — did it get uk/ru/en right?

Bring the 3 `.lrc` files (or just your verdict) back and we decide: proceed to M0 as planned, or adjust (e.g. drop word-level, lean on manual editing, try a different model).

## Notes / knobs to try if quality is poor

- Bigger/other model: `--model mlx-community/whisper-large-v3-turbo` (faster) or a singing-fine-tuned repo.
- Word-level timing here uses Whisper's own cross-attention DTW. The real project will use **MMS forced alignment** (more accurate, and required for the known-text path) — but for "is the text usable?" this is enough.
- If decode fails, confirm `ffmpeg` is on PATH.
