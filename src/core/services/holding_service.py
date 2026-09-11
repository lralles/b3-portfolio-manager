from __future__ import annotations

from pathlib import Path

from ..models.holding import Holding
from ..repositories.holding_repository import HoldingRepository


class HoldingService:
    """Application service for the stored custody/holding catalog."""

    def __init__(self, path: Path = Path("data/store/holdings/holdings.csv")) -> None:
        self._repository = HoldingRepository(path)

    def all(self) -> list[Holding]:
        return self._repository.all()

    def save(self, holdings: list[Holding]) -> None:
        self._repository.save(holdings)
