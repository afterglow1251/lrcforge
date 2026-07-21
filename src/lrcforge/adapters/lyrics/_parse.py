"""Pure conversions: raw text / Whisper segments -> LyricsDraft. No models, no I/O."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from lrcforge.domain.lyrics import LyricLine, LyricsDraft, LyricsSource, LyricWord


def _split_words(raw: str) -> tuple[LyricWord, ...]:
    return tuple(LyricWord(text=w) for w in raw.split())


def lines_to_draft(
    raw_lines: Iterable[str],
    *,
    lang: str,
    source: LyricsSource,
    needs_review: bool,
    confidence: float | None = None,
) -> LyricsDraft:
    lines = tuple(
        LyricLine(words=_split_words(raw), raw=raw.strip())
        for raw in raw_lines
        if raw.strip()
    )
    return LyricsDraft(
        lines=lines,
        lang=lang,
        source=source,
        confidence=confidence,
        needs_review=needs_review,
    )


def segments_to_draft(segments: Iterable[Mapping[str, Any]], *, lang: str) -> LyricsDraft:
    """Whisper transcription -> a draft (text only; timings come from the aligner)."""
    raw_lines = [str(seg["text"]) for seg in segments]
    return lines_to_draft(
        raw_lines,
        lang=lang,
        source=LyricsSource.ASR,
        needs_review=True,  # transcription is always a draft
    )
