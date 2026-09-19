from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from dataclasses import replace
from datetime import date
from pathlib import Path

from config import Config
from src.core.models.asset import Asset, AssetType
from src.core.services.asset_service import AssetService
from src.core.services.source_position_service import SourcePositionService
from src.ingestion.b3.source_position_mapper import source_position_from_sanitized_row


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def ingest(
    input_path: Path,
    output_path: Path,
    assets_path: Path,
    config: Config | None = None,
):
    config = config or Config()
    with input_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    rows.sort(key=lambda row: date.fromisoformat(row["evaluation_date"].strip()))

    asset_service = AssetService(assets_path, config)
    assets = asset_service.all()
    assets_by_id = {asset.asset_id: asset for asset in assets}
    lookup: dict[str, Asset] = {}
    for asset in assets:
        lookup[normalized(asset.asset_name)] = asset
        lookup.setdefault(normalized(asset.asset_name.split(" - ", 1)[0]), asset)
    positions = []
    for row in rows:
        asset = lookup.get(normalized(row["Produto"])) or lookup.get(
            normalized(row["Produto"].split(" - ", 1)[0])
        )
        if asset:
            asset = assets_by_id[asset.asset_id]
        isin = row.get("Código ISIN", "").strip()
        asset_type_value = row.get("asset_type", "").strip()
        if asset:
            enriched_asset = replace(
                asset,
                isin=asset.isin or isin,
                asset_type=(
                    asset.asset_type
                    or AssetType(asset_type_value)
                    if asset_type_value
                    else asset.asset_type
                ),
            )
            assets_by_id[asset.asset_id] = enriched_asset
        positions.append(
            source_position_from_sanitized_row(row, asset.asset_id if asset else None)
        )
    asset_service.save(list(assets_by_id.values()))
    SourcePositionService(output_path, config).save(positions)
    return positions


def main() -> int:
    config = Config()
    parser = argparse.ArgumentParser(description="Ingest source positions for quality checks.")
    parser.add_argument("--input", type=Path, default=config.sanitized_positions_file)
    parser.add_argument("--output", type=Path, default=config.source_positions_file)
    parser.add_argument("--assets", type=Path, default=config.assets_file)
    args = parser.parse_args()
    positions = ingest(args.input, args.output, args.assets)
    print(f"Wrote {len(positions)} source positions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
