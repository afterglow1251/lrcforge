"""Semantic, constrained scalar aliases used across the domain models.

Annotated aliases (not NewType) so ordinary float arithmetic still works, while pydantic
enforces the range at validation time and the name documents intent."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

Seconds = Annotated[float, Field(ge=0.0)]
Confidence = Annotated[float, Field(ge=0.0, le=1.0)]
Fraction = Annotated[float, Field(ge=0.0, le=1.0)]
