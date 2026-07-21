"""Authoritative lyrics from a user-supplied text file (--lyrics-file). No model — the
words are known, so the draft is not a review draft (needs_review=False)."""

from __future__ import annotations

from pathlib import Path

from lrcforge.adapters.lyrics._parse import lines_to_draft
from lrcforge.domain.audio import VocalStem
from lrcforge.domain.errors import TranscriptionError
from lrcforge.domain.lyrics import LyricsDraft, LyricsSource


class UserFileLyricsProvider:
    def __init__(self, path: Path) -> None:
        self._path = path

    def fetch(self, stem: VocalStem, lang: str) -> LyricsDraft:
        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            raise TranscriptionError(f"cannot read lyrics file {self._path}: {exc}") from exc
        return lines_to_draft(
            text.splitlines(),
            lang=lang,
            source=LyricsSource.USER,
            needs_review=False,
        )
