from __future__ import annotations

from typing import Protocol

from lrcforge.domain.audio import VocalStem
from lrcforge.domain.language import LanguageResult


class LanguageDetector(Protocol):
    def detect(self, stem: VocalStem) -> LanguageResult: ...
