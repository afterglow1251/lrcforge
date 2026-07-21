"""Thread-safe in-memory job store. Written by the worker thread, read by async handlers,
so every access is guarded by a lock (Architect: JobStore is a cross-thread data race
otherwise). Jobs are immutable; updates replace the stored snapshot."""

from __future__ import annotations

import threading

from lrcforge.domain.job import Job, JobId, JobStatus
from lrcforge.domain.lrc import LrcMetadata
from lrcforge.domain.progress import ProgressEvent


class JobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[JobId, Job] = {}

    def create(self, job_id: JobId) -> Job:
        job = Job(id=job_id, status=JobStatus.PENDING)
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: JobId) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _update(self, job_id: JobId, **changes: object) -> None:
        with self._lock:
            job = self._jobs[job_id]
            self._jobs[job_id] = job.model_copy(update=changes)

    def append_event(self, job_id: JobId, event: ProgressEvent) -> None:
        with self._lock:
            job = self._jobs[job_id]
            self._jobs[job_id] = job.model_copy(
                update={"events": (*job.events, event), "status": JobStatus.RUNNING}
            )

    def complete(self, job_id: JobId, lrc: str, metadata: LrcMetadata) -> None:
        self._update(job_id, status=JobStatus.DONE, lrc=lrc, metadata=metadata)

    def fail(self, job_id: JobId, error: str) -> None:
        self._update(job_id, status=JobStatus.ERROR, error=error)
