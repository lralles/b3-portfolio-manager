from __future__ import annotations

from pathlib import Path

from config import Config
from ..models.transaction import Transaction
from ..repositories.transaction_repository import TransactionRepository


class TransactionService:
    """Application service for the canonical transaction store."""

    def __init__(
        self, path: Path | None = None, config: Config | None = None
    ) -> None:
        self.config = config or Config()
        self._repository = TransactionRepository(path, self.config)

    def all(self) -> list[Transaction]:
        return self._repository.all()

    def save(self, transactions: list[Transaction]) -> None:
        self._repository.save(transactions)
