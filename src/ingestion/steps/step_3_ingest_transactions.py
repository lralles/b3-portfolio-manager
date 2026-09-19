from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

from config import Config
from src.core.models.asset import Asset
from src.core.models.holding import Holding
from src.core.models.transaction import Transaction, TransactionOperationType
from src.core.models.trading_price import TradingPrice
from src.core.repositories.trading_price_repository import TradingPriceRepository
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
    config: Config | None = None,
    trading_prices_path: Path | None = None,
) -> list[Transaction]:
    config = config or Config()
    trading_prices_path = trading_prices_path or config.trading_prices_file
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
    AssetService(assets_path, config).save(asset_models)
    HoldingService(holdings_path, config).save(holding_models)
    assets = {asset.asset_name: asset for asset in asset_models}
    holdings = {holding.holding_name: holding for holding in holding_models}
    transactions = [
        transaction_from_sanitized_row(
            row,
            transaction_id=f"transaction_{index:03d}",
            asset_id=assets[row["produto"].strip()].asset_id,
            holding_id=holdings[row["instituicao"].strip()].holding_id,
        )
        for index, row in enumerate(rows, start=1)
    ]
    TransactionService(output_path, config).save(transactions)

    _save_transaction_trading_prices(transactions, trading_prices_path, config)
    return transactions


def _save_transaction_trading_prices(
    transactions: list[Transaction],
    trading_prices_path: Path,
    config: Config,
) -> None:
    prices_by_key: dict[tuple[str, date], TradingPrice] = {}
    for transaction in transactions:
        if transaction.operation_type not in (
            TransactionOperationType.PURCHASE,
            TransactionOperationType.SALE,
        ) or transaction.unit_price is None:
            continue
        key = (transaction.asset_id, transaction.date)
        # Multiple trades on the same asset/date are equivalent for this store;
        # retain the first one encountered.
        prices_by_key.setdefault(
            key,
            TradingPrice(
                asset_id=transaction.asset_id,
                evaluation_date=transaction.date,
                value=transaction.unit_price,
            ),
        )

    TradingPriceRepository(trading_prices_path, config).save(prices_by_key.values())


def main() -> int:
    config = Config()
    parser = argparse.ArgumentParser(description="Ingest sanitized transactions.")
    parser.add_argument("--input", type=Path, default=config.sanitized_transactions_file)
    parser.add_argument("--output", type=Path, default=config.transactions_file)
    parser.add_argument("--assets", type=Path, default=config.assets_file)
    parser.add_argument("--holdings", type=Path, default=config.holdings_file)
    parser.add_argument(
        "--trading-prices", type=Path, default=config.trading_prices_file
    )
    args = parser.parse_args()
    transactions = ingest(
        args.input,
        args.output,
        args.assets,
        args.holdings,
        trading_prices_path=args.trading_prices,
    )
    print(
        f"Wrote {len(transactions)} transactions, assets, and holdings "
        f"to {args.output.parent.parent}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
