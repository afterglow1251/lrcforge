from __future__ import annotations

from typing import Protocol

from lrcforge.domain.alignment import AlignedLyrics
from lrcforge.domain.audio import VocalStem
from lrcforge.domain.lyrics import LyricsDraft


class ForcedAligner(Protocol):
    def align(self, stem: VocalStem, draft: LyricsDraft) -> AlignedLyrics: ...
