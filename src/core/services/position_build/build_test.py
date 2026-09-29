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
    transaction_date: date = date(2020, 1, 1),
    quantity: str | None = "1",
    operation_value: str | None = "100",
) -> Transaction:
    return Transaction(
        transaction_id=transaction_id,
        io_flow=io_flow,
        date=transaction_date,
        operation_type=operation_type,
        asset_id="asset_001",
        holding_id=holding_id,
        quantity=Decimal(quantity) if quantity is not None else None,
        unit_price=None,
        operation_value=(Decimal(operation_value) if operation_value is not None else None),
    )


class BuildPositionsTests(unittest.TestCase):
    def test_incorporation_transfers_basis_and_redemption_reduces_it(self) -> None:
        source = Transaction(
            transaction_id="purchase_hgtx",
            io_flow=IOFlow.INFLOW,
            date=date(2021, 1, 13),
            operation_type=TransactionOperationType.PURCHASE,
            asset_id="hgtx",
            holding_id="holding_001",
            quantity=Decimal("4"),
            unit_price=Decimal("15.86"),
            operation_value=Decimal("63.44"),
        )
        incorporation_out = Transaction(
            transaction_id="incorporation_out",
            io_flow=IOFlow.OUTFLOW,
            date=date(2021, 9, 21),
            operation_type=TransactionOperationType.INCORPORATION,
            asset_id="hgtx",
            holding_id="holding_001",
            quantity=Decimal("4"),
            unit_price=None,
            operation_value=None,
            corporate_action_id="hgtx_to_soma",
            corporate_action_related_asset_id="soma",
        )
        incorporation_in = Transaction(
            transaction_id="incorporation_in",
            io_flow=IOFlow.INFLOW,
            date=date(2021, 9, 21),
            operation_type=TransactionOperationType.INCORPORATION,
            asset_id="soma",
            holding_id="holding_001",
            quantity=Decimal("6.5"),
            unit_price=None,
            operation_value=None,
            corporate_action_id="hgtx_to_soma",
            corporate_action_related_asset_id="hgtx",
        )
        redemption = Transaction(
            transaction_id="redemption_cmrv",
            io_flow=IOFlow.INFLOW,
            date=date(2021, 9, 24),
            operation_type=TransactionOperationType.REDEMPTION,
            asset_id="cmrv11",
            holding_id="holding_001",
            quantity=None,
            unit_price=None,
            operation_value=Decimal("38.15"),
            corporate_action_id="hgtx_to_soma",
            corporate_action_related_asset_id="soma",
        )
        fraction = Transaction(
            transaction_id="fraction_soma",
            io_flow=IOFlow.OUTFLOW,
            date=date(2021, 10, 4),
            operation_type=TransactionOperationType.FRACTION_SETTLEMENT,
            asset_id="soma",
            holding_id="holding_001",
            quantity=None,
            unit_price=None,
            operation_value=None,
            corporate_action_id="hgtx_to_soma",
        )

        positions, profit_losses = build_positions(
            [source, incorporation_out, incorporation_in, redemption, fraction]
        )

        by_asset = {position.asset_id: position for position in positions}
        self.assertEqual(by_asset["hgtx"].current_quantity, Decimal("0"))
        self.assertEqual(by_asset["hgtx"].invested_capital, Decimal("0"))
        self.assertEqual(by_asset["soma"].current_quantity, Decimal("6"))
        self.assertEqual(by_asset["soma"].invested_capital, Decimal("25.29"))
        self.assertNotIn("cmrv11", by_asset)
        self.assertEqual(profit_losses, [])

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

    def test_transactions_are_processed_chronologically(self) -> None:
        positions, profit_losses = build_positions([
            transaction(
                TransactionOperationType.SALE,
                transaction_id="transaction_002",
                transaction_date=date(2020, 8, 3),
                quantity="2",
                operation_value="30",
            ),
            transaction(
                TransactionOperationType.PURCHASE,
                transaction_date=date(2020, 7, 23),
                quantity="2",
                operation_value="26",
            ),
        ])

        self.assertEqual(positions[0].current_quantity, Decimal("0"))
        self.assertEqual(profit_losses[0].value, Decimal("4"))

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
