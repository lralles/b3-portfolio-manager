from __future__ import annotations

from pathlib import Path

from config import Config
from ..models.source_position import SourcePosition
from ..repositories.source_position_repository import SourcePositionRepository


class SourcePositionService:
    """Application service for broker-reported source positions."""

    def __init__(
        self,
        path: Path | None = None,
        config: Config | None = None,
    ) -> None:
        self.config = config or Config()
        self._repository = SourcePositionRepository(path, self.config)

    def all(self) -> list[SourcePosition]:
        return self._repository.all()

    def save(self, positions: list[SourcePosition]) -> None:
        self._repository.save(positions)
