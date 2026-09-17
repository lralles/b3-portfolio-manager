from __future__ import annotations

from pathlib import Path

from config import Config
from ..models.asset import Asset
from ..repositories.asset_repository import AssetRepository


class AssetService:
    """Application service for the stored asset catalog."""

    def __init__(self, path: Path | None = None, config: Config | None = None) -> None:
        self.config = config or Config()
        self._repository = AssetRepository(path, self.config)

    def all(self) -> list[Asset]:
        return self._repository.all()

    def save(self, assets: list[Asset]) -> None:
        self._repository.save(assets)

    def update(self, asset: Asset) -> Asset:
        return self._repository.update(asset)
