from __future__ import annotations

from typing import Iterable

from ...models.position import Position
from ...models.profit_loss import ProfitLoss
from ...models.transaction import Transaction, TransactionOperationType
from .handlers import (
    CustodyTransferHandler,
    IgnoredTransactionHandler,
    PositionAccumulator,
    PositionTransactionHandler,
    PurchaseHandler,
    SaleHandler,
)
from .profit_loss_calculation import calculate_profit_loss


POSITION_HANDLERS: dict[TransactionOperationType, PositionTransactionHandler] = {
    TransactionOperationType.PURCHASE: PurchaseHandler(),
    TransactionOperationType.SALE: SaleHandler(),
    TransactionOperationType.TRANSFER: CustodyTransferHandler(),
    TransactionOperationType.DIVIDEND: IgnoredTransactionHandler(),
    TransactionOperationType.INTEREST_ON_EQUITY: IgnoredTransactionHandler(),
    TransactionOperationType.INCOME: IgnoredTransactionHandler(),
}


def build_positions(
    transactions: Iterable[Transaction],
) -> tuple[list[Position], list[ProfitLoss]]:
    """Build consolidated positions and realized profit/loss from transactions."""
    accumulators: dict[str, PositionAccumulator] = {}
    profit_losses: list[ProfitLoss] = []

    for transaction in transactions:
        try:
            handler = POSITION_HANDLERS[transaction.operation_type]
        except KeyError as exc:
            raise ValueError(
                f"No position handler for operation type "
                f"{transaction.operation_type.value!r}"
            ) from exc

        position = accumulators.get(transaction.asset_id)
        if transaction.operation_type is TransactionOperationType.SALE:
            position = accumulators.setdefault(
                transaction.asset_id,
                PositionAccumulator(asset_id=transaction.asset_id),
            )

        profit_loss = calculate_profit_loss(transaction, position)
        if profit_loss is not None:
            profit_losses.append(profit_loss)

        if isinstance(handler, (CustodyTransferHandler, IgnoredTransactionHandler)):
            continue

        if position is None:
            position = accumulators.setdefault(
                transaction.asset_id,
                PositionAccumulator(asset_id=transaction.asset_id),
            )
        handler.apply(position, transaction)

    positions = [
        accumulator.to_position()
        for _, accumulator in sorted(accumulators.items())
    ]
    return positions, profit_losses
