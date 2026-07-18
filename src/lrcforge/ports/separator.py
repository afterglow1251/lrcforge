from __future__ import annotations

from typing import Protocol

from lrcforge.domain.audio import AudioRef, VocalStem


class SourceSeparator(Protocol):
    def separate(self, audio: AudioRef) -> VocalStem: ...
