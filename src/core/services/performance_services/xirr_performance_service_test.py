from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from ...models.portfolio_value import PortfolioValue
from ...models.transaction import IOFlow, Transaction, TransactionOperationType
from .xirr_performance_service import XirrPerformanceService


class StubTransactionRepository:
    def __init__(self, transactions: list[Transaction]) -> None:
        self.transactions = transactions

    def all(self) -> list[Transaction]:
        return self.transactions


class StubPortfolioService:
    def __init__(self, values: dict[date, Decimal]) -> None:
        self.values = values

    def get_value(self, price_date: date, reference_date: date | None = None) -> PortfolioValue:
        return PortfolioValue(price_date, self.values[price_date])


def transaction(
    transaction_date: date,
    value: str,
    io_flow: IOFlow = IOFlow.INFLOW,
) -> Transaction:
    return Transaction(
        transaction_id=transaction_date.isoformat(),
        io_flow=io_flow,
        date=transaction_date,
        operation_type=TransactionOperationType.PURCHASE,
        asset_id="asset_001",
        holding_id="holding_001",
        quantity=Decimal("1"),
        unit_price=Decimal(value),
        operation_value=Decimal(value),
    )


class XirrPerformanceServiceTests(unittest.TestCase):
    def test_defaults_to_first_transaction_and_latest_transaction_date(self) -> None:
        transactions = [
            transaction(date(2024, 1, 1), "100"),
            transaction(date(2025, 1, 1), "0", IOFlow.OUTFLOW),
        ]
        portfolio_service = StubPortfolioService({
            date(2023, 12, 31): Decimal("0"),
            date(2025, 1, 1): Decimal("110"),
        })

        result = XirrPerformanceService(
            portfolio_service=portfolio_service,
            transaction_repository=StubTransactionRepository(transactions),
        ).calculate()

        self.assertEqual(result.start_date, date(2024, 1, 1))
        self.assertEqual(result.end_date, date(2025, 1, 1))
        self.assertEqual(result.cash_flows[0], (date(2024, 1, 1), Decimal("-100")))
        self.assertAlmostEqual(result.xirr, 1.1 ** (365 / 366) - 1, places=6)

    def test_explicit_start_value_is_a_negative_cash_flow(self) -> None:
        transactions = [transaction(date(2024, 6, 1), "20")]
        portfolio_service = StubPortfolioService({
            date(2024, 1, 1): Decimal("100"),
            date(2024, 12, 31): Decimal("132"),
        })

        result = XirrPerformanceService(
            portfolio_service=portfolio_service,
            transaction_repository=StubTransactionRepository(transactions),
        ).calculate(date(2024, 1, 2), date(2024, 12, 31))

        self.assertEqual(result.cash_flows[0], (date(2024, 1, 2), Decimal("-100")))
        self.assertEqual(result.cash_flows[-1], (date(2024, 12, 31), Decimal("132")))
        self.assertGreater(result.xirr, 0)


if __name__ == "__main__":
    unittest.main()
