from __future__ import annotations

from lrcforge.adapters.alignment._regroup import iso3, regroup_words
from lrcforge.domain.alignment import AlignedWord
from lrcforge.domain.lyrics import LyricLine, LyricWord


def _line(*words: str) -> LyricLine:
    return LyricLine(words=tuple(LyricWord(text=w) for w in words), raw=" ".join(words))


def test_iso3_maps_known_and_falls_back() -> None:
    assert iso3("uk") == "ukr"
    assert iso3("RU") == "rus"
    assert iso3("en") == "eng"
    assert iso3("xx") == "xx"  # unknown -> passthrough


def test_regroup_words_chunks_by_line_word_counts() -> None:
    draft = (_line("never", "gonna"), _line("give", "you", "up"))
    flat = [
        AlignedWord(text="never", start=0.0, end=0.5),
        AlignedWord(text="gonna", start=0.5, end=1.0),
        AlignedWord(text="give", start=1.0, end=1.5),
        AlignedWord(text="you", start=1.5, end=2.0),
        AlignedWord(text="up", start=2.0, end=2.5),
    ]
    lines = regroup_words(draft, flat)
    assert len(lines) == 2
    assert [w.text for w in lines[0].words] == ["never", "gonna"]
    assert lines[0].start == 0.0 and lines[0].end == 1.0
    assert lines[1].start == 1.0 and lines[1].end == 2.5


def test_regroup_drops_empty_trailing_line() -> None:
    draft = (_line("only", "line"), _line())  # second line has no words
    flat = [
        AlignedWord(text="only", start=0.0, end=0.5),
        AlignedWord(text="line", start=0.5, end=1.0),
    ]
    lines = regroup_words(draft, flat)
    assert len(lines) == 1
