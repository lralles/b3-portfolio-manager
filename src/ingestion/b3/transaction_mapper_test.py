from __future__ import annotations

import unittest

from src.core.models.transaction import IOFlow, TransactionOperationType
from src.ingestion.b3.transaction_mapper import transaction_from_sanitized_row


def sanitized_row(direction: str) -> dict[str, str]:
    return {
        "entrada_saida": direction,
        "data": "2020-01-01",
        "movimentacao": "transferência - liquidação",
        "quantidade": "2",
        "preco_unitario": "10",
        "valor_operacao": "20",
    }


class TransactionMapperTests(unittest.TestCase):
    def test_position_income_is_an_outflow_even_when_b3_credits_it(self) -> None:
        for operation in (
            "Dividendo",
            "Juros Sobre Capital Próprio",
            "Rendimento",
            "Leilão de Fração",
        ):
            with self.subTest(operation=operation):
                row = sanitized_row("credito")
                row["movimentacao"] = operation
                transaction = transaction_from_sanitized_row(
                    row, "transaction_001", "asset_001", "holding_001"
                )
                self.assertEqual(transaction.io_flow, IOFlow.OUTFLOW)

    def test_maturity_is_mapped_to_redemption_and_is_an_outflow(self) -> None:
        row = sanitized_row("debito")
        row["movimentacao"] = "Vencimento"

        transaction = transaction_from_sanitized_row(
            row, "transaction_001", "asset_001", "holding_001"
        )

        self.assertEqual(transaction.io_flow, IOFlow.OUTFLOW)
        self.assertEqual(transaction.operation_type, TransactionOperationType.REDEMPTION)

    def test_maturity_without_price_is_rejected(self) -> None:
        row = sanitized_row("debito")
        row["movimentacao"] = "Vencimento"
        row["preco_unitario"] = "0"
        row["valor_operacao"] = "0"

        with self.assertRaisesRegex(ValueError, "VENCIMENTO transaction is missing a positive price"):
            transaction_from_sanitized_row(
                row, "transaction_001", "asset_001", "holding_001"
            )

    def test_buy_sell_credit_is_mapped_to_purchase(self) -> None:
        row = sanitized_row("credito")
        row["movimentacao"] = "Compra / Venda"

        transaction = transaction_from_sanitized_row(
            row, "transaction_001", "asset_001", "holding_001"
        )

        self.assertEqual(transaction.io_flow, IOFlow.INFLOW)
        self.assertEqual(transaction.operation_type, TransactionOperationType.PURCHASE)

    def test_buy_sell_debit_is_mapped_to_sale(self) -> None:
        row = sanitized_row("debito")
        row["movimentacao"] = "Compra / Venda"

        transaction = transaction_from_sanitized_row(
            row, "transaction_001", "asset_001", "holding_001"
        )

        self.assertEqual(transaction.io_flow, IOFlow.OUTFLOW)
        self.assertEqual(transaction.operation_type, TransactionOperationType.SALE)

    def test_settlement_credit_is_mapped_to_purchase(self) -> None:
        transaction = transaction_from_sanitized_row(
            sanitized_row("credito"), "transaction_001", "asset_001", "holding_001"
        )

        self.assertEqual(transaction.io_flow, IOFlow.INFLOW)
        self.assertEqual(transaction.operation_type, TransactionOperationType.PURCHASE)

    def test_settlement_debit_is_mapped_to_sale(self) -> None:
        transaction = transaction_from_sanitized_row(
            sanitized_row("debito"), "transaction_001", "asset_001", "holding_001"
        )

        self.assertEqual(transaction.io_flow, IOFlow.OUTFLOW)
        self.assertEqual(transaction.operation_type, TransactionOperationType.SALE)


if __name__ == "__main__":
    unittest.main()
