from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.core.models.asset import Asset, AssetType
from src.core.models.trading_price import TradingPrice
from src.core.repositories.asset_repository import AssetRepository
from src.core.repositories.trading_price_repository import TradingPriceRepository
from src.ingestion.steps.step_4_ingest_source_positions import ingest


class SourcePositionIngestionTests(unittest.TestCase):
    def test_ingest_updates_matched_asset_isin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets_path = root / "assets.csv"
            input_path = root / "sanitized_positions.csv"
            output_path = root / "source_positions.csv"
            trading_prices_path = root / "trading_prices.csv"
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
                        "asset_type",
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
                        "asset_type": "stocks",
                    }
                )

            ingest(
                input_path,
                output_path,
                assets_path,
                trading_prices_path=trading_prices_path,
            )

            self.assertEqual(
                AssetRepository(assets_path).all(),
                [Asset("asset_001", "Example Asset", "BR1234567890", AssetType.STOCKS)],
            )

    def test_ingest_enriches_from_earliest_position(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets_path = root / "assets.csv"
            input_path = root / "sanitized_positions.csv"
            output_path = root / "source_positions.csv"
            trading_prices_path = root / "trading_prices.csv"
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
                        "asset_type",
                    ],
                )
                writer.writeheader()
                writer.writerows(
                    [
                        {
                            "evaluation_date": "2020-12-31",
                            "Produto": "Example Asset",
                            "Quantidade": "0",
                            "Código ISIN": "",
                            "Código ISIN / Distribuição": "",
                            "asset_type": "",
                        },
                        {
                            "evaluation_date": "2020-07-31",
                            "Produto": "Example Asset",
                            "Quantidade": "2",
                            "Código ISIN": "BR1234567890",
                            "Código ISIN / Distribuição": "BR1234567890",
                            "asset_type": "stocks",
                        },
                    ]
                )

            ingest(
                input_path,
                output_path,
                assets_path,
                trading_prices_path=trading_prices_path,
            )

            self.assertEqual(
                AssetRepository(assets_path).all(),
                [Asset("asset_001", "Example Asset", "BR1234567890", AssetType.STOCKS)],
            )

    def test_prefix_fallback_does_not_assign_unmatched_fixed_income_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets_path = root / "assets.csv"
            input_path = root / "sanitized_positions.csv"
            output_path = root / "source_positions.csv"
            AssetRepository(assets_path).save(
                [Asset("asset_001", "CDB - CDB123 - BANK", asset_type=AssetType.PRIVATE_BOND)]
            )
            fieldnames = ["evaluation_date", "Produto", "Quantidade", "asset_type"]
            with input_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(
                    {
                        "evaluation_date": "2024-01-31",
                        "Produto": "CDB - BANK - 04/06/2024",
                        "Quantidade": "2",
                        "asset_type": "private_bond",
                    }
                )

            ingest(input_path, output_path, assets_path)

            with output_path.open(newline="", encoding="utf-8") as fh:
                row = next(csv.DictReader(fh))
            self.assertEqual(row["asset_id"], "")

    def test_ingest_extracts_trading_prices_by_asset_type(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets_path = root / "assets.csv"
            input_path = root / "sanitized_positions.csv"
            output_path = root / "source_positions.csv"
            trading_prices_path = root / "trading_prices.csv"
            AssetRepository(assets_path).save(
                [
                    Asset("stock", "Stock", asset_type=AssetType.STOCKS),
                    Asset("fii", "FII", asset_type=AssetType.FII),
                    Asset("bond", "Bond", asset_type=AssetType.TREASURY_BOND),
                ]
            )
            TradingPriceRepository(trading_prices_path).save(
                [TradingPrice("stock", date(2024, 1, 31), Decimal("999"))]
            )
            fieldnames = [
                "evaluation_date",
                "Produto",
                "Quantidade",
                "Código ISIN",
                "Código ISIN / Distribuição",
                "Preço de Fechamento",
                "Valor Atualizado",
                "asset_type",
            ]
            with input_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(
                    [
                        {
                            "evaluation_date": "2024-01-31",
                            "Produto": "Stock",
                            "Quantidade": "2",
                            "Preço de Fechamento": "10.50",
                            "Valor Atualizado": "21",
                            "asset_type": "stocks",
                        },
                        {
                            "evaluation_date": "2024-01-31",
                            "Produto": "FII",
                            "Quantidade": "2",
                            "Preço de Fechamento": "20.25",
                            "Valor Atualizado": "40.50",
                            "asset_type": "fii",
                        },
                        {
                            "evaluation_date": "2024-01-31",
                            "Produto": "Bond",
                            "Quantidade": "0.5",
                            "Preço de Fechamento": "-",
                            "Valor Atualizado": "100",
                            "asset_type": "treasury_bond",
                        },
                    ]
                )

            ingest(
                input_path,
                output_path,
                assets_path,
                trading_prices_path=trading_prices_path,
            )

            prices = TradingPriceRepository(trading_prices_path).all()
            self.assertEqual(
                [(price.asset_id, price.value) for price in prices],
                [
                    ("bond", Decimal("200")),
                    ("fii", Decimal("20.25")),
                    ("stock", Decimal("10.50")),
                ],
            )

if __name__ == "__main__":
    unittest.main()
