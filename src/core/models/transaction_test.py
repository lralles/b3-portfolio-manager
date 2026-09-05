from __future__ import annotations

import unittest

from src.core.models.transaction import (
    IOFlow,
    Transaction,
    TransactionOperationType,
)


def sanitized_row(direction: str) -> dict[str, str]:
    return {
        "entrada_saida": direction,
        "data": "2020-01-01",
        "movimentacao": "transferência - liquidação",
        "quantidade": "2",
        "preco_unitario": "10",
        "valor_operacao": "20",
    }


class TransactionIngestionTests(unittest.TestCase):
    def test_settlement_credit_is_ingested_as_purchase(self) -> None:
        transaction = Transaction.from_sanitized_row(
            sanitized_row("credito"), "asset_001", "account_001"
        )

        self.assertEqual(transaction.io_flow, IOFlow.INFLOW)
        self.assertEqual(transaction.operation_type, TransactionOperationType.PURCHASE)

    def test_settlement_debit_is_ingested_as_sale(self) -> None:
        transaction = Transaction.from_sanitized_row(
            sanitized_row("debito"), "asset_001", "account_001"
        )

        self.assertEqual(transaction.io_flow, IOFlow.OUTFLOW)
        self.assertEqual(transaction.operation_type, TransactionOperationType.SALE)

    def test_store_row_persists_io_flow_instead_of_direction(self) -> None:
        transaction = Transaction.from_sanitized_row(
            sanitized_row("credito"), "asset_001", "account_001"
        )

        row = transaction.to_formatted_row()

        self.assertNotIn("direction", row)
        self.assertEqual(row["io_flow"], IOFlow.INFLOW.value)
        self.assertEqual(Transaction.from_store_row(row), transaction)


if __name__ == "__main__":
    unittest.main()
