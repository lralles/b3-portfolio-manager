from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from src.core.models.asset import Asset
from src.core.repositories.asset_repository import AssetRepository
from src.ingestion.steps.step_4_ingest_source_positions import ingest


class SourcePositionIngestionTests(unittest.TestCase):
    def test_ingest_updates_matched_asset_isin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets_path = root / "assets.csv"
            input_path = root / "sanitized_positions.csv"
            output_path = root / "source_positions.csv"
            AssetRepository(assets_path).save([Asset("asset_001", "Example Asset")])
            with input_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=[
                        "evaluation_date",
                        "Produto",
                        "Quantidade",
                        "Código ISIN",
                        "Código ISIN / Distribuição",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "evaluation_date": "2024-01-31",
                        "Produto": "Example Asset",
                        "Quantidade": "2",
                        "Código ISIN": "BR1234567890",
                        "Código ISIN / Distribuição": "BR1234567890",
                    }
                )

            ingest(input_path, output_path, assets_path)

            self.assertEqual(
                AssetRepository(assets_path).all(),
                [Asset("asset_001", "Example Asset", "BR1234567890")],
            )


if __name__ == "__main__":
    unittest.main()
