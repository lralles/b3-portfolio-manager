from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.core.models.holding import Holding
from src.core.services.holding_service import HoldingService


class HoldingServiceTests(unittest.TestCase):
    def test_save_and_all_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = HoldingService(Path(directory) / "holdings.csv")
            holdings = [Holding("holding_001", "Example Institution")]

            service.save(holdings)

            self.assertEqual(service.all(), holdings)


if __name__ == "__main__":
    unittest.main()
