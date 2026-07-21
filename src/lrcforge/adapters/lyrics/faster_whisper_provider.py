"""Default transcription backend: faster-whisper (CTranslate2). Portable (CPU int8 on
Apple Silicon). Produces text only; the forced aligner assigns timings. Lazy imports;
model path not exercised in CI."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from lrcforge.adapters.lyrics._parse import segments_to_draft
from lrcforge.domain.audio import VocalStem
from lrcforge.domain.errors import TranscriptionError
from lrcforge.domain.lyrics import LyricsDraft


class _FwSegment(Protocol):
    text: str


class _FwModel(Protocol):
    """The faster-whisper surface we use (avoids a leaked Any)."""

    def transcribe(self, path: str, *, language: str) -> tuple[Iterable[_FwSegment], object]: ...


class FasterWhisperLyricsProvider:
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

    def fetch(self, stem: VocalStem, lang: str) -> LyricsDraft:
        try:
            model = self._ensure_model()
            segments, _info = model.transcribe(str(stem.audio.path), language=lang)
            seg_dicts = [{"text": segment.text} for segment in segments]
        except (RuntimeError, OSError, ValueError) as exc:
            raise TranscriptionError(f"transcription failed for {stem.audio.path}: {exc}") from exc
        return segments_to_draft(seg_dicts, lang=lang)
