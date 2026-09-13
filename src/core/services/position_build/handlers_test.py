from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from src.core.models.transaction import IOFlow, Transaction, TransactionOperationType
from src.core.services.position_build.handlers import (
    CustodyTransferHandler,
    IgnoredTransactionHandler,
    PositionAccumulator,
    PurchaseHandler,
    SaleHandler,
)


def transaction(
    operation_type: TransactionOperationType,
    *,
    quantity: str | None = "2",
    operation_value: str | None = "20",
) -> Transaction:
    return Transaction(
        transaction_id="transaction_001",
        io_flow=IOFlow.INFLOW,
        date=date(2020, 1, 1),
        operation_type=operation_type,
        asset_id="asset_001",
        holding_id="holding_001",
        quantity=Decimal(quantity) if quantity is not None else None,
        unit_price=None,
        operation_value=(Decimal(operation_value) if operation_value is not None else None),
    )


class PositionHandlerTests(unittest.TestCase):
    def test_purchase_handler_updates_position_state(self) -> None:
        position = PositionAccumulator("asset_001")

        PurchaseHandler().apply(position, transaction(TransactionOperationType.PURCHASE))

        self.assertEqual(position.current_quantity, Decimal("2"))
        self.assertEqual(position.total_acquired_quantity, Decimal("2"))
        self.assertEqual(position.invested_capital, Decimal("20"))

    def test_sale_handler_updates_quantity_and_sold_total(self) -> None:
        position = PositionAccumulator(
            "asset_001",
            current_quantity=Decimal("5"),
            total_acquired_quantity=Decimal("5"),
            invested_capital=Decimal("50"),
        )

        SaleHandler().apply(
            position,
            transaction(TransactionOperationType.SALE, quantity="2", operation_value="30"),
        )

        self.assertEqual(position.current_quantity, Decimal("3"))
        self.assertEqual(position.total_sold_quantity, Decimal("2"))
        self.assertEqual(position.invested_capital, Decimal("50"))

    def test_custody_transfer_handler_is_no_op(self) -> None:
        position = PositionAccumulator("asset_001", current_quantity=Decimal("5"))

        CustodyTransferHandler().apply(
            position,
            transaction(TransactionOperationType.TRANSFER),
        )

        self.assertEqual(position.current_quantity, Decimal("5"))

    def test_ignored_handler_is_no_op(self) -> None:
        position = PositionAccumulator("asset_001", current_quantity=Decimal("5"))

        IgnoredTransactionHandler().apply(
            position,
            transaction(TransactionOperationType.DIVIDEND),
        )

        self.assertEqual(position.current_quantity, Decimal("5"))


if __name__ == "__main__":
    unittest.main()
