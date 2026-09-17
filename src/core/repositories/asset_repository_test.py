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

    def test_old_asset_rows_without_isin_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assets.csv"
            path.write_text("asset_id,asset_name\nasset_001,Example Asset\n", encoding="utf-8")

            self.assertEqual(
                AssetRepository(path).all(),
                [Asset("asset_001", "Example Asset")],
            )

    def test_update_replaces_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = AssetRepository(Path(directory) / "assets.csv")
            repository.save([Asset("asset_001", "Example Asset")])

            updated = repository.update(
                Asset("asset_001", "Renamed Asset", "BR1234567890")
            )

            self.assertEqual(updated, Asset("asset_001", "Renamed Asset", "BR1234567890"))
            self.assertEqual(repository.all(), [updated])


if __name__ == "__main__":
    unittest.main()
