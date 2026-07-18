from __future__ import annotations

from pathlib import Path

from lrcforge.domain.lrc import LrcDocument
from lrcforge.domain.lyrics import LyricsSource
from lrcforge.pipeline.options import RunOptions
from lrcforge.pipeline.orchestrator import AlignPipeline


def test_pipeline_produces_reviewable_draft(pipeline: AlignPipeline) -> None:
    doc = pipeline.run(Path("fixture.wav"), RunOptions())
    assert isinstance(doc, LrcDocument)
    assert doc.metadata.source is LyricsSource.ASR
    assert doc.metadata.needs_review is True  # transcription -> draft
    assert doc.metadata.language == "uk"
    assert len(doc.lines) == 2


def test_lines_are_monotonic(pipeline: AlignPipeline) -> None:
    doc = pipeline.run(Path("fixture.wav"), RunOptions())
    starts = [line.start for line in doc.lines]
    assert starts == sorted(starts)
    # words within each line are non-decreasing too
    for line in doc.lines:
        word_starts = [w.start for w in line.words]
        assert word_starts == sorted(word_starts)


def test_forced_language_is_honoured(pipeline: AlignPipeline) -> None:
    doc = pipeline.run(Path("fixture.wav"), RunOptions(forced_lang="en"))
    assert doc.metadata.language == "en"


def test_no_separation_still_runs(pipeline: AlignPipeline) -> None:
    doc = pipeline.run(Path("fixture.wav"), RunOptions(separate=False))
    assert len(doc.lines) == 2
