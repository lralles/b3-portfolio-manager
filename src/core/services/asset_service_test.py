from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.core.models.asset import Asset
from src.core.services.asset_service import AssetService


class AssetServiceTests(unittest.TestCase):
    def test_save_and_all_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = AssetService(Path(directory) / "assets.csv")
            assets = [Asset("asset_001", "Example Asset")]

            service.save(assets)

            self.assertEqual(service.all(), assets)


if __name__ == "__main__":
    unittest.main()
