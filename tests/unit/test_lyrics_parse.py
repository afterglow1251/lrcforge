from __future__ import annotations

from pathlib import Path

from lrcforge.adapters.lyrics._parse import lines_to_draft, segments_to_draft
from lrcforge.adapters.lyrics.userfile_provider import UserFileLyricsProvider
from lrcforge.domain.audio import AudioRef, VocalStem
from lrcforge.domain.lyrics import LyricsSource


def _stem() -> VocalStem:
    return VocalStem(
        audio=AudioRef(path=Path("x.wav"), sample_rate=16000, channels=1, duration_s=1.0),
        separated_by="none",
    )


def test_segments_to_draft_is_asr_review_draft() -> None:
    draft = segments_to_draft([{"text": " never gonna "}, {"text": "give you up"}], lang="en")
    assert draft.source is LyricsSource.ASR
    assert draft.needs_review is True
    assert draft.lines[0].raw == "never gonna"
    assert [w.text for w in draft.lines[0].words] == ["never", "gonna"]


def test_lines_to_draft_skips_blank_lines() -> None:
    draft = lines_to_draft(
        ["hello world", "   ", "", "second line"],
        lang="en",
        source=LyricsSource.USER,
        needs_review=False,
    )
    assert len(draft.lines) == 2
    assert draft.lines[1].raw == "second line"


def test_userfile_provider_is_authoritative(tmp_path: Path) -> None:
    f = tmp_path / "words.txt"
    f.write_text("line one\nline two\n", encoding="utf-8")
    draft = UserFileLyricsProvider(f).fetch(_stem(), "en")
    assert draft.source is LyricsSource.USER
    assert draft.needs_review is False
    assert len(draft.lines) == 2
