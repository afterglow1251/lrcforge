"""The single orchestration path. Emits a ProgressEvent per stage. Graceful
degradation is trivial now (no DB): transcribe unless the caller supplied text."""

from __future__ import annotations

from pathlib import Path

from lrcforge.domain.audio import VocalStem
from lrcforge.domain.lrc import LrcDocument
from lrcforge.domain.progress import ProgressEvent, Stage
from lrcforge.pipeline.options import RunOptions
from lrcforge.ports.aligner import ForcedAligner
from lrcforge.ports.audio_loader import AudioLoader
from lrcforge.ports.language_detector import LanguageDetector
from lrcforge.ports.lrc_writer import LrcWriter
from lrcforge.ports.lyrics_provider import LyricsProvider
from lrcforge.ports.progress import ProgressReporter
from lrcforge.ports.separator import SourceSeparator


class AlignPipeline:
    def __init__(
        self,
        loader: AudioLoader,
        separator: SourceSeparator,
        detector: LanguageDetector,
        lyrics: LyricsProvider,
        aligner: ForcedAligner,
        writer: LrcWriter,
        progress: ProgressReporter,
    ) -> None:
        self._loader = loader
        self._separator = separator
        self._detector = detector
        self._lyrics = lyrics
        self._aligner = aligner
        self._writer = writer
        self._progress = progress

    def _emit(self, stage: Stage, pct: float, message: str) -> None:
        self._progress.emit(ProgressEvent(stage=stage, pct=pct, message=message))

    def run(
        self, path: Path, opts: RunOptions, lyrics: LyricsProvider | None = None
    ) -> LrcDocument:
        """`lyrics` overrides the injected provider for this run (e.g. a user-supplied
        text file → authoritative align-only path). It stays a port, so callers in the
        upper layers pick the concrete adapter without the pipeline importing it."""
        provider = lyrics if lyrics is not None else self._lyrics

        self._emit(Stage.LOAD, 0.0, f"probing {path.name}")
        audio = self._loader.probe(path)

        if opts.separate:
            self._emit(Stage.SEPARATE, 0.1, "separating vocals")
            stem = self._separator.separate(audio)
        else:
            stem = VocalStem(audio=audio, separated_by="none")

        if opts.forced_lang is not None:
            lang = opts.forced_lang
            self._emit(Stage.DETECT_LANG, 0.4, f"language forced: {lang}")
        else:
            self._emit(Stage.DETECT_LANG, 0.4, "detecting language")
            lang = self._detector.detect(stem).lang

        self._emit(Stage.TRANSCRIBE, 0.5, "acquiring lyrics")
        draft = provider.fetch(stem, lang)

        self._emit(Stage.ALIGN, 0.75, "forced alignment")
        aligned = self._aligner.align(stem, draft)

        self._emit(Stage.WRITE, 0.95, "building LRC")
        doc = self._writer.to_document(aligned)

        self._emit(Stage.DONE, 1.0, "done")
        return doc
