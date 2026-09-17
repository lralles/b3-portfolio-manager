from __future__ import annotations

from pathlib import Path

from config import Config
from ..models.holding import Holding
from ..repositories.holding_repository import HoldingRepository


class HoldingService:
    """Application service for the stored custody/holding catalog."""

    def __init__(self, path: Path | None = None, config: Config | None = None) -> None:
        self.config = config or Config()
        self._repository = HoldingRepository(path, self.config)

    def all(self) -> list[Holding]:
        return self._repository.all()

    def save(self, holdings: list[Holding]) -> None:
        self._repository.save(holdings)
