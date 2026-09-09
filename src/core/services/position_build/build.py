from __future__ import annotations

from typing import Iterable

from ...models.position import Position
from ...models.transaction import Transaction, TransactionOperationType
from .handlers import (
    CustodyTransferHandler,
    IgnoredTransactionHandler,
    PositionAccumulator,
    PositionTransactionHandler,
    PurchaseHandler,
    SaleHandler,
)


POSITION_HANDLERS: dict[TransactionOperationType, PositionTransactionHandler] = {
    TransactionOperationType.PURCHASE: PurchaseHandler(),
    TransactionOperationType.SALE: SaleHandler(),
    TransactionOperationType.TRANSFER: CustodyTransferHandler(),
    TransactionOperationType.DIVIDEND: IgnoredTransactionHandler(),
    TransactionOperationType.INTEREST_ON_EQUITY: IgnoredTransactionHandler(),
    TransactionOperationType.INCOME: IgnoredTransactionHandler(),
}


def build_positions(transactions: Iterable[Transaction]) -> list[Position]:
    """Build one consolidated position per asset from transactions."""
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
