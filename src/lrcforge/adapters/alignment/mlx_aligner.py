"""Word-level timing from mlx-whisper (Apple GPU via MLX) — same approach as the
faster-whisper aligner but runs on the GPU, so it is much faster on Apple Silicon.
Selected when transcriber=mlx. Lazy import; not exercised in CI."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypedDict

from lrcforge.domain.alignment import AlignedLine, AlignedLyrics, AlignedWord
from lrcforge.domain.audio import VocalStem
from lrcforge.domain.errors import AlignmentError
from lrcforge.domain.lyrics import LyricsDraft


class _MlxWord(TypedDict):
    word: str
    start: float
    end: float
    probability: float


class MlxWhisperAligner:
    def __init__(self, model_repo: str = "mlx-community/whisper-large-v3") -> None:
        self._model_repo = model_repo

    def align(self, stem: VocalStem, draft: LyricsDraft) -> AlignedLyrics:
        try:
            import mlx_whisper  # lazy

            result = mlx_whisper.transcribe(
                str(stem.audio.path),
                path_or_hf_repo=self._model_repo,
                language=(draft.lang or None),
                word_timestamps=True,
            )
            lines: list[AlignedLine] = []
            for segment in result["segments"]:
                words: list[AlignedWord] = []
                seg_words: Sequence[_MlxWord] = segment.get("words") or []
                for w in seg_words:
                    text = w["word"].strip()
                    if not text:
                        continue
                    start = float(w["start"])
                    words.append(
                        AlignedWord(
                            text=text,
                            start=start,
                            end=max(float(w["end"]), start),
                            score=float(w["probability"]),
                        )
                    )
                if words:
                    lines.append(
                        AlignedLine(words=tuple(words), start=words[0].start, end=words[-1].end)
                    )
        except (RuntimeError, OSError, ValueError, KeyError, ImportError) as exc:
            raise AlignmentError(f"alignment failed for {stem.audio.path}: {exc}") from exc

        return AlignedLyrics(
            lines=tuple(lines),
            lang=draft.lang,
            source=draft.source,
            needs_review=draft.needs_review,
            word_level=True,
        )
