"""Job runners: threaded (production — one worker so GPU/unified-memory access serialises)
and inline (tests — deterministic, no threads)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Protocol

from lrcforge.domain.job import JobId
from lrcforge.jobs.executor import JobExecutor
from lrcforge.pipeline.options import RunOptions


class JobRunner(Protocol):
    def submit(self, job_id: JobId, audio: Path, opts: RunOptions) -> None: ...


class ThreadedJobRunner:
    def __init__(self, executor: JobExecutor, max_workers: int = 1) -> None:
        self._executor = executor
        self._pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="lrcforge-job"
        )

    def submit(self, job_id: JobId, audio: Path, opts: RunOptions) -> None:
        self._pool.submit(self._executor.execute, job_id, audio, opts)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False)


class InlineJobRunner:
    """Runs the job synchronously in the caller's thread (used by tests)."""

    def __init__(self, executor: JobExecutor) -> None:
        self._executor = executor

    def submit(self, job_id: JobId, audio: Path, opts: RunOptions) -> None:
        self._executor.execute(job_id, audio, opts)
