"""Alternative transcription backend: mlx-whisper (Apple GPU via MLX). Selected on
Apple Silicon for speed. Text only; timings from the aligner. Lazy imports."""

from __future__ import annotations

from lrcforge.adapters.lyrics._parse import segments_to_draft
from lrcforge.domain.audio import VocalStem
from lrcforge.domain.errors import TranscriptionError
from lrcforge.domain.lyrics import LyricsDraft


class MlxWhisperLyricsProvider:
    def __init__(self, model_repo: str = "mlx-community/whisper-large-v3-turbo") -> None:
        self._model_repo = model_repo

    def fetch(self, stem: VocalStem, lang: str) -> LyricsDraft:
        try:
            import mlx_whisper  # lazy

            result = mlx_whisper.transcribe(
                str(stem.audio.path), path_or_hf_repo=self._model_repo, language=lang
            )
            segments = result["segments"]
        except (RuntimeError, OSError, ValueError, KeyError, ImportError) as exc:
            raise TranscriptionError(f"transcription failed for {stem.audio.path}: {exc}") from exc
        return segments_to_draft(segments, lang=lang)
