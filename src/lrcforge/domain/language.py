"""Language identification result types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from lrcforge.domain._types import Confidence, Seconds


class WindowVote(BaseModel):
    """A per-window language vote (windowed detection is averaged into a result)."""

    model_config = ConfigDict(frozen=True)

    start_s: Seconds
    lang: str
    confidence: Confidence


class LanguageResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    lang: str  # ISO-639-1, e.g. "uk" | "ru" | "en"
    confidence: Confidence
    per_window: tuple[WindowVote, ...] = ()
