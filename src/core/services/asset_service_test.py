from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.core.models.asset import Asset, AssetType
from src.core.services.asset_service import AssetService


class AssetServiceTests(unittest.TestCase):
    def test_save_and_all_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = AssetService(Path(directory) / "assets.csv")
            assets = [Asset("asset_001", "Example Asset")]

            service.save(assets)

            self.assertEqual(service.all(), assets)

    def test_update_changes_isin_without_changing_asset_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = AssetService(Path(directory) / "assets.csv")
            service.save([Asset("asset_001", "Example Asset")])

            updated = service.update(
                Asset("asset_001", "Example Asset", "BR1234567890", AssetType.STOCKS)
            )

            self.assertEqual(
                updated,
                Asset("asset_001", "Example Asset", "BR1234567890", AssetType.STOCKS),
            )
            self.assertEqual(service.all(), [updated])


if __name__ == "__main__":
    unittest.main()
