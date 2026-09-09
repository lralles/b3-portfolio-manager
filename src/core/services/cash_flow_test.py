from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from src.core.models.transaction import IOFlow, Transaction, TransactionOperationType
from src.core.services.cash_flow import MonthlyCashFlow, calculate_monthly_cash_flow, next_month


def transaction(
    transaction_date: date,
    *,
    io_flow: IOFlow,
    operation_value: str | None,
) -> Transaction:
    return Transaction(
        io_flow=io_flow,
        date=transaction_date,
        operation_type=TransactionOperationType.PURCHASE,
        asset_id="asset_001",
        holding_id="holding_001",
        quantity=None,
        unit_price=None,
        operation_value=(
            Decimal(operation_value) if operation_value is not None else None
        ),
    )


class CashFlowTests(unittest.TestCase):
    def test_empty_transactions_return_no_months(self) -> None:
        self.assertEqual(calculate_monthly_cash_flow([]), [])

    def test_groups_transactions_and_calculates_net(self) -> None:
        result = calculate_monthly_cash_flow([
            transaction(date(2020, 1, 3), io_flow=IOFlow.INFLOW, operation_value="100.50"),
            transaction(date(2020, 1, 20), io_flow=IOFlow.OUTFLOW, operation_value="40.25"),
            transaction(date(2020, 2, 1), io_flow=IOFlow.INFLOW, operation_value="10"),
        ])

        self.assertEqual(result, [
            MonthlyCashFlow(
                date(2020, 1, 1), Decimal("100.50"), Decimal("40.25"), Decimal("60.25"), 2
            ),
            MonthlyCashFlow(
                date(2020, 2, 1), Decimal("10"), Decimal("0"), Decimal("10"), 1
            ),
        ])

    def test_includes_zero_months_between_transactions(self) -> None:
        result = calculate_monthly_cash_flow([
            transaction(date(2020, 1, 31), io_flow=IOFlow.INFLOW, operation_value="10"),
            transaction(date(2020, 3, 1), io_flow=IOFlow.OUTFLOW, operation_value="5"),
        ])

        self.assertEqual([flow.month for flow in result], [
            date(2020, 1, 1), date(2020, 2, 1), date(2020, 3, 1)
        ])
        self.assertEqual(result[1], MonthlyCashFlow(
            date(2020, 2, 1), Decimal("0"), Decimal("0"), Decimal("0"), 0
        ))

    def test_missing_operation_value_counts_transaction_but_not_amount(self) -> None:
        result = calculate_monthly_cash_flow([
            transaction(date(2020, 1, 1), io_flow=IOFlow.INFLOW, operation_value=None),
        ])

        self.assertEqual(result, [
            MonthlyCashFlow(date(2020, 1, 1), Decimal("0"), Decimal("0"), Decimal("0"), 1)
        ])

    def test_next_month_rolls_over_year(self) -> None:
        self.assertEqual(next_month(date(2020, 12, 1)), date(2021, 1, 1))


if __name__ == "__main__":
    unittest.main()
