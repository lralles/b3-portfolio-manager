from __future__ import annotations

import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from src.core.repositories.trading_price_repository import TradingPriceRepository
from src.ingestion.steps.step_3_ingest_transactions import (
    asset_key,
    normalize_transferred_income_rows,
    ingest,
)


class TransactionIngestionTests(unittest.TestCase):
    def test_transferred_income_pairs_become_one_credited_event(self) -> None:
        row = {
            "entrada_saida": "Debito",
            "data": "2021-05-14",
            "movimentacao": "Dividendo - Transferido",
            "produto": "ASSET - Example",
            "instituicao": "Rico",
            "quantidade": "4",
            "preco_unitario": "0.10",
            "valor_operacao": "0.42",
        }
        credit = dict(row)
        credit["entrada_saida"] = "Credito"
        credit["instituicao"] = "XP"

        normalized = normalize_transferred_income_rows([row, credit])

        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["entrada_saida"], "Credito")
        self.assertEqual(normalized[0]["movimentacao"], "dividendo")
        self.assertEqual(normalized[0]["instituicao"], "XP")

    def test_transferred_income_requires_balanced_pairs(self) -> None:
        row = {
            "entrada_saida": "Debito",
            "data": "2021-05-14",
            "movimentacao": "Juros Sobre Capital Próprio - Transferido",
            "produto": "ASSET - Example",
            "instituicao": "Rico",
            "quantidade": "4",
            "preco_unitario": "0.10",
            "valor_operacao": "0.42",
        }

        with self.assertRaisesRegex(ValueError, "matching debit and credit"):
            normalize_transferred_income_rows([row])

    def test_asset_key_uses_ticker_for_b3_product_names(self) -> None:
        self.assertEqual(
            asset_key("B3SA3 - B3 S.A. – BRASIL, BOLSA, BALCÃO"), "B3SA3"
        )
        self.assertEqual(asset_key("Tesouro IPCA+ 2026"), "Tesouro IPCA+ 2026")

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
