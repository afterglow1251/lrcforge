"""dishka providers. M0 uses a single Scope.APP; the REQUEST scope (per web job) and
real ML adapters arrive with M2+/M5 (see PLAN.md §5, §8)."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from lrcforge.adapters.fakes.stages import (
    FakeAligner,
    FakeAudioLoader,
    FakeLanguageDetector,
    FakeSeparator,
    FakeTranscriptionProvider,
    LogProgressReporter,
)
from lrcforge.adapters.lrc.enhanced_lrc_writer import EnhancedLrcWriter
from lrcforge.config import Settings
from lrcforge.pipeline.orchestrator import AlignPipeline
from lrcforge.ports.aligner import ForcedAligner
from lrcforge.ports.audio_loader import AudioLoader
from lrcforge.ports.language_detector import LanguageDetector
from lrcforge.ports.lrc_writer import LrcWriter
from lrcforge.ports.lyrics_provider import LyricsProvider
from lrcforge.ports.progress import ProgressReporter
from lrcforge.ports.separator import SourceSeparator


class ConfigProvider(Provider):
    scope = Scope.APP

    @provide
    def settings(self) -> Settings:
        return Settings()


class CoreProvider(Provider):
    """Pure, non-ML components — real in every configuration."""

    scope = Scope.APP

    @provide
    def writer(self) -> LrcWriter:
        return EnhancedLrcWriter()

    @provide
    def progress(self) -> ProgressReporter:
        return LogProgressReporter()


class FakeStagesProvider(Provider):
    """Binds the ML ports to fakes (M0 + tests) — zero models loaded."""

    scope = Scope.APP

    @provide
    def loader(self) -> AudioLoader:
        return FakeAudioLoader()

    @provide
    def separator(self) -> SourceSeparator:
        return FakeSeparator()

    @provide
    def detector(self) -> LanguageDetector:
        return FakeLanguageDetector()

    @provide
    def lyrics(self) -> LyricsProvider:
        return FakeTranscriptionProvider()

    @provide
    def aligner(self) -> ForcedAligner:
        return FakeAligner()


class PipelineProvider(Provider):
    scope = Scope.APP

    @provide
    def pipeline(
        self,
        loader: AudioLoader,
        separator: SourceSeparator,
        detector: LanguageDetector,
        lyrics: LyricsProvider,
        aligner: ForcedAligner,
        writer: LrcWriter,
        progress: ProgressReporter,
    ) -> AlignPipeline:
        return AlignPipeline(loader, separator, detector, lyrics, aligner, writer, progress)
