from __future__ import annotations

from dishka import Container, make_container

from lrcforge.di.providers import (
    ConfigProvider,
    CoreProvider,
    FakeStagesProvider,
    PipelineProvider,
)


def build_container(*, fakes: bool = True) -> Container:
    """Build the app container. M0 supports fakes only; real ML adapters land at M2+."""
    if not fakes:
        raise NotImplementedError("real ML stage adapters land at M2+ (see PLAN.md §8)")
    return make_container(
        ConfigProvider(),
        CoreProvider(),
        FakeStagesProvider(),
        PipelineProvider(),
    )
