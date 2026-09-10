from __future__ import annotations

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.core.models.source_position import SourcePosition
from src.core.repositories.source_position_repository import SourcePositionRepository


class SourcePositionRepositoryTests(unittest.TestCase):
    def test_repository_round_trip_and_sorting(self) -> None:
        positions = [
            SourcePosition(date(2020, 12, 31), None, "Zeta Asset", Decimal("2")),
            SourcePosition(date(2020, 12, 31), "asset_001", "Alpha Asset", Decimal("1.5")),
        ]

        with tempfile.TemporaryDirectory() as directory:
            repository = SourcePositionRepository(Path(directory) / "source_positions.csv")
            repository.save(positions)

            self.assertEqual(repository.all(), [positions[1], positions[0]])

    def test_empty_asset_id_is_loaded_as_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source_positions.csv"
            path.write_text(
                "evaluation_date,asset_id,asset_name,quantity\n"
                "2020-12-31,,Unmatched Asset,3\n",
                encoding="utf-8",
            )

            position = SourcePositionRepository(path).all()[0]

            self.assertIsNone(position.asset_id)


if __name__ == "__main__":
    unittest.main()
