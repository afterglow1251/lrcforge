from __future__ import annotations

from pathlib import Path

import pytest

from lrcforge.cli.app import align, batch, lang


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


def test_align_with_lyrics_file_is_authoritative(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    words = tmp_path / "w.txt"
    words.write_text("hello world\nsecond line\n", encoding="utf-8")
    align(Path("song.wav"), lyrics_file=words, line=True, fake=True)
    out = capsys.readouterr().out
    assert "hello world" in out
    assert "second line" in out
    assert "needs review" not in out  # user-supplied text is authoritative


def test_batch_writes_sidecar_lrc(tmp_path: Path) -> None:
    (tmp_path / "a.mp3").write_bytes(b"x")
    (tmp_path / "b.mp3").write_bytes(b"y")
    batch(tmp_path, fake=True)
    assert (tmp_path / "a.lrc").read_text(encoding="utf-8").startswith("[la:uk]")
    assert (tmp_path / "b.lrc").exists()
