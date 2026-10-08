from __future__ import annotations

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.core.models.position import Position
from src.core.models.position_value import PositionValue
from src.core.models.trading_price import TradingPrice
from src.core.repositories.trading_price_repository import TradingPriceRepository
from src.core.services.position_value_service import PositionValueService


class PositionValueServiceTests(unittest.TestCase):
    def test_get_fetches_price_for_position_and_date(self) -> None:
        position = Position("asset_001", Decimal("2"), Decimal("2"), Decimal("0"), Decimal("20"))
        price = TradingPrice("asset_001", date(2024, 1, 31), Decimal("12.50"))

        with tempfile.TemporaryDirectory() as directory:
            repository = TradingPriceRepository(Path(directory) / "prices.csv")
            repository.save([price, TradingPrice("asset_001", date(2024, 2, 29), Decimal("13"))])

            self.assertEqual(
                PositionValueService(repository).get(position, date(2024, 1, 31)),
                PositionValue(position, price),
            )
            self.assertEqual(
                PositionValueService(repository).get(position, date(2024, 1, 31)).value,
                Decimal("25.00"),
            )

    def test_get_uses_latest_price_on_or_before_requested_date(self) -> None:
        position = Position("asset_001", Decimal("2"), Decimal("2"), Decimal("0"), Decimal("20"))
        latest_price = TradingPrice("asset_001", date(2024, 1, 31), Decimal("12.50"))

        with tempfile.TemporaryDirectory() as directory:
            repository = TradingPriceRepository(Path(directory) / "prices.csv")
            repository.save([
                TradingPrice("asset_001", date(2024, 1, 1), Decimal("10")),
                latest_price,
                TradingPrice("asset_001", date(2024, 3, 1), Decimal("13")),
            ])

            result = PositionValueService(repository).get(position, date(2024, 2, 15))

            self.assertEqual(result, PositionValue(position, latest_price))

    def test_get_uses_zero_when_price_is_missing(self) -> None:
        position = Position("asset_001", Decimal("2"), Decimal("2"), Decimal("0"), Decimal("20"))

        with tempfile.TemporaryDirectory() as directory:
            repository = TradingPriceRepository(Path(directory) / "prices.csv")
            repository.save([])

            result = PositionValueService(repository).get(position, date(2024, 1, 31))

            self.assertIsNone(result.trading_price.evaluation_date)
            self.assertEqual(result.trading_price.value, Decimal("0"))
            self.assertEqual(result.value, Decimal("0"))


if __name__ == "__main__":
    unittest.main()
