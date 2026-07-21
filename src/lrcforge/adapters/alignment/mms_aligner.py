"""Forced alignment via ctc-forced-aligner (MMS multilingual wav2vec2 CTC).

Aligns the (known) draft text to the vocal stem -> per-word timestamps. Default aligner
for UA/RU/EN. NOTE: the model call path is not exercised in CI (torch not installed);
lazy imports keep it out of the fakes path. Validate the exact ctc-forced-aligner API on
a first real run. The re-grouping of aligned words into lines is pure and unit-tested."""

from __future__ import annotations

from typing import Any

from lrcforge.adapters.alignment._regroup import iso3, regroup_words
from lrcforge.domain.alignment import AlignedLyrics, AlignedWord
from lrcforge.domain.audio import VocalStem
from lrcforge.domain.errors import AlignmentError
from lrcforge.domain.lyrics import LyricsDraft


class MmsForcedAligner:
    def __init__(self, device: str = "auto", batch_size: int = 16) -> None:
        self._device = "cpu" if device == "auto" else device
        self._batch_size = batch_size
        self._model: Any = None
        self._tokenizer: Any = None

    def _ensure_model(self) -> tuple[Any, Any]:
        if self._model is None:
            from ctc_forced_aligner import load_alignment_model  # lazy

            self._model, self._tokenizer = load_alignment_model(self._device)
        return self._model, self._tokenizer

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
            word_ts = postprocess_results(text_starred, spans, stride, scores)
        except (RuntimeError, OSError, ValueError, KeyError) as exc:
            raise AlignmentError(f"alignment failed for {stem.audio.path}: {exc}") from exc

        flat = [
            AlignedWord(
                text=str(w["text"]),
                start=float(w["start"]),
                end=float(w["end"]),
                score=(float(w["score"]) if w.get("score") is not None else None),
            )
            for w in word_ts
        ]
        return AlignedLyrics(
            lines=regroup_words(draft.lines, flat),
            lang=draft.lang,
            source=draft.source,
            needs_review=draft.needs_review,
            word_level=True,
        )
