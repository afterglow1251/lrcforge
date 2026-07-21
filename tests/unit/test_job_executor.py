from __future__ import annotations

from pathlib import Path

from lrcforge.di.web import build_web_container
from lrcforge.domain.job import JobId, JobStatus
from lrcforge.jobs.executor import JobExecutor
from lrcforge.jobs.store import JobStore
from lrcforge.pipeline.options import RunOptions


def test_executor_runs_job_to_done_on_fakes(tmp_path: Path) -> None:
    container = build_web_container(fakes=True)
    try:
        store = container.get(JobStore)
        executor = JobExecutor(container, store)
        jid = JobId("job-1")
        store.create(jid)
        audio = tmp_path / "a.wav"
        audio.write_bytes(b"ignored-by-fakes")

        executor.execute(jid, audio, RunOptions())

        job = store.get(jid)
        assert job is not None
        assert job.status is JobStatus.DONE
        assert job.lrc is not None and job.lrc.startswith("[la:uk]")
        assert job.metadata is not None and job.metadata.needs_review is True
        assert len(job.events) >= 5  # a progress event per stage
    finally:
        container.close()
