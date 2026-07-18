"""Golden (snapshot) tests locking the exact LRC wire format — standard + Enhanced A2."""

from __future__ import annotations

from syrupy.assertion import SnapshotAssertion

from lrcforge.domain.alignment import AlignedLine, AlignedWord
from lrcforge.domain.lrc import LrcDocument, LrcMetadata, render_lrc
from lrcforge.domain.lyrics import LyricsSource


def _doc() -> LrcDocument:
    lines = (
        AlignedLine(
            words=(
                AlignedWord(text="never", start=0.0, end=1.2),
                AlignedWord(text="gonna", start=1.2, end=2.4),
                AlignedWord(text="give", start=2.4, end=3.6),
            ),
            start=0.0,
            end=3.6,
        ),
        AlignedLine(
            words=(
                AlignedWord(text="you", start=61.05, end=61.6),
                AlignedWord(text="up", start=61.6, end=62.0),
            ),
            start=61.05,
            end=62.0,
        ),
    )
    meta = LrcMetadata(
        language="en", tool="lrcforge", source=LyricsSource.ASR, needs_review=True
    )
    return LrcDocument(metadata=meta, lines=lines)


def test_enhanced_lrc_golden(snapshot: SnapshotAssertion) -> None:
    assert render_lrc(_doc(), enhanced=True) == snapshot


def test_line_lrc_golden(snapshot: SnapshotAssertion) -> None:
    assert render_lrc(_doc(), enhanced=False) == snapshot
