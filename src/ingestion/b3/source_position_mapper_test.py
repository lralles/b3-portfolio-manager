from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from src.ingestion.b3.source_position_mapper import source_position_from_sanitized_row


def sanitized_row() -> dict[str, str]:
    return {
        "Produto": "Example Asset",
        "Quantidade": "12.5",
        "evaluation_date": "2020-12-31",
    }


class SourcePositionMapperTests(unittest.TestCase):
    def test_maps_raw_shaped_sanitized_row(self) -> None:
        position = source_position_from_sanitized_row(sanitized_row(), "asset_001")

        self.assertEqual(position.evaluation_date, date(2020, 12, 31))
        self.assertEqual(position.asset_id, "asset_001")
        self.assertEqual(position.asset_name, "Example Asset")
        self.assertEqual(position.quantity, Decimal("12.5"))

    def test_allows_unmatched_asset_id(self) -> None:
        position = source_position_from_sanitized_row(sanitized_row(), None)

        self.assertIsNone(position.asset_id)
        self.assertEqual(position.asset_name, "Example Asset")

    def test_rejects_missing_raw_position_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "Quantidade"):
            source_position_from_sanitized_row(
                {"Produto": "Example Asset", "evaluation_date": "2020-12-31"},
                None,
            )


if __name__ == "__main__":
    unittest.main()
