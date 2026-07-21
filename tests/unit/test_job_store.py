from __future__ import annotations

from lrcforge.domain.job import JobId, JobStatus
from lrcforge.domain.lrc import LrcMetadata
from lrcforge.domain.lyrics import LyricsSource
from lrcforge.domain.progress import ProgressEvent, Stage
from lrcforge.jobs.store import JobStore


def test_store_lifecycle_to_done() -> None:
    store = JobStore()
    jid = JobId("j1")
    store.create(jid)

    pending = store.get(jid)
    assert pending is not None and pending.status is JobStatus.PENDING

    store.append_event(jid, ProgressEvent(stage=Stage.LOAD, pct=0.0, message="probing"))
    running = store.get(jid)
    assert running is not None
    assert running.status is JobStatus.RUNNING
    assert len(running.events) == 1

    meta = LrcMetadata(language="uk", tool="lrcforge", source=LyricsSource.ASR, needs_review=True)
    store.complete(jid, "[la:uk]\n", meta)
    done = store.get(jid)
    assert done is not None
    assert done.status is JobStatus.DONE
    assert done.lrc == "[la:uk]\n"
    assert done.metadata == meta


def test_store_fail() -> None:
    store = JobStore()
    jid = JobId("j2")
    store.create(jid)
    store.fail(jid, "boom")
    failed = store.get(jid)
    assert failed is not None
    assert failed.status is JobStatus.ERROR
    assert failed.error == "boom"


def test_get_unknown_returns_none() -> None:
    assert JobStore().get(JobId("nope")) is None
