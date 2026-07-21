"""Assemble the web app: build the web container, wire the job store + threaded runner,
and hand them to the FastAPI factory."""

from __future__ import annotations

from fastapi import FastAPI

from lrcforge.di.web import build_web_container
from lrcforge.jobs.executor import JobExecutor
from lrcforge.jobs.runner import JobRunner, ThreadedJobRunner
from lrcforge.jobs.store import JobStore
from lrcforge.service.api import create_app


def build_web_app(*, fakes: bool = False) -> FastAPI:
    container = build_web_container(fakes=fakes)
    store = container.get(JobStore)
    executor = JobExecutor(container, store)
    runner: JobRunner = ThreadedJobRunner(executor)
    return create_app(runner=runner, store=store)
