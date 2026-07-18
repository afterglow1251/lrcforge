from __future__ import annotations

from pathlib import Path
from typing import Protocol

from lrcforge.domain.audio import AudioRef


class AudioLoader(Protocol):
    def probe(self, path: Path) -> AudioRef: ...
