from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import asdict
from pathlib import Path

# Allow this file to be run directly from the repository root as well as with
# `python -m src.ingestion.format_transactions`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.models.account import Account
from core.models.asset import Asset
from core.models.transaction import FORMATTED_COLUMNS, Transaction


def load_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def reference_id(prefix: str, name: str, names: list[str]) -> str:
    return f"{prefix}_{names.index(name) + 1:03d}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert sanitized transaction CSV data into the typed formatted model."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/santized/transactions/transactions.csv"),
        help="Sanitized transaction CSV path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/store/transactions/transactions.csv"),
        help="Stored transaction CSV path.",
    )
    args = parser.parse_args()

    rows = load_rows(args.input)
    asset_names = sorted({row["produto"].strip() for row in rows})
    account_names = sorted({row["instituicao"].strip() for row in rows})
    assets = [
        Asset(reference_id("asset", name, asset_names), name) for name in asset_names
    ]
    accounts = [
        Account(reference_id("account", name, account_names), name)
        for name in account_names
    ]
    asset_ids = {asset.asset_name: asset.asset_id for asset in assets}
    account_ids = {account.account_name: account.account_id for account in accounts}
    transactions = [
        Transaction.from_sanitized_row(
            row,
            asset_id=asset_ids[row["produto"].strip()],
            account_id=account_ids[row["instituicao"].strip()],
        )
        for row in rows
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FORMATTED_COLUMNS)
        writer.writeheader()
        writer.writerows(transaction.to_formatted_row() for transaction in transactions)

    assets_path = args.output.parent.parent / "assets" / "assets.csv"
    accounts_path = args.output.parent.parent / "accounts" / "accounts.csv"
    assets_path.parent.mkdir(parents=True, exist_ok=True)
    accounts_path.parent.mkdir(parents=True, exist_ok=True)
    with assets_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["asset_id", "asset_name"])
        writer.writeheader()
        writer.writerows(asdict(asset) for asset in assets)
    with accounts_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["account_id", "account_name"])
        writer.writeheader()
        writer.writerows(asdict(account) for account in accounts)

    print(
        f"Wrote {len(transactions)} transactions, {len(assets)} assets, "
        f"and {len(accounts)} accounts to {args.output.parent.parent}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
