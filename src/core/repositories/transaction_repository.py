from __future__ import annotations

import csv
from pathlib import Path

from ..models.transaction import Transaction


class TransactionRepository:
    def __init__(self, csv_path: Path = Path("data/store/transactions/transactions.csv")) -> None:
        self.csv_path = csv_path

    def all(self) -> list[Transaction]:
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            return [Transaction.from_store_row(row) for row in csv.DictReader(fh)]
