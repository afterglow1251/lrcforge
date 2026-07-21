from __future__ import annotations

from dishka import Container, Provider, make_container

from lrcforge.di.providers import (
    CliRuntimeProvider,
    ConfigProvider,
    FakeStagesProvider,
    RealStagesProvider,
    WriterProvider,
)


def build_container(*, fakes: bool = True) -> Container:
    """Build the CLI container.

    fakes=True  -> zero-model pipeline (tests, `align --fake`).
    fakes=False -> real ML adapters. Construction is lazy, so building the container does
    not import torch; models load on first stage call.
    """
    stages: Provider = FakeStagesProvider() if fakes else RealStagesProvider()
    return make_container(
        ConfigProvider(),
        WriterProvider(),
        stages,
        CliRuntimeProvider(),
    )
