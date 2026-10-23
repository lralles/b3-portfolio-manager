from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from ...models.portfolio_value import PortfolioValue
from ...models.transaction import IOFlow, Transaction, TransactionOperationType
from .running_performance_service import RunningPerformanceService


class StubTransactionRepository:
    def __init__(self, transactions: list[Transaction]) -> None:
        self.transactions = transactions

    def all(self) -> list[Transaction]:
        return self.transactions


class StubPortfolioService:
    def __init__(self, values: list[PortfolioValue]) -> None:
        self.values = values

    def get_over_time(self) -> list[PortfolioValue]:
        return self.values


def transaction(
    transaction_date: date,
    value: str,
    operation_type: TransactionOperationType = TransactionOperationType.PURCHASE,
    io_flow: IOFlow = IOFlow.INFLOW,
) -> Transaction:
    return Transaction(
        transaction_id=f"{transaction_date.isoformat()}-{value}-{operation_type}",
        io_flow=io_flow,
        date=transaction_date,
        operation_type=operation_type,
        asset_id="asset_001",
        holding_id="holding_001",
        quantity=Decimal("1"),
        unit_price=Decimal(value),
        operation_value=Decimal(value),
    )


class RunningPerformanceServiceTests(unittest.TestCase):
    def test_adjusts_each_interval_for_io_and_compounds_running_performance(self) -> None:
        transactions = [
            transaction(date(2024, 1, 1), "100"),
            transaction(date(2024, 1, 2), "20"),
        ]
        portfolio_service = StubPortfolioService([
            PortfolioValue(date(2024, 1, 1), Decimal("100")),
            PortfolioValue(date(2024, 1, 2), Decimal("130")),
            PortfolioValue(date(2024, 1, 3), Decimal("143")),
        ])

        result = RunningPerformanceService(
            portfolio_service=portfolio_service,
            transaction_repository=StubTransactionRepository(transactions),
        ).calculate()

        self.assertEqual(result[0].previous_date, date(2024, 1, 1))
        self.assertEqual(result[0].date, date(2024, 1, 2))
        self.assertEqual(result[0].net_io, Decimal("20"))
        self.assertEqual(result[0].period_performance, Decimal("0.1"))
        self.assertEqual(result[0].performance, Decimal("0.1"))
        self.assertEqual(result[1].period_performance, Decimal("0.1"))
        self.assertEqual(result[1].performance, Decimal("0.21"))

    def test_uses_same_io_classification_as_monthly_cash_flow(self) -> None:
        transactions = [
            transaction(date(2024, 1, 1), "100"),
            transaction(date(2024, 1, 2), "20"),
            transaction(
                date(2024, 1, 2),
                "5",
                TransactionOperationType.DIVIDEND,
            ),
        ]
        portfolio_service = StubPortfolioService([
            PortfolioValue(date(2024, 1, 1), Decimal("100")),
            PortfolioValue(date(2024, 1, 2), Decimal("125")),
        ])

        result = RunningPerformanceService(
            portfolio_service=portfolio_service,
            transaction_repository=StubTransactionRepository(transactions),
        ).calculate()

        self.assertEqual(result[0].inflow, Decimal("20"))
        self.assertEqual(result[0].outflow, Decimal("5"))
        self.assertEqual(result[0].net_io, Decimal("15"))
        self.assertEqual(result[0].performance, Decimal("0.1"))

    def test_zero_starting_value_has_no_period_or_running_performance(self) -> None:
        transactions = [transaction(date(2024, 1, 1), "100")]
        portfolio_service = StubPortfolioService([
            PortfolioValue(date(2024, 1, 1), Decimal("0")),
            PortfolioValue(date(2024, 1, 2), Decimal("100")),
            PortfolioValue(date(2024, 1, 3), Decimal("110")),
        ])

        result = RunningPerformanceService(
            portfolio_service=portfolio_service,
            transaction_repository=StubTransactionRepository(transactions),
        ).calculate()

        self.assertIsNone(result[0].period_performance)
        self.assertIsNone(result[0].performance)
        self.assertEqual(result[1].period_performance, Decimal("0.1"))
        self.assertEqual(result[1].performance, Decimal("0.1"))

    def test_empty_or_single_point_history_has_no_running_performance(self) -> None:
        repository = StubTransactionRepository([])
        self.assertEqual(
            RunningPerformanceService(
                portfolio_service=StubPortfolioService([]),
                transaction_repository=repository,
            ).calculate(),
            [],
        )
        self.assertEqual(
            RunningPerformanceService(
                portfolio_service=StubPortfolioService([
                    PortfolioValue(date(2024, 1, 1), Decimal("100")),
                ]),
                transaction_repository=repository,
            ).calculate(),
            [],
        )


if __name__ == "__main__":
    unittest.main()
