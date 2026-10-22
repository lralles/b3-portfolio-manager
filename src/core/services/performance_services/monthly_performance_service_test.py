from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from ...models.portfolio_value import PortfolioValue
from ...models.transaction import IOFlow, Transaction, TransactionOperationType
from .monthly_performance_service import MonthlyPerformanceService


class StubTransactionRepository:
    def __init__(self, transactions: list[Transaction]) -> None:
        self.transactions = transactions

    def all(self) -> list[Transaction]:
        return self.transactions


class StubPortfolioService:
    def __init__(self, values: dict[date, Decimal]) -> None:
        self.values = values
        self.calls: list[tuple[date, date]] = []

    def get_value(self, price_date: date, reference_date: date | None = None) -> PortfolioValue:
        assert reference_date is not None
        self.calls.append((price_date, reference_date))
        return PortfolioValue(price_date, self.values[price_date])


def transaction(transaction_date: date, value: str) -> Transaction:
    return Transaction(
        transaction_id=transaction_date.isoformat(),
        io_flow=IOFlow.INFLOW,
        date=transaction_date,
        operation_type=TransactionOperationType.PURCHASE,
        asset_id="asset_001",
        holding_id="holding_001",
        quantity=Decimal("1"),
        unit_price=Decimal(value),
        operation_value=Decimal(value),
    )


class MonthlyPerformanceServiceTests(unittest.TestCase):
    def test_uses_calendar_month_ends_and_adjusts_for_next_month_io(self) -> None:
        transactions = [
            transaction(date(2024, 1, 15), "100"),
            transaction(date(2024, 2, 15), "20"),
            transaction(date(2024, 3, 15), "100"),
        ]
        portfolio_service = StubPortfolioService({
            date(2024, 1, 31): Decimal("100"),
            date(2024, 2, 29): Decimal("130"),
            date(2024, 3, 31): Decimal("140"),
        })

        result = MonthlyPerformanceService(
            portfolio_service=portfolio_service,
            transaction_repository=StubTransactionRepository(transactions),
        ).calculate()

        self.assertEqual(
            portfolio_service.calls,
            [
                (date(2024, 1, 31), date(2024, 1, 31)),
                (date(2024, 2, 29), date(2024, 2, 29)),
                (date(2024, 3, 31), date(2024, 3, 31)),
            ],
        )
        self.assertEqual(result[0].month, date(2024, 2, 1))
        self.assertEqual(result[0].net_io, Decimal("20"))
        self.assertEqual(result[0].performance, Decimal("0.1"))

    def test_zero_starting_value_has_no_performance(self) -> None:
        transactions = [
            transaction(date(2024, 1, 15), "100"),
            transaction(date(2024, 2, 15), "100"),
        ]
        portfolio_service = StubPortfolioService({
            date(2024, 1, 31): Decimal("0"),
            date(2024, 2, 29): Decimal("100"),
        })

        result = MonthlyPerformanceService(
            portfolio_service=portfolio_service,
            transaction_repository=StubTransactionRepository(transactions),
        ).calculate()

        self.assertIsNone(result[0].performance)

    def test_month_without_transactions_has_zero_io(self) -> None:
        transactions = [
            transaction(date(2024, 1, 15), "100"),
            transaction(date(2024, 3, 15), "100"),
        ]
        portfolio_service = StubPortfolioService({
            date(2024, 1, 31): Decimal("100"),
            date(2024, 2, 29): Decimal("110"),
            date(2024, 3, 31): Decimal("120"),
        })

        result = MonthlyPerformanceService(
            portfolio_service=portfolio_service,
            transaction_repository=StubTransactionRepository(transactions),
        ).calculate()

        self.assertEqual(result[0].net_io, Decimal("0"))
        self.assertEqual(result[0].performance, Decimal("0.1"))

    def test_empty_transactions_have_no_monthly_performance(self) -> None:
        result = MonthlyPerformanceService(
            portfolio_service=StubPortfolioService({}),
            transaction_repository=StubTransactionRepository([]),
        ).calculate()

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
