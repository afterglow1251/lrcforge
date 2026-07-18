"""Audio references. Raw sample arrays are intentionally kept OUT of these models
(adapters load them lazily from the path) so domain types stay cheap and serializable
and each stage can decode/resample to whatever sample rate it needs."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class AudioRef(BaseModel):
    """A decodable audio file plus probed metadata."""

    model_config = ConfigDict(frozen=True)

    path: Path
    sample_rate: int
    channels: int
    duration_s: float


class VocalStem(BaseModel):
    """An (ideally vocals-only) audio reference."""

    model_config = ConfigDict(frozen=True)

    audio: AudioRef
    separated_by: str  # e.g. "demucs:htdemucs" | "none" | "fake"
