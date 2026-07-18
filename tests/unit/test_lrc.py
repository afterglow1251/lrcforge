from __future__ import annotations

from lrcforge.domain.alignment import AlignedLine, AlignedWord
from lrcforge.domain.lrc import LrcDocument, LrcMetadata, render_lrc
from lrcforge.domain.lyrics import LyricsSource


def _doc(*, needs_review: bool = True) -> LrcDocument:
    line = AlignedLine(
        words=(
            AlignedWord(text="hello", start=1.0, end=1.5),
            AlignedWord(text="world", start=1.5, end=2.0),
        ),
        start=1.0,
        end=2.0,
    )
    meta = LrcMetadata(
        language="en", tool="lrcforge", source=LyricsSource.ASR, needs_review=needs_review
    )
    return LrcDocument(metadata=meta, lines=(line,))


def test_enhanced_render_has_word_tags() -> None:
    out = render_lrc(_doc(), enhanced=True)
    assert "[la:en]" in out
    assert "[00:01.00]<00:01.00>hello <00:01.50>world" in out


def test_line_render_has_no_word_tags() -> None:
    out = render_lrc(_doc(), enhanced=False)
    assert "[00:01.00]hello world" in out
    assert "<00:01.50>" not in out


def test_needs_review_banner_present_only_when_flagged() -> None:
    assert "needs review" in render_lrc(_doc(needs_review=True), enhanced=True)
    assert "needs review" not in render_lrc(_doc(needs_review=False), enhanced=True)
