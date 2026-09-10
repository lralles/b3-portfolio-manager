from __future__ import annotations

from dataclasses import dataclass

from ...models.position import Position
from ...models.source_position import SourcePosition


@dataclass(frozen=True, slots=True)
class PositionConflict:
    """A source position that does not match the computed position."""

    position: Position | None
    source_position: SourcePosition

    @property
    def computed_position(self) -> Position | None:
        return self.position

