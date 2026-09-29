from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from ...models.position import Position
from ...models.profit_loss import ProfitLoss
from ...models.transaction import IOFlow, Transaction, TransactionOperationType
from .handlers import (
    CustodyTransferHandler,
    CorporateActionHandler,
    FractionAuctionHandler,
    IgnoredTransactionHandler,
    PositionAccumulator,
    PositionTransactionHandler,
    PurchaseHandler,
    QuantityDecreaseHandler,
    QuantityIncreaseHandler,
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
    TransactionOperationType.INCORPORATION: CorporateActionHandler(),
    TransactionOperationType.REDEMPTION: CorporateActionHandler(),
    TransactionOperationType.FRACTION_SETTLEMENT: CorporateActionHandler(),
    TransactionOperationType.ASSET_BONUS: QuantityIncreaseHandler(),
    TransactionOperationType.ASSET_SPLIT: QuantityIncreaseHandler(),
    TransactionOperationType.SUBSCRIPTION_RIGHT_GRANT: QuantityIncreaseHandler(),
    TransactionOperationType.SUBSCRIPTION_RIGHT_EXPIRY: QuantityDecreaseHandler(),
    TransactionOperationType.SUBSCRIPTION_RIGHT_DISPOSAL: QuantityDecreaseHandler(),
    TransactionOperationType.RIGHTS_TRANSFER: CustodyTransferHandler(),
    TransactionOperationType.FRACTION_AUCTION: FractionAuctionHandler(),
    TransactionOperationType.CASH_EVENT_TRANSFER: CustodyTransferHandler(),
}


def build_positions(
    transactions: Iterable[Transaction],
) -> tuple[list[Position], list[ProfitLoss]]:
    """Build consolidated positions and realized profit/loss from transactions."""
    accumulators: dict[str, PositionAccumulator] = {}
    profit_losses: list[ProfitLoss] = []
    corporate_action_basis: dict[str, Decimal] = {}

    ordered_transactions = sorted(transactions, key=lambda transaction: transaction.date)
    for transaction in ordered_transactions:
        try:
            handler = POSITION_HANDLERS[transaction.operation_type]
        except KeyError as exc:
            raise ValueError(
                f"No position handler for operation type "
                f"{transaction.operation_type.value!r}"
            ) from exc

        position = accumulators.get(transaction.asset_id)
        if transaction.operation_type in (
            TransactionOperationType.SALE,
            TransactionOperationType.INCORPORATION,
        ) and transaction.io_flow is IOFlow.OUTFLOW:
            position = accumulators.setdefault(
                transaction.asset_id,
                PositionAccumulator(asset_id=transaction.asset_id),
            )

        profit_loss = calculate_profit_loss(transaction, position)
        if profit_loss is not None:
            profit_losses.append(profit_loss)

        if transaction.operation_type is TransactionOperationType.INCORPORATION:
            if not transaction.corporate_action_id:
                raise ValueError(
                    "Incorporation transaction is missing corporate_action_id"
                )
            quantity = transaction.quantity or Decimal("0")
            if transaction.io_flow is IOFlow.OUTFLOW:
                if position is None:
                    raise ValueError(
                        f"No source position for incorporation {transaction.transaction_id!r}"
                    )
                corporate_action_basis[transaction.corporate_action_id] = (
                    position.invested_capital
                )
                position.current_quantity -= quantity
                position.invested_capital = 0
            else:
                position = accumulators.setdefault(
                    transaction.asset_id,
                    PositionAccumulator(asset_id=transaction.asset_id),
                )
                position.current_quantity += quantity
                position.invested_capital += corporate_action_basis.get(
                    transaction.corporate_action_id, Decimal("0")
                )
            continue

        if transaction.operation_type is TransactionOperationType.REDEMPTION:
            if transaction.corporate_action_related_asset_id:
                related_position = accumulators.get(
                    transaction.corporate_action_related_asset_id
                )
                if related_position is not None:
                    related_position.invested_capital -= (
                        transaction.operation_value or Decimal("0")
                    )
            elif position is not None:
                position.current_quantity -= transaction.quantity or Decimal("0")
            continue

        if transaction.operation_type is TransactionOperationType.FRACTION_SETTLEMENT:
            if position is not None:
                fraction = position.current_quantity % 1
                position.current_quantity -= fraction
            continue

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
