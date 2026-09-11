from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.core.models.asset import Asset
from src.core.models.holding import Holding
from src.core.models.transaction import Transaction
from src.core.services.asset_service import AssetService
from src.core.services.holding_service import HoldingService
from src.core.services.transaction_service import TransactionService
from src.ingestion.b3.transaction_mapper import transaction_from_sanitized_row


def reference_id(prefix: str, name: str, names: list[str]) -> str:
    return f"{prefix}_{names.index(name) + 1:03d}"


def ingest(
    input_path: Path,
    output_path: Path,
    assets_path: Path,
    holdings_path: Path,
) -> list[Transaction]:
    with input_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    asset_names = sorted({row["produto"].strip() for row in rows})
    holding_names = sorted({row["instituicao"].strip() for row in rows})
    asset_models = [
        Asset(reference_id("asset", name, asset_names), name)
        for name in asset_names
    ]
    holding_models = [
        Holding(reference_id("holding", name, holding_names), name)
        for name in holding_names
    ]
    # Recreate these catalogs before mapping transactions because their IDs are
    # required by the canonical transaction model.
    AssetService(assets_path).save(asset_models)
    HoldingService(holdings_path).save(holding_models)
    assets = {asset.asset_name: asset for asset in asset_models}
    holdings = {holding.holding_name: holding for holding in holding_models}
    transactions = [
        transaction_from_sanitized_row(
            row,
            asset_id=assets[row["produto"].strip()].asset_id,
            holding_id=holdings[row["instituicao"].strip()].holding_id,
        )
        for row in rows
    ]
    TransactionService(output_path).save(transactions)
    return transactions


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest sanitized transactions.")
    parser.add_argument("--input", type=Path, default=Path("data/santized/transactions/transactions.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/store/transactions/transactions.csv"))
    parser.add_argument("--assets", type=Path, default=Path("data/store/assets/assets.csv"))
    parser.add_argument("--holdings", type=Path, default=Path("data/store/holdings/holdings.csv"))
    args = parser.parse_args()
    transactions = ingest(args.input, args.output, args.assets, args.holdings)
    print(
        f"Wrote {len(transactions)} transactions, assets, and holdings "
        f"to {args.output.parent.parent}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
