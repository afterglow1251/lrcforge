"""Runs one job's pipeline. Enters the dishka REQUEST scope MANUALLY here (keyed to the
job) — NOT via the FastAPI request lifecycle, because the job outlives its HTTP request
(Architect fix). Runs on the worker thread; must never let an exception escape."""

from __future__ import annotations

import traceback
from pathlib import Path

from dishka import Container

from lrcforge.domain.errors import LrcforgeError
from lrcforge.domain.job import JobId
from lrcforge.domain.lrc import render_lrc
from lrcforge.jobs.context import JobContext
from lrcforge.jobs.store import JobStore
from lrcforge.pipeline.options import RunOptions
from lrcforge.pipeline.orchestrator import AlignPipeline


class JobExecutor:
    def __init__(self, container: Container, store: JobStore) -> None:
        self._container = container
        self._store = store

    def execute(self, job_id: JobId, audio: Path, opts: RunOptions) -> None:
        try:
            with self._container(context={JobContext: JobContext(job_id)}) as request_container:
                pipeline = request_container.get(AlignPipeline)
                doc = pipeline.run(audio, opts)
            text = render_lrc(doc, enhanced=opts.enhanced)
            self._store.complete(job_id, text, doc.metadata)
        except LrcforgeError as exc:
            traceback.print_exc()  # surface the real cause in the server console
            self._store.fail(job_id, str(exc))
        except Exception as exc:  # worker thread must not die silently
            traceback.print_exc()
            self._store.fail(job_id, f"unexpected error: {exc}")
