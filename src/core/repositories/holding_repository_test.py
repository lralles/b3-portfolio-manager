from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.core.models.holding import Holding
from src.core.repositories.holding_repository import HoldingRepository


class HoldingRepositoryTests(unittest.TestCase):
    def test_repository_round_trip(self) -> None:
        holding = Holding("holding_001", "Example Holding")

        with tempfile.TemporaryDirectory() as directory:
            repository = HoldingRepository(Path(directory) / "holdings.csv")
            repository.save([holding])

            self.assertEqual(repository.all(), [holding])


if __name__ == "__main__":
    unittest.main()
