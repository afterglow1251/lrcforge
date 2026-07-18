"""In-memory fakes: deterministic, no I/O, no models.

They satisfy the same Protocols as the real adapters, so the orchestrator can't tell
them apart. `FakeAligner` spreads the draft's words evenly across the stem duration so
downstream LRC rendering has plausible, monotonic timestamps to work with."""

from __future__ import annotations

from pathlib import Path

from lrcforge.domain.alignment import AlignedLine, AlignedLyrics, AlignedWord
from lrcforge.domain.audio import AudioRef, VocalStem
from lrcforge.domain.language import LanguageResult
from lrcforge.domain.lyrics import LyricLine, LyricsDraft, LyricsSource, LyricWord
from lrcforge.domain.progress import ProgressEvent

_FAKE_LINES: tuple[str, ...] = (
    "never gonna give you up",
    "never gonna let you down",
)


class FakeAudioLoader:
    def __init__(self, duration_s: float = 12.0) -> None:
        self._duration_s = duration_s

    def probe(self, path: Path) -> AudioRef:
        return AudioRef(path=path, sample_rate=44100, channels=2, duration_s=self._duration_s)


class FakeSeparator:
    def separate(self, audio: AudioRef) -> VocalStem:
        return VocalStem(audio=audio, separated_by="fake")


class FakeLanguageDetector:
    def __init__(self, lang: str = "uk") -> None:
        self._lang = lang

    def detect(self, stem: VocalStem) -> LanguageResult:
        return LanguageResult(lang=self._lang, confidence=1.0)


class FakeTranscriptionProvider:
    """Stands in for Whisper: returns canned lines flagged as a draft needing review."""

    def fetch(self, stem: VocalStem, lang: str) -> LyricsDraft:
        lines = tuple(
            LyricLine(words=tuple(LyricWord(text=w) for w in raw.split()), raw=raw)
            for raw in _FAKE_LINES
        )
        return LyricsDraft(
            lines=lines,
            lang=lang,
            source=LyricsSource.ASR,
            confidence=0.5,
            needs_review=True,
        )


class FakeAligner:
    """Spread words evenly across the stem's duration -> monotonic timestamps."""

    def align(self, stem: VocalStem, draft: LyricsDraft) -> AlignedLyrics:
        total_words = sum(len(line.words) for line in draft.lines)
        duration = stem.audio.duration_s
        dt = duration / total_words if total_words else 0.0

        idx = 0
        aligned_lines: list[AlignedLine] = []
        for line in draft.lines:
            words: list[AlignedWord] = []
            for word in line.words:
                start = idx * dt
                end = (idx + 1) * dt
                words.append(AlignedWord(text=word.text, start=start, end=end, score=1.0))
                idx += 1
            if words:
                aligned_lines.append(
                    AlignedLine(words=tuple(words), start=words[0].start, end=words[-1].end)
                )
        return AlignedLyrics(
            lines=tuple(aligned_lines),
            lang=draft.lang,
            source=draft.source,
            needs_review=draft.needs_review,
            word_level=True,
        )


class LogProgressReporter:
    """Collects events (and could log them). Kept trivial for M0."""

    def __init__(self) -> None:
        self.events: list[ProgressEvent] = []

    def emit(self, event: ProgressEvent) -> None:
        self.events.append(event)


class NullProgressReporter:
    def emit(self, event: ProgressEvent) -> None:
        return None
