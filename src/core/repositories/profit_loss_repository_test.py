from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from src.core.models.profit_loss import ProfitLoss, ProfitLossType
from src.core.repositories.profit_loss_repository import ProfitLossRepository


class ProfitLossRepositoryTests(unittest.TestCase):
    def test_repository_round_trip_persists_realized_type(self) -> None:
        profit_loss = ProfitLoss(
            "asset_001",
            "transaction_001",
            "holding_001",
            Decimal("-5.25"),
            ProfitLossType.NOT_REALIZED,
        )

        with tempfile.TemporaryDirectory() as directory:
            repository = ProfitLossRepository(Path(directory) / "profit_losses.csv")
            repository.save([profit_loss])

            self.assertEqual(
                repository.all(),
                [
                    ProfitLoss(
                        "asset_001",
                        "transaction_001",
                        "holding_001",
                        Decimal("-5.25"),
                        ProfitLossType.REALIZED,
                    )
                ],
            )


if __name__ == "__main__":
    unittest.main()
