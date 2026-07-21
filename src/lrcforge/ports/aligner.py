from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from lrcforge.domain.alignment import AlignedLyrics
from lrcforge.domain.audio import VocalStem
from lrcforge.domain.lyrics import LyricsDraft

# (fraction 0..1, human message) — reported during the (long) align stage.
AlignProgress = Callable[[float, str], None]


class ForcedAligner(Protocol):
    def align(
        self, stem: VocalStem, draft: LyricsDraft, on_progress: AlignProgress | None = None
    ) -> AlignedLyrics: ...
