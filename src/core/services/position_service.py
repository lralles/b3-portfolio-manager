from __future__ import annotations

from ..models.position import Position
from ..repositories.asset_repository import AssetRepository
from ..repositories.position_repository import PositionRepository
from ..repositories.transaction_repository import TransactionRepository
from .position_build import build_positions


class PositionService:
    """Builds, persists, and reads the position projection."""

    def __init__(
        self,
        transaction_repository: TransactionRepository | None = None,
        position_repository: PositionRepository | None = None,
        asset_repository: AssetRepository | None = None,
    ) -> None:
        self.transaction_repository = transaction_repository or TransactionRepository()
        self.position_repository = position_repository or PositionRepository()
        self.asset_repository = asset_repository or AssetRepository()

    def build(self) -> list[Position]:
        return build_positions(self.transaction_repository.all())

    def build_and_save(self) -> list[Position]:
        positions = self.build()
        self.position_repository.save(positions)
        return positions

    def save(self) -> list[Position]:
        return self.build_and_save()

    def all(self) -> list[Position]:
        assets = {asset.asset_id: asset for asset in self.asset_repository.all()}
        positions = []
        for position in self.position_repository.all():
            try:
                asset = assets[position.asset_id]
            except KeyError as exc:
                raise ValueError(
                    f"No stored asset found for position {position.asset_id!r}"
                ) from exc
            positions.append(position.with_asset(asset))
        return positions


def build_and_save_positions(
    transaction_repository: TransactionRepository | None = None,
    position_repository: PositionRepository | None = None,
) -> list[Position]:
    return PositionService(transaction_repository, position_repository).save()
