from __future__ import annotations

from dataclasses import dataclass

from lrcforge.domain.job import JobId


@dataclass(frozen=True, slots=True)
class JobContext:
    """Per-job value injected into the dishka REQUEST scope (see di/web.py)."""

    job_id: JobId
