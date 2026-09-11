from __future__ import annotations

from pathlib import Path

from ..models.transaction import Transaction
from ..repositories.transaction_repository import TransactionRepository


class TransactionService:
    """Application service for the canonical transaction store."""

    def __init__(
        self, path: Path = Path("data/store/transactions/transactions.csv")
    ) -> None:
        self._repository = TransactionRepository(path)

    def all(self) -> list[Transaction]:
        return self._repository.all()

    def save(self, transactions: list[Transaction]) -> None:
        self._repository.save(transactions)
