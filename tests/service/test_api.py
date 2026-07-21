"""API tests with the fake pipeline + an inline (synchronous) runner, so POST /jobs
completes the job before returning — deterministic, no threads, no models."""

from __future__ import annotations

from fastapi.testclient import TestClient

from lrcforge.di.web import build_web_container
from lrcforge.jobs.executor import JobExecutor
from lrcforge.jobs.runner import InlineJobRunner
from lrcforge.jobs.store import JobStore
from lrcforge.service.api import create_app


def _client() -> TestClient:
    container = build_web_container(fakes=True)
    store = container.get(JobStore)
    executor = JobExecutor(container, store)
    runner = InlineJobRunner(executor)
    return TestClient(create_app(runner=runner, store=store))


def test_index_is_served() -> None:
    resp = _client().get("/")
    assert resp.status_code == 200
    assert "lrcforge" in resp.text


def test_job_lifecycle_produces_lrc() -> None:
    client = _client()
    resp = client.post(
        "/jobs",
        files={"audio": ("song.wav", b"ignored-by-fakes", "audio/wav")},
        data={"line": "true"},
    )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    job = client.get(f"/jobs/{job_id}").json()
    assert job["status"] == "done"
    assert job["lrc"].startswith("[la:uk]")
    assert job["needs_review"] is True
    assert job["language"] == "uk"


def test_unknown_job_is_404() -> None:
    assert _client().get("/jobs/does-not-exist").status_code == 404
