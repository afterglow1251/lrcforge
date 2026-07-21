"""Windowed language identification via faster-whisper's detect_language.

Samples several windows across the track and votes, so an instrumental intro or a
single code-switched line doesn't decide the whole song. Model call path is lazy and
not exercised in CI; the windowing + voting are pure and unit-tested."""

from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from lrcforge.domain.audio import VocalStem
from lrcforge.domain.errors import LanguageDetectionError
from lrcforge.domain.language import LanguageResult, WindowVote

_SR = 16000


class _LidModel(Protocol):
    """The faster-whisper surface we use for LID (avoids a leaked Any)."""

    def detect_language(self, audio: object) -> tuple[object, ...]: ...


def plan_windows(
    total_samples: int, *, sample_rate: int = _SR, n: int = 5, window_s: float = 10.0
) -> tuple[tuple[int, int, float], ...]:
    """Evenly spaced (start_sample, end_sample, start_seconds) windows across the audio."""
    if total_samples <= 0:
        return ()
    win = int(window_s * sample_rate)
    if total_samples <= win:
        return ((0, total_samples, 0.0),)
    spots = max(1, n)
    step = (total_samples - win) / (spots - 1) if spots > 1 else 0.0
    out: list[tuple[int, int, float]] = []
    for i in range(spots):
        start = int(i * step)
        out.append((start, start + win, start / sample_rate))
    return tuple(out)


def aggregate_votes(votes: tuple[WindowVote, ...]) -> LanguageResult:
    """Winner = highest summed confidence; its reported confidence is its mean."""
    if not votes:
        raise LanguageDetectionError("no language votes produced")
    summed: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for v in votes:
        summed[v.lang] += v.confidence
        counts[v.lang] += 1
    winner = max(summed, key=lambda k: summed[k])
    return LanguageResult(
        lang=winner,
        confidence=summed[winner] / counts[winner],
        per_window=votes,
    )


class WhisperLanguageDetector:
    def __init__(
        self, model_name: str = "small", device: str = "auto", windows: int = 5
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._windows = windows
        self._model: _LidModel | None = None

    def _ensure_model(self) -> _LidModel:
        if self._model is None:
            from faster_whisper import WhisperModel  # lazy

            self._model = WhisperModel(self._model_name, device=self._device)
        model = self._model
        assert model is not None
        return model

    def detect(self, stem: VocalStem) -> LanguageResult:
        try:
            from faster_whisper.audio import decode_audio  # lazy

            model = self._ensure_model()
            audio = decode_audio(str(stem.audio.path), sampling_rate=_SR)
            votes: list[WindowVote] = []
            for start, end, start_s in plan_windows(len(audio), n=self._windows):
                detected = model.detect_language(audio[start:end])
                votes.append(
                    WindowVote(
                        start_s=start_s,
                        lang=str(detected[0]),
                        confidence=float(detected[1]),  # type: ignore[arg-type]
                    )
                )
        except (RuntimeError, OSError, ValueError, ImportError) as exc:
            raise LanguageDetectionError(
                f"LID failed for {stem.audio.path}: {exc} "
                "(faster-whisper is required for language ID — install the [ml] extra)"
            ) from exc

        return aggregate_votes(tuple(votes))
