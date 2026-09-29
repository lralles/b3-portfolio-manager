from __future__ import annotations

import unittest

from src.core.models.asset import AssetType
from src.ingestion.steps.step_2_sanitize_source_positions import (
    asset_type_from_sheet_name,
)


class SourcePositionSanitizationTests(unittest.TestCase):
    def test_asset_type_is_resolved_from_worksheet_name(self) -> None:
        self.assertEqual(asset_type_from_sheet_name("Ações"), AssetType.STOCKS)
        self.assertEqual(
            asset_type_from_sheet_name("Fundo de Investimento"), AssetType.FII
        )
        self.assertEqual(asset_type_from_sheet_name("ETF"), AssetType.ETF)
        self.assertEqual(
            asset_type_from_sheet_name("Tesouro Direto"), AssetType.TREASURY_BOND
        )

    def test_unknown_worksheet_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported B3 position worksheet"):
            asset_type_from_sheet_name("Unknown")


if __name__ == "__main__":
    unittest.main()
