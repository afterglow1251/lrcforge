"""Real LRC writer — pure, no ML. Builds a dumb LrcDocument; rendering is in domain.lrc."""

from __future__ import annotations

from lrcforge.domain.alignment import AlignedLyrics
from lrcforge.domain.lrc import LrcDocument, LrcMetadata


class EnhancedLrcWriter:
    tool_name = "lrcforge"

    def to_document(self, aligned: AlignedLyrics) -> LrcDocument:
        meta = LrcMetadata(
            language=aligned.lang,
            tool=self.tool_name,
            source=aligned.source,
            needs_review=aligned.needs_review,
        )
        return LrcDocument(metadata=meta, lines=aligned.lines)
