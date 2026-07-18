from __future__ import annotations

from typing import Protocol

from lrcforge.domain.progress import ProgressEvent


class ProgressReporter(Protocol):
    def emit(self, event: ProgressEvent) -> None: ...
