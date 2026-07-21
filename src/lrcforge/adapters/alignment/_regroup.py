"""Pure helpers for the MMS aligner: language code mapping and re-grouping the flat
aligned word list back into the draft's line structure. No models."""

from __future__ import annotations

from collections.abc import Sequence

from lrcforge.domain.alignment import AlignedLine, AlignedWord
from lrcforge.domain.lyrics import LyricLine

# ISO 639-1 -> 639-3 (what MMS / uroman expect). Falls back to the input code.
_ISO3 = {"uk": "ukr", "ru": "rus", "en": "eng", "pl": "pol", "de": "deu", "fr": "fra"}


def iso3(lang: str) -> str:
    return _ISO3.get(lang.lower(), lang.lower())


def regroup_words(
    draft_lines: Sequence[LyricLine], flat: Sequence[AlignedWord]
) -> tuple[AlignedLine, ...]:
    """Chunk the flat aligned words back into lines using each draft line's word count."""
    out: list[AlignedLine] = []
    idx = 0
    for line in draft_lines:
        n = len(line.words)
        chunk = tuple(flat[idx : idx + n])
        idx += n
        if chunk:
            out.append(AlignedLine(words=chunk, start=chunk[0].start, end=chunk[-1].end))
    return tuple(out)
