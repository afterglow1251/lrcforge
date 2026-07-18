"""Aligned lyrics: words/lines carrying start/end timestamps."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from lrcforge.domain.lyrics import LyricsSource


class AlignedWord(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    start: float
    end: float
    score: float | None = None

    @model_validator(mode="after")
    def _check_span(self) -> Self:
        if self.end < self.start:
            raise ValueError(f"word end {self.end} precedes start {self.start}")
        return self


class AlignedLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    words: tuple[AlignedWord, ...]
    start: float
    end: float

    @model_validator(mode="after")
    def _check_monotonic(self) -> Self:
        prev = self.start
        for w in self.words:
            if w.start < prev:
                raise ValueError("words within a line must be non-decreasing in time")
            prev = w.start
        return self


class AlignedLyrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    lines: tuple[AlignedLine, ...]
    lang: str
    source: LyricsSource
    needs_review: bool
    word_level: bool  # whether per-word timings are trustworthy

    @model_validator(mode="after")
    def _check_lines_monotonic(self) -> Self:
        prev = 0.0
        for line in self.lines:
            if line.start < prev:
                raise ValueError("lines must be non-decreasing in start time")
            prev = line.start
        return self
