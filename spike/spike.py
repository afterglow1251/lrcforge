#!/usr/bin/env python3
"""
lrcforge spike — throwaway viability test.

Answers ONE question: is singing transcription good enough on UA/RU/EN to make a
usable karaoke LRC?  This is NOT production code — no types, no DI, no ports.
Delete it once we have the answer; keep the reference clips.

Pipeline:  decode -> (Demucs vocal separation) -> mlx-whisper (word timestamps) -> .lrc

Judge the result by playing the track against the produced .lrc (any LRC-capable
player), or just read the printed lines against what you hear.

Usage:
    python spike.py song.mp3                 # separate + transcribe, word-level LRC
    python spike.py song.mp3 --no-sep        # skip Demucs (compare quality)
    python spike.py song.mp3 --lang uk       # force language instead of auto-detect
    python spike.py song.mp3 --line          # line-level LRC instead of word-level A2
"""
from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path


def log(msg: str) -> None:
    print(f"[spike] {msg}", file=sys.stderr, flush=True)


def separate_vocals(src: Path) -> Path:
    """Demucs htdemucs -> isolated vocal wav. Returns the vocals.wav path."""
    from demucs.api import Separator, save_audio

    t = time.time()
    log("loading demucs htdemucs ...")
    sep = Separator(model="htdemucs")
    log("separating vocals (slow part) ...")
    _origin, stems = sep.separate_audio_file(src)
    out = Path(tempfile.mkdtemp()) / "vocals.wav"
    save_audio(stems["vocals"], out, samplerate=sep.samplerate)
    log(f"vocals -> {out}  ({time.time() - t:.1f}s)")
    return out


def transcribe(audio: Path, model_repo: str, lang: str | None) -> dict:
    import mlx_whisper

    t = time.time()
    log(f"transcribing with {model_repo} (lang={lang or 'auto'}) ...")
    res = mlx_whisper.transcribe(
        str(audio),
        path_or_hf_repo=model_repo,
        word_timestamps=True,
        language=lang,  # None -> auto-detect
    )
    log(f"detected language: {res.get('language')}  ({time.time() - t:.1f}s)")
    return res


def _ts(sec: float) -> str:
    m, s = divmod(max(0.0, sec), 60)
    return f"{int(m):02d}:{s:05.2f}"


def to_lrc(res: dict, *, enhanced: bool) -> str:
    lines = [f"[la:{res.get('language', '??')}]", "[re:lrcforge-spike]"]
    for seg in res["segments"]:
        start = _ts(seg["start"])
        if enhanced and seg.get("words"):
            body = "".join(f"<{_ts(w['start'])}>{w['word']}" for w in seg["words"]).strip()
            lines.append(f"[{start}]{body}")
        else:
            lines.append(f"[{start}]{seg['text'].strip()}")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="lrcforge throwaway spike")
    ap.add_argument("audio", type=Path)
    ap.add_argument("-o", "--out", type=Path, help="output .lrc (default: alongside input)")
    ap.add_argument("--model", default="mlx-community/whisper-large-v3")
    ap.add_argument("--lang", default=None, help="force language (uk/ru/en); default auto-detect")
    ap.add_argument("--no-sep", action="store_true", help="skip Demucs separation")
    ap.add_argument("--line", action="store_true", help="line-level LRC instead of word-level A2")
    args = ap.parse_args()

    if not args.audio.exists():
        sys.exit(f"no such file: {args.audio}")

    total = time.time()
    vocal = args.audio if args.no_sep else separate_vocals(args.audio)
    res = transcribe(vocal, args.model, args.lang)
    lrc = to_lrc(res, enhanced=not args.line)

    out = args.out or args.audio.with_suffix(".lrc")
    out.write_text(lrc, encoding="utf-8")
    log(f"wrote {out}  (total {time.time() - total:.1f}s)")
    print(lrc)


if __name__ == "__main__":
    main()
