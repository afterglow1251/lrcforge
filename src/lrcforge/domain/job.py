"""Web job types."""

from __future__ import annotations

from enum import StrEnum
from typing import NewType

from pydantic import BaseModel, ConfigDict

from lrcforge.domain.lrc import LrcMetadata
from lrcforge.domain.progress import ProgressEvent

JobId = NewType("JobId", str)


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class Job(BaseModel):
    """Immutable snapshot of a job; the store replaces it on each update."""

    model_config = ConfigDict(frozen=True)

    id: JobId
    status: JobStatus
    events: tuple[ProgressEvent, ...] = ()
    lrc: str | None = None
    metadata: LrcMetadata | None = None
    error: str | None = None
