from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from ...models.position import Position
from ...models.transaction import Transaction


@dataclass(slots=True)
class PositionAccumulator:
    """Mutable calculation state for one asset during a build."""

    asset_id: str
    current_quantity: Decimal = Decimal("0")
    total_acquired_quantity: Decimal = Decimal("0")
    total_sold_quantity: Decimal = Decimal("0")
    invested_capital: Decimal = Decimal("0")

    def to_position(self) -> Position:
        return Position(
            asset_id=self.asset_id,
            current_quantity=self.current_quantity,
            total_acquired_quantity=self.total_acquired_quantity,
            total_sold_quantity=self.total_sold_quantity,
            invested_capital=self.invested_capital,
        )


class PositionTransactionHandler(Protocol):
    def apply(self, position: PositionAccumulator, transaction: Transaction) -> None:
        ...


def quantity_of(transaction: Transaction) -> Decimal:
    return transaction.quantity or Decimal("0")


def operation_value_of(transaction: Transaction) -> Decimal:
    return transaction.operation_value or Decimal("0")


class PurchaseHandler:
    def apply(self, position: PositionAccumulator, transaction: Transaction) -> None:
        quantity = quantity_of(transaction)
        position.current_quantity += quantity
        position.total_acquired_quantity += quantity
        position.invested_capital += operation_value_of(transaction)


class SaleHandler:
    def apply(self, position: PositionAccumulator, transaction: Transaction) -> None:
        quantity = quantity_of(transaction)
        position.current_quantity -= quantity
        position.total_sold_quantity += quantity


class CustodyTransferHandler:
    """Custody movements are globally neutral across all holdings."""

    def apply(self, position: PositionAccumulator, transaction: Transaction) -> None:
        return None


class IgnoredTransactionHandler:
    def apply(self, position: PositionAccumulator, transaction: Transaction) -> None:
        return None


class CorporateActionHandler:
    """Marker handler for operations applied by the position builder."""

    def apply(self, position: PositionAccumulator, transaction: Transaction) -> None:
        return None
