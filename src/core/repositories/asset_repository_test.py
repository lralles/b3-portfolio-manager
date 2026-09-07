from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.core.models.asset import Asset
from src.core.repositories.asset_repository import AssetRepository


class AssetRepositoryTests(unittest.TestCase):
    def test_repository_round_trip(self) -> None:
        asset = Asset("asset_001", "Example Asset")

        with tempfile.TemporaryDirectory() as directory:
            repository = AssetRepository(Path(directory) / "assets.csv")
            repository.save([asset])

            self.assertEqual(repository.all(), [asset])


if __name__ == "__main__":
    unittest.main()
