from __future__ import annotations

from pathlib import Path

from ..models.source_position import SourcePosition
from ..repositories.source_position_repository import SourcePositionRepository


class SourcePositionService:
    """Application service for broker-reported source positions."""

    def __init__(
        self,
        path: Path = Path("data/store/source_positions/source_positions.csv"),
    ) -> None:
        self._repository = SourcePositionRepository(path)

    def all(self) -> list[SourcePosition]:
        return self._repository.all()

    def save(self, positions: list[SourcePosition]) -> None:
        self._repository.save(positions)
