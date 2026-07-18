from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RunOptions:
    separate: bool = True
    forced_lang: str | None = None  # None -> auto-detect
    lyrics_file: Path | None = None  # supplied text -> authoritative align-only path
    enhanced: bool = True  # word-level A2 output vs. line-level
