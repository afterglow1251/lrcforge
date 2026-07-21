from __future__ import annotations

from pathlib import Path

import pytest

from lrcforge.cli.app import align, lang


def test_align_prints_lrc(capsys: pytest.CaptureFixture[str]) -> None:
    align(Path("song.wav"), fake=True)
    out = capsys.readouterr().out
    assert "[la:uk]" in out
    assert "needs review" in out


def test_align_writes_file(tmp_path: Path) -> None:
    out_file = tmp_path / "song.lrc"
    align(Path("song.wav"), out=out_file, fake=True)
    assert out_file.read_text(encoding="utf-8").startswith("[la:uk]")


def test_lang_prints_detected_language(capsys: pytest.CaptureFixture[str]) -> None:
    lang(Path("song.wav"), fake=True)
    assert "uk" in capsys.readouterr().out
