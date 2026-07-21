"""cyclopts CLI — a thin shell over the injected AlignPipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter

from lrcforge.di.container import build_container
from lrcforge.domain.audio import VocalStem
from lrcforge.domain.lrc import render_lrc
from lrcforge.pipeline.options import RunOptions
from lrcforge.pipeline.orchestrator import AlignPipeline
from lrcforge.ports.audio_loader import AudioLoader
from lrcforge.ports.language_detector import LanguageDetector

app = App(name="lrcforge", help="Audio -> karaoke LRC generator.")


@app.command
def align(
    audio: Path,
    *,
    out: Annotated[Path | None, Parameter(name=["--out", "-o"])] = None,
    lang: str | None = None,
    no_separation: bool = False,
    line: bool = False,
    fake: bool = False,
) -> None:
    """Generate a karaoke LRC for AUDIO.

    Parameters
    ----------
    audio: input audio file.
    out: write the LRC here (default: print to stdout).
    lang: force the language (e.g. uk/ru/en) instead of auto-detecting.
    no_separation: skip vocal separation.
    line: emit line-level LRC instead of word-level (A2).
    fake: use the zero-model fake pipeline (dummy output; for smoke-testing the plumbing).
    """
    container = build_container(fakes=fake)
    try:
        pipeline = container.get(AlignPipeline)
        opts = RunOptions(separate=not no_separation, forced_lang=lang, enhanced=not line)
        doc = pipeline.run(audio, opts)
        text = render_lrc(doc, enhanced=not line)
    finally:
        container.close()

    if out is not None:
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text, end="")


@app.command
def lang(audio: Path, *, fake: bool = False) -> None:
    """Detect and print the language of AUDIO."""
    container = build_container(fakes=fake)
    try:
        loader = container.get(AudioLoader)
        detector = container.get(LanguageDetector)
        stem = VocalStem(audio=loader.probe(audio), separated_by="none")
        result = detector.detect(stem)
    finally:
        container.close()
    print(f"{result.lang} ({result.confidence:.2f})")


@app.command
def serve(host: str = "127.0.0.1", port: int = 8000, fake: bool = False) -> None:
    """Launch the FastAPI service + karaoke-preview web UI (needs the [service] extra)."""
    import uvicorn  # lazy: keep fastapi/uvicorn out of the base CLI import

    from lrcforge.service.app_factory import build_web_app

    uvicorn.run(build_web_app(fakes=fake), host=host, port=port)


def main() -> None:
    app()
