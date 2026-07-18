from __future__ import annotations

from typing import Protocol

from lrcforge.domain.audio import VocalStem
from lrcforge.domain.lyrics import LyricsDraft


class LyricsProvider(Protocol):
    """Produce the words to align: transcription by default, or user-supplied text."""

    def fetch(self, stem: VocalStem, lang: str) -> LyricsDraft: ...
