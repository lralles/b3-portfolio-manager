from __future__ import annotations

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.core.models.source_position import SourcePosition
from src.core.services.source_position_service import SourcePositionService


class SourcePositionServiceTests(unittest.TestCase):
    def test_save_and_all_round_trip(self) -> None:
        position = SourcePosition(
            date(2020, 12, 31), "asset_001", "Example Asset", Decimal("3.5")
        )

        with tempfile.TemporaryDirectory() as directory:
            service = SourcePositionService(Path(directory) / "source_positions.csv")

            service.save([position])

            self.assertEqual(service.all(), [position])


if __name__ == "__main__":
    unittest.main()
