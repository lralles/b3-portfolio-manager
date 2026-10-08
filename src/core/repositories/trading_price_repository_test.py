from __future__ import annotations

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.core.models.trading_price import TradingPrice
from src.core.repositories.trading_price_repository import TradingPriceRepository


class TradingPriceRepositoryTests(unittest.TestCase):
    def test_repository_round_trip_defaults_currency_to_brl(self) -> None:
        trading_price = TradingPrice("asset_001", date(2024, 1, 31), Decimal("10.50"))

        with tempfile.TemporaryDirectory() as directory:
            repository = TradingPriceRepository(Path(directory) / "trading_prices.csv")
            repository.save([trading_price])

            self.assertEqual(repository.all(), [trading_price])
            self.assertEqual(repository.all()[0].currency, "BRL")

    def test_repository_sorts_by_evaluation_date_and_asset(self) -> None:
        prices = [
            TradingPrice("asset_002", date(2024, 2, 29), Decimal("20")),
            TradingPrice("asset_001", date(2024, 1, 31), Decimal("10")),
        ]

        with tempfile.TemporaryDirectory() as directory:
            repository = TradingPriceRepository(Path(directory) / "trading_prices.csv")
            repository.save(prices)

            self.assertEqual([price.asset_id for price in repository.all()], [
                "asset_001",
                "asset_002",
            ])

    def test_latest_for_asset_on_or_before_date(self) -> None:
        prices = [
            TradingPrice("asset_001", date(2024, 1, 1), Decimal("10")),
            TradingPrice("asset_001", date(2024, 1, 31), Decimal("12.50")),
            TradingPrice("asset_001", date(2024, 3, 1), Decimal("13")),
        ]

        with tempfile.TemporaryDirectory() as directory:
            repository = TradingPriceRepository(Path(directory) / "prices.csv")
            repository.save(prices)

            self.assertEqual(
                repository.latest_for_asset_on_or_before(
                    "asset_001", date(2024, 2, 15)
                ),
                prices[1],
            )

    def test_latest_for_asset_on_or_before_date_returns_zero_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = TradingPriceRepository(Path(directory) / "prices.csv")
            repository.save([])

            self.assertEqual(
                repository.latest_for_asset_on_or_before(
                    "asset_001", date(2024, 1, 31)
                ),
                TradingPrice("asset_001", None, Decimal("0")),
            )


if __name__ == "__main__":
    unittest.main()
