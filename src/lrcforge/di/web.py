"""Web container: ML stages stay APP singletons, but the ProgressReporter and the
AlignPipeline are REQUEST-scoped and keyed to the per-job JobContext (entered manually
by the JobExecutor). The JobStore is an APP singleton shared across jobs."""

from __future__ import annotations

from dishka import Container, Provider, Scope, from_context, make_container, provide

from lrcforge.di.providers import (
    ConfigProvider,
    FakeStagesProvider,
    RealStagesProvider,
    WriterProvider,
)
from lrcforge.jobs.context import JobContext
from lrcforge.jobs.progress import JobProgressReporter
from lrcforge.jobs.store import JobStore
from lrcforge.pipeline.orchestrator import AlignPipeline
from lrcforge.ports.aligner import ForcedAligner
from lrcforge.ports.audio_loader import AudioLoader
from lrcforge.ports.language_detector import LanguageDetector
from lrcforge.ports.lrc_writer import LrcWriter
from lrcforge.ports.lyrics_provider import LyricsProvider
from lrcforge.ports.progress import ProgressReporter
from lrcforge.ports.separator import SourceSeparator


class WebProvider(Provider):
    job_context = from_context(provides=JobContext, scope=Scope.REQUEST)

    @provide(scope=Scope.APP)
    def store(self) -> JobStore:
        return JobStore()

    @provide(scope=Scope.REQUEST)
    def progress(self, ctx: JobContext, store: JobStore) -> ProgressReporter:
        return JobProgressReporter(ctx.job_id, store)

    @provide(scope=Scope.REQUEST)
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


def build_web_container(*, fakes: bool = False) -> Container:
    stages: Provider = FakeStagesProvider() if fakes else RealStagesProvider()
    return make_container(
        ConfigProvider(),
        WriterProvider(),
        stages,
        WebProvider(),
    )
