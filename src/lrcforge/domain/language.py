"""Language identification result types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WindowVote(BaseModel):
    """A per-window language vote (windowed detection is averaged into a result)."""

    model_config = ConfigDict(frozen=True)

    start_s: float
    lang: str
    confidence: float


class LanguageResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    lang: str  # ISO-639-1, e.g. "uk" | "ru" | "en"
    confidence: float
    per_window: tuple[WindowVote, ...] = ()
