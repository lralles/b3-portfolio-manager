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
