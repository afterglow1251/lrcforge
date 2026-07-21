"""Lyrics draft types (pre-alignment: words known, timings not yet)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from lrcforge.domain._types import Confidence


class LyricsSource(StrEnum):
    ASR = "asr"  # transcribed — a draft, needs review
    USER = "user"  # supplied text (--lyrics-file) — authoritative


class LyricWord(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str


class LyricLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    words: tuple[LyricWord, ...]
    raw: str


class LyricsDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    lines: tuple[LyricLine, ...]
    lang: str
    source: LyricsSource
    confidence: Confidence | None = None  # None for authoritative USER text
    needs_review: bool
