from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from config import Config
from ..models.asset import Asset


ASSET_COLUMNS = ["asset_id", "asset_name"]


class AssetRepository:
    def __init__(
        self,
        csv_path: Path | None = None,
        config: Config | None = None,
    ) -> None:
        self.config = config or Config()
        self.csv_path = csv_path or self.config.assets_file

    def all(self) -> list[Asset]:
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            return [Asset.from_store_row(row) for row in csv.DictReader(fh)]

    def save(self, assets: Iterable[Asset]) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=ASSET_COLUMNS)
            writer.writeheader()
            writer.writerows(_to_store_row(asset) for asset in assets)


def _to_store_row(asset: Asset) -> dict[str, str]:
    return {
        "asset_id": asset.asset_id,
        "asset_name": asset.asset_name,
    }
