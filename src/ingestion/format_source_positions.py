from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.core.repositories.asset_repository import AssetRepository
from src.core.repositories.source_position_repository import SourcePositionRepository
from src.ingestion.b3.source_position_mapper import source_position_from_sanitized_row


def load_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def asset_lookup(asset_names: list[tuple[str, str]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for asset_id, asset_name in asset_names:
        lookup[normalized(asset_name)] = asset_id
        ticker = asset_name.split(" - ", 1)[0]
        lookup.setdefault(normalized(ticker), asset_id)
    return lookup


def asset_id_for_name(asset_name: str, lookup: dict[str, str]) -> str | None:
    asset_id = lookup.get(normalized(asset_name))
    if asset_id is not None:
        return asset_id
    ticker = asset_name.split(" - ", 1)[0]
    return lookup.get(normalized(ticker))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert sanitized source positions into the stored model."
    )
    parser.add_argument(
        "--input", type=Path,
        default=Path("data/santized/positions/source_positions.csv"),
        help="Sanitized source-position CSV path.",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/store/source_positions/source_positions.csv"),
        help="Stored source-position CSV path.",
    )
    parser.add_argument(
        "--assets", type=Path,
        default=Path("data/store/assets/assets.csv"),
        help="Existing asset table used to resolve asset_id.",
    )
    args = parser.parse_args()
    rows = load_rows(args.input)
    assets = AssetRepository(args.assets).all()
    lookup = asset_lookup([(asset.asset_id, asset.asset_name) for asset in assets])
    positions = [
        source_position_from_sanitized_row(
            row, asset_id_for_name(row["asset_name"], lookup)
        )
        for row in rows
    ]
    SourcePositionRepository(args.output).save(positions)
    print(f"Wrote {len(positions)} source positions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
