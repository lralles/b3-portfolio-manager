from __future__ import annotations

from typing import Iterable

from ..models.position import Position
from ..models.transaction import Transaction, TransactionOperationType
from ..repositories.position_repository import PositionRepository
from ..repositories.transaction_repository import TransactionRepository
from .position_handlers import (
    CustodyTransferHandler,
    IgnoredTransactionHandler,
    PositionAccumulator,
    PositionTransactionHandler,
    PurchaseHandler,
    SaleHandler,
    SettlementTransferHandler,
)


POSITION_HANDLERS: dict[TransactionOperationType, PositionTransactionHandler] = {
    TransactionOperationType.PURCHASE: PurchaseHandler(),
    TransactionOperationType.SALE: SaleHandler(),
    TransactionOperationType.SETTLEMENT_TRANSFER: SettlementTransferHandler(),
    TransactionOperationType.TRANSFER: CustodyTransferHandler(),
    TransactionOperationType.DIVIDEND: IgnoredTransactionHandler(),
    TransactionOperationType.INTEREST_ON_EQUITY: IgnoredTransactionHandler(),
    TransactionOperationType.INCOME: IgnoredTransactionHandler(),
}


def build_positions(transactions: Iterable[Transaction]) -> list[Position]:
    """Build one consolidated position per asset."""
    accumulators: dict[str, PositionAccumulator] = {}

    for transaction in transactions:
        try:
            handler = POSITION_HANDLERS[transaction.operation_type]
        except KeyError as exc:
            raise ValueError(
                f"No position handler for operation type "
                f"{transaction.operation_type.value!r}"
            ) from exc

        if isinstance(handler, (CustodyTransferHandler, IgnoredTransactionHandler)):
            continue

        position = accumulators.setdefault(
            transaction.asset_id,
            PositionAccumulator(asset_id=transaction.asset_id),
        )
        handler.apply(position, transaction)

    return [
        accumulator.to_position()
        for _, accumulator in sorted(accumulators.items())
    ]


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
        return self.build_and_save()


def build_and_save_positions(
    transaction_repository: TransactionRepository | None = None,
    position_repository: PositionRepository | None = None,
) -> list[Position]:
    return PositionBuildService(transaction_repository, position_repository).save()
