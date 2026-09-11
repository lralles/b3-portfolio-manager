from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path

from src.core.services.asset_service import AssetService
from src.core.services.source_position_service import SourcePositionService
from src.ingestion.b3.source_position_mapper import source_position_from_sanitized_row


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def ingest(input_path: Path, output_path: Path, assets_path: Path):
    with input_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    lookup: dict[str, str] = {}
    for asset in AssetService(assets_path).all():
        lookup[normalized(asset.asset_name)] = asset.asset_id
        lookup.setdefault(normalized(asset.asset_name.split(" - ", 1)[0]), asset.asset_id)
    positions = [
        source_position_from_sanitized_row(
            row, lookup.get(normalized(row["Produto"]))
            or lookup.get(normalized(row["Produto"].split(" - ", 1)[0]))
        )
        for row in rows
    ]
    SourcePositionService(output_path).save(positions)
    return positions


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest source positions for quality checks.")
    parser.add_argument("--input", type=Path, default=Path("data/santized/positions/source_positions.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/store/source_positions/source_positions.csv"))
    parser.add_argument("--assets", type=Path, default=Path("data/store/assets/assets.csv"))
    args = parser.parse_args()
    positions = ingest(args.input, args.output, args.assets)
    print(f"Wrote {len(positions)} source positions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
