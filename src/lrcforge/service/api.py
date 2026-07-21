"""FastAPI routes. Long-running work is a job: POST /jobs returns immediately, progress
streams over SSE (poll-based — sidesteps the fragile thread->event-loop bridge), and the
finished LRC is fetched from GET /jobs/{id}."""

from __future__ import annotations

import asyncio
import json
import tempfile
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from lrcforge.domain.job import JobId, JobStatus
from lrcforge.jobs.runner import JobRunner
from lrcforge.jobs.store import JobStore
from lrcforge.pipeline.options import RunOptions

_STATIC = Path(__file__).parent / "static"


def create_app(*, runner: JobRunner, store: JobStore) -> FastAPI:
    app = FastAPI(title="lrcforge")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return (_STATIC / "index.html").read_text(encoding="utf-8")

    @app.post("/jobs")
    async def create_job(
        audio: UploadFile,
        lang: Annotated[str | None, Form()] = None,
        no_separation: Annotated[bool, Form()] = False,
        line: Annotated[bool, Form()] = False,
    ) -> dict[str, str]:
        job_id = JobId(uuid.uuid4().hex)
        suffix = Path(audio.filename or "audio").suffix or ".bin"
        dest = Path(tempfile.mkdtemp(prefix="lrcforge-upload-")) / f"input{suffix}"
        dest.write_bytes(await audio.read())
        store.create(job_id)
        opts = RunOptions(separate=not no_separation, forced_lang=lang, enhanced=not line)
        runner.submit(job_id, dest, opts)
        return {"job_id": job_id}

    @app.get("/jobs/{job_id}")
    async def get_job(job_id: str) -> dict[str, object]:
        job = store.get(JobId(job_id))
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        return {
            "id": job.id,
            "status": job.status.value,
            "lrc": job.lrc,
            "language": job.metadata.language if job.metadata else None,
            "needs_review": job.metadata.needs_review if job.metadata else None,
            "error": job.error,
        }

    @app.get("/jobs/{job_id}/events")
    async def job_events(job_id: str) -> EventSourceResponse:
        jid = JobId(job_id)

        async def stream() -> AsyncIterator[dict[str, str]]:
            cursor = 0
            while True:
                job = store.get(jid)
                if job is None:
                    yield {"event": "error", "data": json.dumps({"error": "unknown job"})}
                    return
                for event in job.events[cursor:]:
                    yield {"event": "progress", "data": event.model_dump_json()}
                cursor = len(job.events)
                if job.status in (JobStatus.DONE, JobStatus.ERROR):
                    payload = {"status": job.status.value, "error": job.error}
                    yield {"event": job.status.value, "data": json.dumps(payload)}
                    return
                await asyncio.sleep(0.25)

        return EventSourceResponse(stream())

    return app
