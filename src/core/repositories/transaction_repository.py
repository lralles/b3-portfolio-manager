from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from ..models.transaction import Transaction


TRANSACTION_COLUMNS = [
    "io_flow",
    "date",
    "operation_type",
    "asset_id",
    "holding_id",
    "quantity",
    "unit_price",
    "operation_value",
]


class TransactionRepository:
    def __init__(self, csv_path: Path = Path("data/store/transactions/transactions.csv")) -> None:
        self.csv_path = csv_path

    def all(self) -> list[Transaction]:
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            return [Transaction.from_store_row(row) for row in csv.DictReader(fh)]

    def save(self, transactions: Iterable[Transaction]) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=TRANSACTION_COLUMNS)
            writer.writeheader()
            writer.writerows(_to_store_row(transaction) for transaction in transactions)


def _to_store_row(transaction: Transaction) -> dict[str, str]:
    return {
        "io_flow": transaction.io_flow.value,
        "date": transaction.date.isoformat(),
        "operation_type": transaction.operation_type.value,
        "asset_id": transaction.asset_id,
        "holding_id": transaction.holding_id,
        "quantity": _format_decimal(transaction.quantity),
        "unit_price": _format_decimal(transaction.unit_price),
        "operation_value": _format_decimal(transaction.operation_value),
    }


def _format_decimal(value: Decimal | None) -> str:
    return "" if value is None else format(value, "f")
