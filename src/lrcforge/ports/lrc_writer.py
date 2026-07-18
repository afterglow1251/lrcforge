from __future__ import annotations

from typing import Protocol

from lrcforge.domain.alignment import AlignedLyrics
from lrcforge.domain.lrc import LrcDocument


class LrcWriter(Protocol):
    def to_document(self, aligned: AlignedLyrics) -> LrcDocument: ...
