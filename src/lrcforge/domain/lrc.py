"""LRC document + a single pure rendering function.

Rendering lives here as a module-level function (not as a method on the model, and
not duplicated in the writer) so there is exactly one place that knows the LRC format.
The `LrcWriter` port only *builds* the dumb `LrcDocument`; this function renders it."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from lrcforge.domain.alignment import AlignedLine
from lrcforge.domain.lyrics import LyricsSource


class LrcMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    language: str
    tool: str
    source: LyricsSource
    needs_review: bool


class LrcDocument(BaseModel):
    """Dumb data holder — no rendering behaviour (see `render_lrc`)."""

    model_config = ConfigDict(frozen=True)

    metadata: LrcMetadata
    lines: tuple[AlignedLine, ...]


def _fmt_ts(sec: float) -> str:
    sec = max(0.0, sec)
    minutes = int(sec // 60)
    seconds = sec - minutes * 60
    return f"{minutes:02d}:{seconds:05.2f}"


def render_lrc(doc: LrcDocument, *, enhanced: bool) -> str:
    """Render a standard line-level LRC, or Enhanced (A2) word-level when `enhanced`."""
    meta = doc.metadata
    out: list[str] = [f"[la:{meta.language}]", f"[re:{meta.tool}]"]
    if meta.needs_review:
        out.append("[by:auto-transcribed draft - needs review]")
    for line in doc.lines:
        stamp = _fmt_ts(line.start)
        if enhanced and line.words:
            body = " ".join(f"<{_fmt_ts(w.start)}>{w.text}" for w in line.words)
            out.append(f"[{stamp}]{body}")
        else:
            out.append(f"[{stamp}]{' '.join(w.text for w in line.words)}")
    return "\n".join(out) + "\n"
