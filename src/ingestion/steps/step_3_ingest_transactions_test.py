from __future__ import annotations

import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from src.core.repositories.trading_price_repository import TradingPriceRepository
from src.ingestion.steps.step_3_ingest_transactions import ingest


class TransactionIngestionTests(unittest.TestCase):
    def test_extracts_one_price_per_asset_and_date_from_buys_and_sells(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "sanitized_transactions.csv"
            transactions_path = root / "transactions.csv"
            assets_path = root / "assets.csv"
            holdings_path = root / "holdings.csv"
            trading_prices_path = root / "trading_prices.csv"
            fieldnames = [
                "entrada_saida",
                "data",
                "movimentacao",
                "produto",
                "instituicao",
                "quantidade",
                "preco_unitario",
                "valor_operacao",
            ]
            with input_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(
                    [
                        {
                            "entrada_saida": "Credito",
                            "data": "2024-01-31",
                            "movimentacao": "Compra",
                            "produto": "Asset A",
                            "instituicao": "Broker",
                            "quantidade": "1",
                            "preco_unitario": "10",
                            "valor_operacao": "10",
                        },
                        {
                            "entrada_saida": "Debito",
                            "data": "2024-01-31",
                            "movimentacao": "Venda",
                            "produto": "Asset A",
                            "instituicao": "Broker",
                            "quantidade": "1",
                            "preco_unitario": "11",
                            "valor_operacao": "11",
                        },
                        {
                            "entrada_saida": "Credito",
                            "data": "2024-01-31",
                            "movimentacao": "Rendimento",
                            "produto": "Asset A",
                            "instituicao": "Broker",
                            "quantidade": "1",
                            "preco_unitario": "99",
                            "valor_operacao": "99",
                        },
                        {
                            "entrada_saida": "Credito",
                            "data": "2024-01-31",
                            "movimentacao": "Transferência",
                            "produto": "Asset A",
                            "instituicao": "Broker",
                            "quantidade": "1",
                            "preco_unitario": "88",
                            "valor_operacao": "88",
                        },
                        {
                            "entrada_saida": "Credito",
                            "data": "2024-01-31",
                            "movimentacao": "Transferência - Liquidação",
                            "produto": "Asset B",
                            "instituicao": "Broker",
                            "quantidade": "1",
                            "preco_unitario": "20",
                            "valor_operacao": "20",
                        },
                    ]
                )

            ingest(
                input_path,
                transactions_path,
                assets_path,
                holdings_path,
                trading_prices_path=trading_prices_path,
            )

            prices = TradingPriceRepository(trading_prices_path).all()
            self.assertEqual(len(prices), 2)
            prices_by_asset = {price.asset_id: price.value for price in prices}
            self.assertEqual(prices_by_asset["asset_002"], Decimal("20"))
            self.assertIn(prices_by_asset["asset_001"], {Decimal("10"), Decimal("11")})


if __name__ == "__main__":
    unittest.main()
