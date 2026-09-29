from __future__ import annotations

from decimal import Decimal

from ...models.profit_loss import ProfitLoss, ProfitLossType
from ...models.transaction import Transaction, TransactionOperationType
from .handlers import PositionAccumulator


INCOME_OPERATION_TYPES = {
    TransactionOperationType.DIVIDEND,
    TransactionOperationType.INTEREST_ON_EQUITY,
    TransactionOperationType.INCOME,
}


def calculate_profit_loss(
    transaction: Transaction,
    position: PositionAccumulator | None = None,
) -> ProfitLoss | None:
    """Create realized profit/loss for a transaction, when applicable.

    Sales require the position state before the sale is applied so their
    acquisition cost can be calculated using the current weighted average.
    """
    if transaction.operation_type in INCOME_OPERATION_TYPES:
        return ProfitLoss(
            asset_id=transaction.asset_id,
            transaction_id=transaction.transaction_id,
            holding_id=transaction.holding_id,
            value=transaction.operation_value or Decimal("0"),
            type=ProfitLossType.REALIZED,
        )

    if transaction.operation_type is TransactionOperationType.REDEMPTION:
        if transaction.corporate_action_related_asset_id:
            return None
    elif transaction.operation_type is not TransactionOperationType.SALE:
        return None

    if position is None:
        raise ValueError("A position is required to calculate sale profit/loss")

    acquisition_cost = Decimal("0")
    if position.total_acquired_quantity:
        acquisition_cost = (
            position.invested_capital
            / position.total_acquired_quantity
            * (transaction.quantity or Decimal("0"))
        )

    return ProfitLoss(
        asset_id=transaction.asset_id,
        transaction_id=transaction.transaction_id,
        holding_id=transaction.holding_id,
        value=(transaction.operation_value or Decimal("0")) - acquisition_cost,
        type=ProfitLossType.REALIZED,
    )
