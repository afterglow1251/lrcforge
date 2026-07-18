from __future__ import annotations

from collections.abc import Iterator

import pytest
from dishka import Container

from lrcforge.di.container import build_container
from lrcforge.pipeline.orchestrator import AlignPipeline


@pytest.fixture
def container() -> Iterator[Container]:
    c = build_container()
    yield c
    c.close()


@pytest.fixture
def pipeline(container: Container) -> AlignPipeline:
    return container.get(AlignPipeline)
