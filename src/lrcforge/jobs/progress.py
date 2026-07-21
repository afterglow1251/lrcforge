"""ProgressReporter that records events onto the job in the store (thread-safe)."""

from __future__ import annotations

from lrcforge.domain.job import JobId
from lrcforge.domain.progress import ProgressEvent
from lrcforge.jobs.store import JobStore


class JobProgressReporter:
    def __init__(self, job_id: JobId, store: JobStore) -> None:
        self._job_id = job_id
        self._store = store

    def emit(self, event: ProgressEvent) -> None:
        self._store.append_event(self._job_id, event)
