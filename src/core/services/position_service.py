from __future__ import annotations

from ..models.position import Position
from ..models.profit_loss import ProfitLoss
from ..repositories.asset_repository import AssetRepository
from ..repositories.profit_loss_repository import ProfitLossRepository
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
        profit_loss_repository: ProfitLossRepository | None = None,
    ) -> None:
        self.transaction_repository = transaction_repository or TransactionRepository()
        self.position_repository = position_repository or PositionRepository()
        self.asset_repository = asset_repository or AssetRepository()
        self.profit_loss_repository = profit_loss_repository or ProfitLossRepository()

    def build(self) -> tuple[list[Position], list[ProfitLoss]]:
        return build_positions(self.transaction_repository.all())

    def build_and_save(self) -> tuple[list[Position], list[ProfitLoss]]:
        positions, profit_losses = self.build()
        self.position_repository.save(positions)
        self.profit_loss_repository.save(profit_losses)
        return positions, profit_losses

    def save(self) -> tuple[list[Position], list[ProfitLoss]]:
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
) -> tuple[list[Position], list[ProfitLoss]]:
    return PositionService(transaction_repository, position_repository).save()
