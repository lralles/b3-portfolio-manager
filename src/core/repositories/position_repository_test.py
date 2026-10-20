from __future__ import annotations

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.core.models.position import Position
from src.core.repositories.position_repository import PositionRepository


class PositionRepositoryTests(unittest.TestCase):
    def test_repository_round_trip_and_sorting(self) -> None:
        positions = [
            Position(
                "asset_002", Decimal("3"), Decimal("4"), Decimal("1"), Decimal("30"),
                reference_date=date(2020, 2, 1),
            ),
            Position(
                "asset_001", Decimal("2"), Decimal("2"), Decimal("0"), Decimal("20"),
                reference_date=date(2020, 1, 1),
            ),
        ]

        with tempfile.TemporaryDirectory() as directory:
            repository = PositionRepository(Path(directory) / "positions.csv")
            repository.save(positions)

            self.assertEqual(repository.all(), [positions[1], positions[0]])

    def test_all_returns_latest_position_on_or_before_reference_date(self) -> None:
        positions = [
            Position(
                "asset_001",
                Decimal("2"),
                Decimal("2"),
                Decimal("0"),
                Decimal("20"),
                reference_date=date(2020, 1, 1),
            ),
            Position(
                "asset_001",
                Decimal("5"),
                Decimal("5"),
                Decimal("0"),
                Decimal("50"),
                reference_date=date(2020, 3, 1),
            ),
        ]

        with tempfile.TemporaryDirectory() as directory:
            repository = PositionRepository(Path(directory) / "positions.csv")
            repository.save(positions)

            self.assertEqual(repository.all(date(2020, 2, 1)), [positions[0]])
            self.assertEqual(repository.all(date(2020, 3, 1)), [positions[1]])


if __name__ == "__main__":
    unittest.main()
