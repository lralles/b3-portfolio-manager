from __future__ import annotations

from collections import defaultdict, deque
from decimal import Decimal
from typing import Iterable

from ..models.position import Position
from ..models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionOperationType,
)
from ..repositories.position_repository import PositionRepository
from ..repositories.transaction_repository import TransactionRepository


POSITION_OPERATION_SIGNS = {
    TransactionOperationType.PURCHASE: 1,
    TransactionOperationType.SALE: -1,
    TransactionOperationType.SETTLEMENT_TRANSFER: 1,
}


def build_positions(transactions: Iterable[Transaction]) -> list[Position]:
    """Aggregate only operations that change an asset holding.

    Income-like operations, interest, and dividends are deliberately excluded.
    Custody transfers change the account holding but not the portfolio holding,
    so invested capital is moved from the source account to the destination.
    """
    transactions = sorted(
        enumerate(transactions),
        key=lambda item: (
            item[1].date,
            # A transfer debit must be processed before its matching credit so
            # that the source capital is available to carry over.
            0
            if item[1].operation_type is TransactionOperationType.TRANSFER
            and item[1].direction is TransactionDirection.DEBIT
            else 2
            if item[1].operation_type is TransactionOperationType.TRANSFER
            and item[1].direction is TransactionDirection.CREDIT
            else 1,
            item[0],
        ),
    )
    totals: dict[tuple[str, str], list[Decimal]] = defaultdict(
        lambda: [Decimal("0"), Decimal("0")]
    )
    transferred_capital: dict[str, deque[tuple[Decimal, Decimal]]] = defaultdict(deque)

    for _, transaction in transactions:
        if transaction.operation_type is TransactionOperationType.TRANSFER:
            _apply_custody_transfer(totals, transferred_capital, transaction)
            continue

        sign = POSITION_OPERATION_SIGNS.get(transaction.operation_type)
        if sign is None:
            continue

        quantity = transaction.quantity or Decimal("0")
        operation_value = transaction.operation_value or Decimal("0")
        quantity_sign = (
            1
            if transaction.direction is TransactionDirection.CREDIT
            else -1
            if transaction.operation_type is TransactionOperationType.SETTLEMENT_TRANSFER
            else sign
        )
        totals[(transaction.asset_id, transaction.account_id)][0] += quantity_sign * quantity
        capital_sign = (
            1
            if transaction.operation_type is TransactionOperationType.SETTLEMENT_TRANSFER
            and transaction.direction is TransactionDirection.CREDIT
            else -1
            if transaction.operation_type is TransactionOperationType.SETTLEMENT_TRANSFER
            and transaction.direction is TransactionDirection.DEBIT
            else sign
        )
        totals[(transaction.asset_id, transaction.account_id)][1] += (
            capital_sign * operation_value
        )

    return [
        Position(
            asset_id=asset_id,
            account_id=account_id,
            quantity=values[0],
            invested_capital=values[1],
        )
        for (asset_id, account_id), values in sorted(totals.items())
    ]


def _apply_custody_transfer(
    totals: dict[tuple[str, str], list[Decimal]],
    transferred_capital: dict[str, deque[tuple[Decimal, Decimal]]],
    transaction: Transaction,
) -> None:
    quantity = transaction.quantity or Decimal("0")
    position = totals[(transaction.asset_id, transaction.account_id)]

    if transaction.direction is TransactionDirection.DEBIT:
        source_quantity = position[0]
        capital = (
            position[1] * quantity / source_quantity
            if source_quantity
            else Decimal("0")
        )
        position[0] -= quantity
        position[1] -= capital
        transferred_capital[transaction.asset_id].append((quantity, capital))
        return

    remaining_quantity = quantity
    capital = Decimal("0")
    capital_transfers = transferred_capital[transaction.asset_id]
    while remaining_quantity and capital_transfers:
        transfer_quantity, transfer_capital = capital_transfers[0]
        applied_quantity = min(remaining_quantity, transfer_quantity)
        capital += transfer_capital * applied_quantity / transfer_quantity
        remaining_quantity -= applied_quantity
        transfer_quantity -= applied_quantity
        transfer_capital -= transfer_capital * applied_quantity / (transfer_quantity + applied_quantity)
        if transfer_quantity:
            capital_transfers[0] = (transfer_quantity, transfer_capital)
        else:
            capital_transfers.popleft()

    position[0] += quantity
    position[1] += capital


class PositionBuildService:
    def __init__(
        self,
        transaction_repository: TransactionRepository | None = None,
        position_repository: PositionRepository | None = None,
    ) -> None:
        self.transaction_repository = transaction_repository or TransactionRepository()
        self.position_repository = position_repository or PositionRepository()

    def build(self) -> list[Position]:
        return build_positions(self.transaction_repository.all())

    def build_and_save(self) -> list[Position]:
        positions = self.build()
        self.position_repository.save(positions)
        return positions

    def save(self) -> list[Position]:
        """Build positions from the transaction repository and persist them."""
        return self.build_and_save()


def build_and_save_positions(
    transaction_repository: TransactionRepository | None = None,
    position_repository: PositionRepository | None = None,
) -> list[Position]:
    return PositionBuildService(transaction_repository, position_repository).save()
