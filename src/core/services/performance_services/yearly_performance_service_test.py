from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from ...models.portfolio_value import PortfolioValue
from ...models.transaction import IOFlow, Transaction, TransactionOperationType
from .yearly_performance_service import YearlyPerformanceService


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


class YearlyPerformanceServiceTests(unittest.TestCase):
    def test_uses_year_ends_and_aggregates_io_for_the_year(self) -> None:
        transactions = [
            transaction(date(2023, 2, 15), "100"),
            transaction(date(2024, 2, 15), "20"),
            transaction(date(2024, 8, 15), "30"),
        ]
        portfolio_service = StubPortfolioService({
            date(2023, 12, 31): Decimal("100"),
            date(2024, 12, 31): Decimal("160"),
        })

        result = YearlyPerformanceService(
            portfolio_service=portfolio_service,
            transaction_repository=StubTransactionRepository(transactions),
        ).calculate()

        self.assertEqual(
            portfolio_service.calls,
            [
                (date(2023, 12, 31), date(2023, 12, 31)),
                (date(2024, 12, 31), date(2024, 12, 31)),
            ],
        )
        self.assertEqual(result[0].year, date(2024, 1, 1))
        self.assertEqual(result[0].net_io, Decimal("50"))
        self.assertEqual(result[0].performance, Decimal("0.1"))

    def test_empty_transactions_have_no_yearly_performance(self) -> None:
        result = YearlyPerformanceService(
            portfolio_service=StubPortfolioService({}),
            transaction_repository=StubTransactionRepository([]),
        ).calculate()

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
