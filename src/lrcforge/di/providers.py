"""dishka providers. Construction of the ML adapters is lazy (no models load here), so
building any container never imports torch — models load on first stage call."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from lrcforge.adapters.alignment.mlx_aligner import MlxWhisperAligner
from lrcforge.adapters.alignment.mms_aligner import MmsForcedAligner
from lrcforge.adapters.alignment.whisper_aligner import WhisperForcedAligner
from lrcforge.adapters.audio.soundfile_loader import SoundfileAudioLoader
from lrcforge.adapters.fakes.stages import (
    FakeAligner,
    FakeAudioLoader,
    FakeLanguageDetector,
    FakeSeparator,
    FakeTranscriptionProvider,
    LogProgressReporter,
)
from lrcforge.adapters.language.whisper_lid import WhisperLanguageDetector
from lrcforge.adapters.lrc.enhanced_lrc_writer import EnhancedLrcWriter
from lrcforge.adapters.lyrics.deferred_provider import DeferredLyricsProvider
from lrcforge.adapters.lyrics.faster_whisper_provider import FasterWhisperLyricsProvider
from lrcforge.adapters.lyrics.mlx_provider import MlxWhisperLyricsProvider
from lrcforge.adapters.separation.demucs_separator import DemucsSeparator
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


class WriterProvider(Provider):
    """The pure, non-ML LRC writer — real in every configuration."""

    scope = Scope.APP

    @provide
    def writer(self) -> LrcWriter:
        return EnhancedLrcWriter()


class FakeStagesProvider(Provider):
    """Binds the ML ports to fakes (M0 + tests + `--fake`) — zero models loaded."""

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


class RealStagesProvider(Provider):
    """Binds the ML ports to real adapters (Demucs, LID, Whisper, MMS)."""

    scope = Scope.APP

    @provide
    def loader(self) -> AudioLoader:
        return SoundfileAudioLoader()

    @provide
    def separator(self, settings: Settings) -> SourceSeparator:
        return DemucsSeparator(device=settings.device)

    @provide
    def detector(self, settings: Settings) -> LanguageDetector:
        return WhisperLanguageDetector(model_name=settings.lid_model, device=settings.device)

    @provide
    def lyrics(self, settings: Settings) -> LyricsProvider:
        # The whisper aligner transcribes + times in one pass, so no separate transcription.
        if settings.aligner == "whisper":
            return DeferredLyricsProvider()
        if settings.transcriber == "mlx":
            return MlxWhisperLyricsProvider(model_repo=settings.mlx_model)
        return FasterWhisperLyricsProvider(model_name=settings.faster_model, device=settings.device)

    @provide
    def aligner(self, settings: Settings) -> ForcedAligner:
        if settings.aligner == "whisper":
            if settings.transcriber == "mlx":  # Apple GPU — much faster on Apple Silicon
                return MlxWhisperAligner(model_repo=settings.mlx_model)
            return WhisperForcedAligner(model_name=settings.faster_model, device=settings.device)
        if settings.aligner == "mms":
            return MmsForcedAligner(device=settings.device)
        raise NotImplementedError(f"aligner {settings.aligner!r} not implemented")


class CliRuntimeProvider(Provider):
    """CLI runtime: a plain APP-scoped progress reporter + pipeline (no per-job scope)."""

    scope = Scope.APP

    @provide
    def progress(self) -> ProgressReporter:
        return LogProgressReporter()

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
