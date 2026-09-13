from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from src.core.models.position import Position
from src.core.models.profit_loss import ProfitLoss, ProfitLossType
from src.core.models.transaction import IOFlow, Transaction, TransactionOperationType
from src.core.services.position_build import build_positions


def transaction(
    operation_type: TransactionOperationType,
    *,
    io_flow: IOFlow = IOFlow.INFLOW,
    holding_id: str = "holding_001",
    transaction_id: str = "transaction_001",
    quantity: str | None = "1",
    operation_value: str | None = "100",
) -> Transaction:
    return Transaction(
        transaction_id=transaction_id,
        io_flow=io_flow,
        date=date(2020, 1, 1),
        operation_type=operation_type,
        asset_id="asset_001",
        holding_id=holding_id,
        quantity=Decimal(quantity) if quantity is not None else None,
        unit_price=None,
        operation_value=(Decimal(operation_value) if operation_value is not None else None),
    )


class BuildPositionsTests(unittest.TestCase):
    def test_purchase_accumulates_quantity_and_capital(self) -> None:
        positions, profit_losses = build_positions([
            transaction(TransactionOperationType.PURCHASE, quantity="2", operation_value="20"),
            transaction(TransactionOperationType.PURCHASE, quantity="3", operation_value="45"),
        ])

        self.assertEqual(
            positions,
            [Position("asset_001", Decimal("5"), Decimal("5"), Decimal("0"), Decimal("65"))],
        )
        self.assertEqual(profit_losses, [])

    def test_sale_reduces_current_quantity_and_preserves_invested_capital(self) -> None:
        positions, profit_losses = build_positions([
            transaction(TransactionOperationType.PURCHASE, quantity="5", operation_value="65"),
            transaction(
                TransactionOperationType.SALE,
                io_flow=IOFlow.OUTFLOW,
                transaction_id="transaction_002",
                quantity="2",
                operation_value="30",
            ),
        ])

        self.assertEqual(positions[0].current_quantity, Decimal("3"))
        self.assertEqual(positions[0].total_acquired_quantity, Decimal("5"))
        self.assertEqual(positions[0].total_sold_quantity, Decimal("2"))
        self.assertEqual(positions[0].invested_capital, Decimal("65"))
        self.assertEqual(
            profit_losses,
            [
                ProfitLoss(
                    "asset_001",
                    "transaction_002",
                    "holding_001",
                    Decimal("4"),
                    ProfitLossType.REALIZED,
                )
            ],
        )

    def test_custody_transfers_are_globally_neutral(self) -> None:
        positions, profit_losses = build_positions([
            transaction(
                TransactionOperationType.TRANSFER,
                io_flow=IOFlow.OUTFLOW,
                quantity="2",
                operation_value=None,
            ),
            transaction(
                TransactionOperationType.TRANSFER,
                io_flow=IOFlow.INFLOW,
                holding_id="holding_002",
                quantity="2",
                operation_value=None,
            ),
        ])

        self.assertEqual(positions, [])
        self.assertEqual(profit_losses, [])

    def test_holdings_are_aggregated_by_asset(self) -> None:
        positions, profit_losses = build_positions([
            transaction(
                TransactionOperationType.PURCHASE,
                holding_id="holding_001",
                quantity="2",
                operation_value="20",
            ),
            transaction(
                TransactionOperationType.PURCHASE,
                holding_id="holding_002",
                quantity="3",
                operation_value="45",
            ),
        ])

        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0].current_quantity, Decimal("5"))
        self.assertEqual(positions[0].invested_capital, Decimal("65"))
        self.assertEqual(profit_losses, [])

    def test_non_position_operations_are_ignored(self) -> None:
        positions, profit_losses = build_positions([
            transaction(TransactionOperationType.DIVIDEND, transaction_id="transaction_002"),
            transaction(TransactionOperationType.INTEREST_ON_EQUITY, transaction_id="transaction_003"),
            transaction(TransactionOperationType.INCOME, transaction_id="transaction_004"),
            transaction(TransactionOperationType.TRANSFER),
        ])

        self.assertEqual(positions, [])
        self.assertEqual(
            profit_losses,
            [
                ProfitLoss(
                    "asset_001", "transaction_002", "holding_001", Decimal("100"), ProfitLossType.REALIZED
                ),
                ProfitLoss(
                    "asset_001", "transaction_003", "holding_001", Decimal("100"), ProfitLossType.REALIZED
                ),
                ProfitLoss(
                    "asset_001", "transaction_004", "holding_001", Decimal("100"), ProfitLossType.REALIZED
                ),
            ],
        )

    def test_zero_current_quantity_retains_history(self) -> None:
        positions, _ = build_positions([
            transaction(TransactionOperationType.PURCHASE, quantity="2", operation_value="20"),
            transaction(
                TransactionOperationType.SALE,
                io_flow=IOFlow.OUTFLOW,
                quantity="2",
                operation_value="25",
            ),
        ])

        self.assertEqual(positions[0].current_quantity, Decimal("0"))
        self.assertEqual(positions[0].total_acquired_quantity, Decimal("2"))
        self.assertEqual(positions[0].total_sold_quantity, Decimal("2"))
        self.assertEqual(positions[0].invested_capital, Decimal("20"))


if __name__ == "__main__":
    unittest.main()
