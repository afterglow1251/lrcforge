from __future__ import annotations

from dishka import Container, Provider, make_container

from lrcforge.di.providers import (
    ConfigProvider,
    CoreProvider,
    FakeStagesProvider,
    PipelineProvider,
    RealStagesProvider,
)


def build_container(*, fakes: bool = True) -> Container:
    """Build the app container.

    fakes=True  -> zero-model pipeline (tests, `align --fake`, the M0 skeleton).
    fakes=False -> real ML adapters (Demucs, LID, Whisper, MMS). Construction is lazy,
    so building the container does not import torch; models load on first stage call.
    """
    stages: Provider = FakeStagesProvider() if fakes else RealStagesProvider()
    return make_container(
        ConfigProvider(),
        CoreProvider(),
        stages,
        PipelineProvider(),
    )
