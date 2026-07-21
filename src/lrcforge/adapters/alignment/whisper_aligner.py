"""Word-level timing straight from faster-whisper (`word_timestamps=True`).

This is the robust default aligner: it re-derives the sung words AND their timings in one
pass, with no separate forced-alignment dependency. Because it transcribes itself, the
injected lyrics step for this path is a no-op placeholder (DeferredLyricsProvider) so we
transcribe exactly once. Lazy imports; not exercised in CI."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from lrcforge.domain.alignment import AlignedLine, AlignedLyrics, AlignedWord
from lrcforge.domain.audio import VocalStem
from lrcforge.domain.errors import AlignmentError
from lrcforge.domain.lyrics import LyricsDraft
from lrcforge.ports.aligner import AlignProgress


class _FwWord(Protocol):
    word: str
    start: float
    end: float
    probability: float


class _FwSegment(Protocol):
    end: float
    words: list[_FwWord] | None


class _FwModel(Protocol):
    def transcribe(
        self,
        path: str,
        *,
        language: str | None,
        word_timestamps: bool,
        vad_filter: bool,
        condition_on_previous_text: bool,
    ) -> tuple[Iterable[_FwSegment], object]: ...


class WhisperForcedAligner:
    def __init__(
        self, model_name: str = "large-v3", device: str = "auto", compute_type: str = "default"
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._compute_type = compute_type
        self._model: _FwModel | None = None

    def _ensure_model(self) -> _FwModel:
        if self._model is None:
            from faster_whisper import WhisperModel  # lazy

            self._model = WhisperModel(
                self._model_name, device=self._device, compute_type=self._compute_type
            )
        model = self._model
        assert model is not None
        return model

    def align(
        self, stem: VocalStem, draft: LyricsDraft, on_progress: AlignProgress | None = None
    ) -> AlignedLyrics:
        try:
            if on_progress is not None:
                on_progress(0.0, "loading model (first run downloads)")
            model = self._ensure_model()
            segments, _info = model.transcribe(
                str(stem.audio.path),
                language=(draft.lang or None),
                word_timestamps=True,
                vad_filter=True,  # skip instrumental gaps -> far fewer hallucinated repeats
                condition_on_previous_text=False,  # stop a bad segment poisoning the next
            )
            duration = stem.audio.duration_s
            lines: list[AlignedLine] = []
            for segment in segments:
                words: list[AlignedWord] = []
                for w in segment.words or []:
                    text = w.word.strip()
                    if not text:
                        continue
                    start = float(w.start)
                    words.append(
                        AlignedWord(
                            text=text,
                            start=start,
                            end=max(float(w.end), start),
                            score=float(w.probability),
                        )
                    )
                if words:
                    lines.append(
                        AlignedLine(words=tuple(words), start=words[0].start, end=words[-1].end)
                    )
                if on_progress is not None and duration > 0:
                    pct = min(float(segment.end) / duration, 1.0)
                    on_progress(pct, f"transcribing {int(pct * 100)}%")
        except (RuntimeError, OSError, ValueError, ImportError) as exc:
            raise AlignmentError(f"alignment failed for {stem.audio.path}: {exc}") from exc

        return AlignedLyrics(
            lines=tuple(lines),
            lang=draft.lang,
            source=draft.source,
            needs_review=draft.needs_review,
            word_level=True,
        )
