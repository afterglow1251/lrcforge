"""Progress events emitted by the pipeline (CLI prints them; the web will stream them)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Stage(StrEnum):
    LOAD = "load"
    SEPARATE = "separate"
    DETECT_LANG = "detect_lang"
    TRANSCRIBE = "transcribe"
    ALIGN = "align"
    WRITE = "write"
    DONE = "done"


class ProgressEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    stage: Stage
    pct: float
    message: str
