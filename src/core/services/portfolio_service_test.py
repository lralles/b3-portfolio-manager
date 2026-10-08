from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from src.core.models.asset import Asset
from src.core.models.portfolio import Portfolio
from src.core.models.position import Position
from src.core.models.position_value import PositionValue
from src.core.models.trading_price import TradingPrice
from src.core.services.portfolio_service import PortfolioService


class StubPositionService:
    def __init__(self, positions: list[Position]) -> None:
        self.positions = positions

    def all(self) -> list[Position]:
        return self.positions


class StubPositionValueService:
    def __init__(self) -> None:
        self.calls: list[tuple[Position, date]] = []

    def get(self, position: Position, price_date: date) -> PositionValue:
        self.calls.append((position, price_date))
        return PositionValue(
            position,
            TradingPrice(position.asset_id, price_date, Decimal("10")),
        )


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


if __name__ == "__main__":
    unittest.main()
