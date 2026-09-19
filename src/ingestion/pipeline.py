from __future__ import annotations

import argparse
from pathlib import Path

from config import Config
from src.ingestion.steps.step_1_sanitize_transactions import sanitize as sanitize_transactions
from src.ingestion.steps.step_2_sanitize_source_positions import sanitize as sanitize_source_positions
from src.ingestion.steps.step_3_ingest_transactions import ingest as ingest_transactions
from src.ingestion.steps.step_4_ingest_source_positions import ingest as ingest_source_positions
from src.ingestion.steps.step_5_reconcile_positions import reconcile


def run(
    raw_transactions: Path | None = None,
    raw_position: Path | None = None,
    sanitized_dir: Path | None = None,
    store_dir: Path | None = None,
    trading_prices: Path | None = None,
):
    """Run sanitization, ingestion, and quality checks in dependency order."""
    config = Config()
    raw_transactions = raw_transactions or config.raw_transactions_dir
    raw_position = raw_position or config.raw_position_file
    sanitized_dir = sanitized_dir or config.sanitized_dir
    store_dir = store_dir or config.store_dir
    sanitized_transactions = sanitized_dir / config.sanitized_transactions_file.relative_to(
        config.sanitized_dir
    )
    sanitized_positions = sanitized_dir / config.sanitized_positions_file.relative_to(
        config.sanitized_dir
    )
    assets = store_dir / config.assets_file.relative_to(config.store_dir)
    holdings = store_dir / config.holdings_file.relative_to(config.store_dir)
    transactions = store_dir / config.transactions_file.relative_to(config.store_dir)
    source_positions = store_dir / config.source_positions_file.relative_to(config.store_dir)
    trading_prices = trading_prices or store_dir / config.trading_prices_file.relative_to(
        config.store_dir
    )
    positions = store_dir / config.positions_file.relative_to(config.store_dir)
    profit_losses = store_dir / config.profit_losses_file.relative_to(config.store_dir)

    sanitize_transactions(raw_transactions, sanitized_transactions)
    sanitize_source_positions(raw_position, sanitized_positions)
    ingest_transactions(sanitized_transactions, transactions, assets, holdings, config)
    ingest_source_positions(
        sanitized_positions,
        source_positions,
        assets,
        config,
        trading_prices_path=trading_prices,
    )
    status = reconcile(transactions, positions, assets, source_positions, profit_losses, config)
    if status.status != "success":
        raise ValueError(f"Position reconciliation failed: {status.conflicts}")
    return status


def main() -> int:
    config = Config()
    parser = argparse.ArgumentParser(description="Run the complete B3 portfolio pipeline.")
    parser.add_argument("--raw-transactions", type=Path, default=config.raw_transactions_dir)
    parser.add_argument("--raw-position", type=Path, default=config.raw_position_file)
    parser.add_argument("--sanitized-dir", type=Path, default=config.sanitized_dir)
    parser.add_argument("--store-dir", type=Path, default=config.store_dir)
    args = parser.parse_args()
    run(args.raw_transactions, args.raw_position, args.sanitized_dir, args.store_dir)
    print("Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
