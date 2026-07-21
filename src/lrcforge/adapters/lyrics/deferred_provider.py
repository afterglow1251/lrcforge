"""No-op lyrics step for the Whisper-aligner path: the aligner transcribes AND times in a
single pass, so this only carries language/source/needs_review (no separate transcription)."""

from __future__ import annotations

from lrcforge.domain.audio import VocalStem
from lrcforge.domain.lyrics import LyricsDraft, LyricsSource


class DeferredLyricsProvider:
    def fetch(self, stem: VocalStem, lang: str) -> LyricsDraft:
        return LyricsDraft(
            lines=(), lang=lang, source=LyricsSource.ASR, confidence=None, needs_review=True
        )
