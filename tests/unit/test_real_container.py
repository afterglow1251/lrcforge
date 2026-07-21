"""The real (fakes=False) container must wire up without importing torch or loading any
model — construction is lazy, models load only on first stage call."""

from __future__ import annotations

import sys

from lrcforge.di.container import build_container
from lrcforge.pipeline.orchestrator import AlignPipeline
from lrcforge.ports.aligner import ForcedAligner
from lrcforge.ports.language_detector import LanguageDetector
from lrcforge.ports.lyrics_provider import LyricsProvider
from lrcforge.ports.separator import SourceSeparator


def test_real_container_resolves_pipeline_without_loading_models() -> None:
    container = build_container(fakes=False)
    try:
        pipeline = container.get(AlignPipeline)
        assert isinstance(pipeline, AlignPipeline)
        # every real stage resolves...
        assert container.get(SourceSeparator) is not None
        assert container.get(LanguageDetector) is not None
        assert container.get(LyricsProvider) is not None
        assert container.get(ForcedAligner) is not None
    finally:
        container.close()

    # ...and none of it dragged in torch / the heavy ML libs
    for heavy in ("torch", "demucs", "faster_whisper", "ctc_forced_aligner"):
        assert heavy not in sys.modules, f"{heavy} was imported at container build time"
