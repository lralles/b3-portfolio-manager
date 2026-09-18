from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping

from config import Config
from ..models.asset import Asset, AssetType


ASSET_COLUMNS = ["asset_id", "asset_name", "isin", "asset_type"]


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
            return [_from_store_row(row) for row in csv.DictReader(fh)]

    def save(self, assets: Iterable[Asset]) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=ASSET_COLUMNS)
            writer.writeheader()
            writer.writerows(_to_store_row(asset) for asset in assets)

    def update(self, asset: Asset) -> Asset:
        assets = self.all()
        for index, stored_asset in enumerate(assets):
            if stored_asset.asset_id == asset.asset_id:
                assets[index] = asset
                self.save(assets)
                return asset
        raise ValueError(f"No stored asset found for {asset.asset_id!r}")


def _to_store_row(asset: Asset) -> dict[str, str]:
    return {
        "asset_id": asset.asset_id,
        "asset_name": asset.asset_name,
        "isin": asset.isin or "",
        "asset_type": asset.asset_type.value if asset.asset_type else "",
    }


def _from_store_row(row: Mapping[str, str]) -> Asset:
    try:
        asset_id = row["asset_id"].strip()
        asset_name = row["asset_name"].strip()
        isin = row.get("isin", "").strip() or None
        asset_type_value = row.get("asset_type", "").strip()
        asset_type = AssetType(asset_type_value) if asset_type_value else None
    except KeyError as exc:
        raise ValueError(f"Missing stored asset field: {exc.args[0]}") from exc

    if not asset_id:
        raise ValueError("Stored asset has an empty asset_id")
    if not asset_name:
        raise ValueError(f"Stored asset {asset_id!r} has an empty asset_name")

    return Asset(
        asset_id=asset_id,
        asset_name=asset_name,
        isin=isin,
        asset_type=asset_type,
    )
