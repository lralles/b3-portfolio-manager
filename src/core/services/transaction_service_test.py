from __future__ import annotations

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.core.models.transaction import IOFlow, Transaction, TransactionOperationType
from src.core.services.transaction_service import TransactionService


class TransactionServiceTests(unittest.TestCase):
    def test_save_and_all_round_trip(self) -> None:
        transaction = Transaction(
            io_flow=IOFlow.INFLOW,
            date=date(2020, 1, 1),
            operation_type=TransactionOperationType.PURCHASE,
            asset_id="asset_001",
            holding_id="holding_001",
            quantity=Decimal("2"),
            unit_price=Decimal("10"),
            operation_value=Decimal("20"),
        )

        with tempfile.TemporaryDirectory() as directory:
            service = TransactionService(Path(directory) / "transactions.csv")

            service.save([transaction])

            self.assertEqual(service.all(), [transaction])


if __name__ == "__main__":
    unittest.main()
