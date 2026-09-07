from __future__ import annotations

from ..models.position import Position
from ..repositories.asset_repository import AssetRepository
from ..repositories.position_repository import PositionRepository


class PositionService:
    """Reads stored positions and attaches their corresponding assets."""

    def __init__(
        self,
        position_repository: PositionRepository | None = None,
        asset_repository: AssetRepository | None = None,
    ) -> None:
        self.position_repository = position_repository or PositionRepository()
        self.asset_repository = asset_repository or AssetRepository()

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
