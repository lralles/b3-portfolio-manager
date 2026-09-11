from __future__ import annotations

import argparse
from pathlib import Path

from src.ingestion.steps.step_1_sanitize_transactions import sanitize as sanitize_transactions
from src.ingestion.steps.step_2_sanitize_source_positions import sanitize as sanitize_source_positions
from src.ingestion.steps.step_3_ingest_transactions import ingest as ingest_transactions
from src.ingestion.steps.step_4_ingest_source_positions import ingest as ingest_source_positions
from src.ingestion.steps.step_5_reconcile_positions import reconcile


def run(
    raw_transactions: Path = Path("data/raw/transactions"),
    raw_position: Path = Path("data/raw/position/2020/posicao-2020-12-31.xlsx"),
    sanitized_dir: Path = Path("data/santized"),
    store_dir: Path = Path("data/store"),
):
    """Run sanitization, ingestion, and quality checks in dependency order."""
    sanitized_transactions = sanitized_dir / "transactions/transactions.csv"
    sanitized_positions = sanitized_dir / "positions/source_positions.csv"
    assets = store_dir / "assets/assets.csv"
    holdings = store_dir / "holdings/holdings.csv"
    transactions = store_dir / "transactions/transactions.csv"
    source_positions = store_dir / "source_positions/source_positions.csv"
    positions = store_dir / "computed_positions/positions.csv"

    sanitize_transactions(raw_transactions, sanitized_transactions)
    sanitize_source_positions(raw_position, sanitized_positions)
    ingest_transactions(sanitized_transactions, transactions, assets, holdings)
    ingest_source_positions(sanitized_positions, source_positions, assets)
    status = reconcile(transactions, positions, assets, source_positions)
    if status.status != "success":
        raise ValueError(f"Position reconciliation failed: {status.conflicts}")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the complete B3 portfolio pipeline.")
    parser.add_argument("--raw-transactions", type=Path, default=Path("data/raw/transactions"))
    parser.add_argument("--raw-position", type=Path, default=Path("data/raw/position/2020/posicao-2020-12-31.xlsx"))
    parser.add_argument("--sanitized-dir", type=Path, default=Path("data/santized"))
    parser.add_argument("--store-dir", type=Path, default=Path("data/store"))
    args = parser.parse_args()
    run(args.raw_transactions, args.raw_position, args.sanitized_dir, args.store_dir)
    print("Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
