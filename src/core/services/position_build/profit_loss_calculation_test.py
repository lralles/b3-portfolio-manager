from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from src.core.models.profit_loss import ProfitLoss, ProfitLossType
from src.core.models.transaction import IOFlow, Transaction, TransactionOperationType
from src.core.services.position_build.handlers import PositionAccumulator
from src.core.services.position_build.profit_loss_calculation import (
    calculate_profit_loss,
)


def transaction(
    operation_type: TransactionOperationType,
    *,
    transaction_id: str = "transaction_001",
    quantity: str | None = "2",
    operation_value: str | None = "30",
) -> Transaction:
    return Transaction(
        transaction_id=transaction_id,
        io_flow=IOFlow.OUTFLOW,
        date=date(2020, 1, 1),
        operation_type=operation_type,
        asset_id="asset_001",
        holding_id="holding_001",
        quantity=Decimal(quantity) if quantity is not None else None,
        unit_price=None,
        operation_value=(Decimal(operation_value) if operation_value is not None else None),
    )


class ProfitLossCalculationTests(unittest.TestCase):
    def test_sale_uses_position_weighted_acquisition_cost(self) -> None:
        position = PositionAccumulator(
            asset_id="asset_001",
            total_acquired_quantity=Decimal("5"),
            invested_capital=Decimal("65"),
        )

        result = calculate_profit_loss(
            transaction(TransactionOperationType.SALE), position
        )

        self.assertEqual(
            result,
            ProfitLoss(
                "asset_001",
                "transaction_001",
                "holding_001",
                Decimal("4"),
                ProfitLossType.REALIZED,
            ),
        )

    def test_sale_can_produce_a_negative_value(self) -> None:
        position = PositionAccumulator(
            asset_id="asset_001",
            total_acquired_quantity=Decimal("5"),
            invested_capital=Decimal("65"),
        )

        result = calculate_profit_loss(
            transaction(TransactionOperationType.SALE, operation_value="20"), position
        )

        self.assertEqual(result.value, Decimal("-6"))

    def test_income_operations_use_transaction_operation_value(self) -> None:
        for operation_type in (
            TransactionOperationType.DIVIDEND,
            TransactionOperationType.INTEREST_ON_EQUITY,
            TransactionOperationType.INCOME,
        ):
            with self.subTest(operation_type=operation_type):
                result = calculate_profit_loss(
                    transaction(operation_type, operation_value="12.50")
                )

                self.assertEqual(result.value, Decimal("12.50"))
                self.assertEqual(result.type, ProfitLossType.REALIZED)

    def test_purchase_and_transfer_do_not_create_profit_loss(self) -> None:
        self.assertIsNone(
            calculate_profit_loss(transaction(TransactionOperationType.PURCHASE))
        )
        self.assertIsNone(
            calculate_profit_loss(transaction(TransactionOperationType.TRANSFER))
        )

    def test_sale_requires_position(self) -> None:
        with self.assertRaisesRegex(ValueError, "position is required"):
            calculate_profit_loss(transaction(TransactionOperationType.SALE))


if __name__ == "__main__":
    unittest.main()
