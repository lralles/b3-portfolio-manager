from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
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
from src.ingestion.custom_operations import CorporateAction, load, transactions_for


def reference_id(prefix: str, name: str, names: list[str]) -> str:
    return f"{prefix}_{names.index(name) + 1:03d}"


def asset_key(name: str) -> str:
    """Use the B3 ticker to identify products with varying descriptions."""
    match = re.match(r"^([A-Z0-9]{4,6})\s+-\s+", name.strip())
    return match.group(1) if match else name.strip()


TRANSFERRED_INCOME_OPERATION_MAP = {
    "dividendo - transferido": "dividendo",
    "juros sobre capital próprio - transferido": "juros sobre capital próprio",
}


def normalize_transferred_income_rows(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Collapse custody debit/credit pairs into one credited income event."""
    grouped: dict[tuple[str, ...], dict[str, list[dict[str, str]]]] = defaultdict(
        lambda: {"debito": [], "credito": []}
    )
    group_order: list[tuple[str, ...]] = []
    normalized_rows: list[dict[str, str]] = []

    for row in rows:
        operation = row["movimentacao"].strip().lower()
        if operation not in TRANSFERRED_INCOME_OPERATION_MAP:
            normalized_rows.append(row)
            continue

        key = (
            operation,
            row["data"].strip(),
            row["produto"].strip(),
            row["quantidade"].strip(),
            row["preco_unitario"].strip(),
            row["valor_operacao"].strip(),
        )
        if key not in grouped:
            group_order.append(key)
        direction = row["entrada_saida"].strip().lower()
        if direction not in ("debito", "credito"):
            raise ValueError(
                f"Unknown direction for transferred income: {direction!r}"
            )
        grouped[key][direction].append(row)

    transferred_rows: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for key in group_order:
        group = grouped[key]
        if len(group["debito"]) != len(group["credito"]):
            raise ValueError(
                "Transferred income must have matching debit and credit rows: "
                f"{key!r} (debit={len(group['debito'])}, "
                f"credit={len(group['credito'])})"
            )
        normalized_operation = TRANSFERRED_INCOME_OPERATION_MAP[key[0]]
        transferred_rows[key] = []
        for row in group["credito"]:
            normalized_row = dict(row)
            normalized_row["movimentacao"] = normalized_operation
            transferred_rows[key].append(normalized_row)

    result: list[dict[str, str]] = []
    emitted_groups: set[tuple[str, ...]] = set()
    for row in rows:
        operation = row["movimentacao"].strip().lower()
        if operation not in TRANSFERRED_INCOME_OPERATION_MAP:
            result.append(row)
            continue
        key = (
            operation,
            row["data"].strip(),
            row["produto"].strip(),
            row["quantidade"].strip(),
            row["preco_unitario"].strip(),
            row["valor_operacao"].strip(),
        )
        if key not in emitted_groups:
            result.extend(transferred_rows[key])
            emitted_groups.add(key)
    return result


def ingest(
    input_path: Path,
    output_path: Path,
    assets_path: Path,
    holdings_path: Path,
    config: Config | None = None,
    trading_prices_path: Path | None = None,
    custom_operations_path: Path | None = None,
) -> list[Transaction]:
    config = config or Config()
    trading_prices_path = trading_prices_path or config.trading_prices_file
    custom_operations_path = custom_operations_path or (
        input_path.parent.parent / "custom_operations" / "corporate_actions.csv"
    )
    with input_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    corporate_actions = load(custom_operations_path)
    rows = [row for row in rows if not _is_replaced_by_custom_action(row, corporate_actions)]
    rows = normalize_transferred_income_rows(rows)

    names_by_key: dict[str, list[str]] = {}
    for row in rows:
        name = row["produto"].strip()
        names_by_key.setdefault(asset_key(name), []).append(name)
    for action in corporate_actions:
        for name in (
            action.source_product,
            action.target_product,
            action.redemption_product,
        ):
            if name.strip():
                names_by_key.setdefault(asset_key(name), []).append(name)
    asset_names = sorted(min(names) for names in names_by_key.values())
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
    assets = {asset_key(asset.asset_name): asset for asset in asset_models}
    holdings = {holding.holding_name: holding for holding in holding_models}
    transactions = [
        transaction_from_sanitized_row(
            row,
            transaction_id=f"transaction_{index:03d}",
            asset_id=assets[asset_key(row["produto"])].asset_id,
            holding_id=holdings[row["instituicao"].strip()].holding_id,
        )
        for index, row in enumerate(rows, start=1)
    ]
    next_transaction_number = len(transactions) + 1
    for action in corporate_actions:
        action_transactions = transactions_for(
            action,
            assets,
            holdings,
            next_transaction_number,
        )
        transactions.extend(action_transactions)
        next_transaction_number += len(action_transactions)
    TransactionService(output_path, config).save(transactions)

    _save_transaction_trading_prices(transactions, trading_prices_path, config)
    return transactions


def _is_replaced_by_custom_action(
    row: dict[str, str], corporate_actions: list[CorporateAction]
) -> bool:
    operation = row["movimentacao"].strip().lower()
    row_date = row["data"].strip()
    row_asset = asset_key(row["produto"])
    for action in corporate_actions:
        if operation == "incorporação" and row_date == action.date.isoformat():
            return True
        if (
            operation == "resgate"
            and action.redemption_date is not None
            and row_date == action.redemption_date.isoformat()
            and row_asset == asset_key(action.redemption_product)
        ):
            return True
        if (
            operation == "vencimento"
            and action.redemption_date is not None
            and row_date == action.redemption_date.isoformat()
            and row_asset == asset_key(action.redemption_product)
        ):
            return True
        if (
            operation == "fração em ativos"
            and row_date == action.fraction_settlement_date.isoformat()
            and row_asset == asset_key(action.target_product)
        ):
            return True
    return False


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
    parser.add_argument(
        "--custom-operations",
        type=Path,
        default=config.sanitized_dir / "custom_operations" / "corporate_actions.csv",
    )
    args = parser.parse_args()
    transactions = ingest(
        args.input,
        args.output,
        args.assets,
        args.holdings,
        trading_prices_path=args.trading_prices,
        custom_operations_path=args.custom_operations,
    )
    print(
        f"Wrote {len(transactions)} transactions, assets, and holdings "
        f"to {args.output.parent.parent}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
