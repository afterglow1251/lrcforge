"""Forced alignment via ctc-forced-aligner (MMS multilingual wav2vec2 CTC).

Aligns the (known) draft text to the vocal stem -> per-word timestamps. Default aligner
for UA/RU/EN. NOTE: the model call path is not exercised in CI (torch not installed);
lazy imports keep it out of the fakes path. Validate the exact ctc-forced-aligner API on
a first real run. The re-grouping of aligned words into lines is pure and unit-tested."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypedDict

from lrcforge.adapters.alignment._regroup import iso3, regroup_words
from lrcforge.domain.alignment import AlignedLyrics, AlignedWord
from lrcforge.domain.audio import VocalStem
from lrcforge.domain.errors import AlignmentError
from lrcforge.domain.lyrics import LyricsDraft


class _AlignModel(Protocol):
    """The ctc-forced-aligner model surface we use (avoids a leaked Any)."""

    dtype: object
    device: object


class _WordTs(TypedDict):
    """Shape of one entry returned by ctc-forced-aligner's postprocess_results."""

    text: str
    start: float
    end: float
    score: float | None


class MmsForcedAligner:
    def __init__(self, device: str = "auto", batch_size: int = 16) -> None:
        self._device = "cpu" if device == "auto" else device
        self._batch_size = batch_size
        self._model: _AlignModel | None = None
        self._tokenizer: object = None

    def _ensure_model(self) -> tuple[_AlignModel, object]:
        if self._model is None:
            from ctc_forced_aligner import load_alignment_model  # lazy

            self._model, self._tokenizer = load_alignment_model(self._device)
        model = self._model
        assert model is not None
        return model, self._tokenizer

    def align(self, stem: VocalStem, draft: LyricsDraft) -> AlignedLyrics:
        try:
            from ctc_forced_aligner import (  # lazy
                generate_emissions,
                get_alignments,
                get_spans,
                load_audio,
                postprocess_results,
                preprocess_text,
            )

            model, tokenizer = self._ensure_model()
            text = "\n".join(line.raw for line in draft.lines)
            waveform = load_audio(str(stem.audio.path), model.dtype, model.device)
            emissions, stride = generate_emissions(model, waveform, batch_size=self._batch_size)
            tokens_starred, text_starred = preprocess_text(
                text, romanize=True, language=iso3(draft.lang)
            )
            segments, scores, blank_id = get_alignments(emissions, tokens_starred, tokenizer)
            spans = get_spans(tokens_starred, segments, blank_id)
            word_ts: Sequence[_WordTs] = postprocess_results(text_starred, spans, stride, scores)
        except (RuntimeError, OSError, ValueError, KeyError, ImportError) as exc:
            raise AlignmentError(f"alignment failed for {stem.audio.path}: {exc}") from exc

        flat = [
            AlignedWord(text=w["text"], start=w["start"], end=w["end"], score=w.get("score"))
            for w in word_ts
        ]
        return AlignedLyrics(
            lines=regroup_words(draft.lines, flat),
            lang=draft.lang,
            source=draft.source,
            needs_review=draft.needs_review,
            word_level=True,
        )
