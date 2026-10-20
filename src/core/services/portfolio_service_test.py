from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from src.core.models.asset import Asset
from src.core.models.portfolio import Portfolio
from src.core.models.portfolio_value import PortfolioValue
from src.core.models.position import Position
from src.core.models.position_value import PositionValue
from src.core.models.trading_price import TradingPrice
from src.core.models.transaction import IOFlow, Transaction, TransactionOperationType
from src.core.services.portfolio_service import PortfolioService


class StubPositionService:
    def __init__(self, positions: list[Position]) -> None:
        self.positions = positions

    def all(self, reference_date: date | None = None) -> list[Position]:
        return self.positions


class StubTransactionRepository:
    def __init__(self, dates: list[date]) -> None:
        self.transactions = [
            Transaction(
                f"transaction_{index}",
                IOFlow.INFLOW,
                transaction_date,
                TransactionOperationType.PURCHASE,
                "asset_001",
                "holding_001",
                Decimal("1"),
                Decimal("10"),
                Decimal("10"),
            )
            for index, transaction_date in enumerate(dates)
        ]

    def all(self) -> list[Transaction]:
        return self.transactions


class StubPositionValueService:
    def __init__(self, price_dates: list[date] | None = None) -> None:
        self.calls: list[tuple[Position, date]] = []
        self.trading_price_repository = StubTradingPriceRepository(price_dates or [])

    def get(self, position: Position, price_date: date) -> PositionValue:
        self.calls.append((position, price_date))
        return PositionValue(
            position,
            TradingPrice(position.asset_id, price_date, Decimal("10")),
        )


class StubTradingPriceRepository:
    def __init__(self, dates: list[date]) -> None:
        self.dates = dates

    def all(self) -> list[TradingPrice]:
        return [
            TradingPrice("asset_001", evaluation_date, Decimal("10"))
            for evaluation_date in self.dates
        ]


class PortfolioServiceTests(unittest.TestCase):
    def test_values_all_positions_on_requested_date(self) -> None:
        positions = [
            Position("asset_001", Decimal("2"), Decimal("2"), Decimal("0"), Decimal("20"), Asset("asset_001", "One")),
            Position("asset_002", Decimal("3"), Decimal("3"), Decimal("0"), Decimal("30"), Asset("asset_002", "Two")),
        ]
        value_service = StubPositionValueService()
        price_date = date(2024, 1, 31)

        portfolio = PortfolioService(
            StubPositionService(positions), value_service
        ).get(price_date)

        self.assertEqual(
            portfolio,
            Portfolio(tuple(
                PositionValue(position, TradingPrice(position.asset_id, price_date, Decimal("10")))
                for position in positions
            )),
        )
        self.assertEqual(value_service.calls, [(position, price_date) for position in positions])
        self.assertEqual(portfolio.portfolio_value, Decimal("50"))
        self.assertEqual(portfolio.value, Decimal("50"))

    def test_get_over_time_uses_transaction_and_price_dates(self) -> None:
        value_service = StubPositionValueService([date(2024, 1, 2)])
        portfolio_service = PortfolioService(
            StubPositionService([]),
            value_service,
            StubTransactionRepository([date(2024, 1, 1), date(2024, 1, 3)]),
        )

        history = portfolio_service.get_over_time()

        self.assertEqual(
            [portfolio_value.evaluation_date for portfolio_value in history],
            [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)],
        )
        self.assertEqual(
            history,
            [
                PortfolioValue(date(2024, 1, 1), Decimal("0")),
                PortfolioValue(date(2024, 1, 2), Decimal("0")),
                PortfolioValue(date(2024, 1, 3), Decimal("0")),
            ],
        )


if __name__ == "__main__":
    unittest.main()
