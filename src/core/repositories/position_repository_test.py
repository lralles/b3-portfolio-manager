from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from src.core.models.position import Position
from src.core.repositories.position_repository import PositionRepository


class PositionRepositoryTests(unittest.TestCase):
    def test_repository_round_trip_and_sorting(self) -> None:
        positions = [
            Position("asset_002", Decimal("3"), Decimal("4"), Decimal("1"), Decimal("30")),
            Position("asset_001", Decimal("2"), Decimal("2"), Decimal("0"), Decimal("20")),
        ]

        with tempfile.TemporaryDirectory() as directory:
            repository = PositionRepository(Path(directory) / "positions.csv")
            repository.save(positions)

            self.assertEqual(repository.all(), [positions[1], positions[0]])


if __name__ == "__main__":
    unittest.main()
