from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from dataclasses import replace
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
    asset_service = AssetService(assets_path, config)
    lookup: dict[str, Asset] = {}
    for asset in asset_service.all():
        lookup[normalized(asset.asset_name)] = asset
        lookup.setdefault(normalized(asset.asset_name.split(" - ", 1)[0]), asset)
    positions = []
    for row in rows:
        asset = lookup.get(normalized(row["Produto"])) or lookup.get(
            normalized(row["Produto"].split(" - ", 1)[0])
        )
        isin = row.get("Código ISIN", "").strip()
        asset_type_value = row.get("asset_type", "").strip()
        if asset and (isin or asset_type_value):
            asset_service.update(
                replace(
                    asset,
                    isin=isin or asset.isin,
                    asset_type=(
                        AssetType(asset_type_value)
                        if asset_type_value
                        else asset.asset_type
                    ),
                )
            )
        positions.append(
            source_position_from_sanitized_row(row, asset.asset_id if asset else None)
        )
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
