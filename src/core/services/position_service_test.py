from __future__ import annotations

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.core.models.asset import Asset
from src.core.models.position import Position
from src.core.models.transaction import IOFlow, Transaction, TransactionOperationType
from src.core.repositories.asset_repository import AssetRepository
from src.core.repositories.position_repository import PositionRepository
from src.core.repositories.transaction_repository import TransactionRepository
from src.core.services.position_service import PositionService


class PositionServiceTests(unittest.TestCase):
    def test_build_and_save_creates_positions_from_transactions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transaction_repository = TransactionRepository(root / "transactions.csv")
            position_repository = PositionRepository(root / "positions.csv")
            asset_repository = AssetRepository(root / "assets.csv")
            transaction_repository.save([
                Transaction(
                    "transaction_001",
                    IOFlow.INFLOW,
                    date(2020, 1, 1),
                    TransactionOperationType.PURCHASE,
                    "asset_001",
                    "holding_001",
                    Decimal("4"),
                    Decimal("10"),
                    Decimal("40"),
                )
            ])
            asset_repository.save([Asset("asset_001", "Example Asset")])
            service = PositionService(
                transaction_repository, position_repository, asset_repository
            )

            saved = service.build_and_save()

            expected = Position(
                "asset_001", Decimal("4"), Decimal("4"), Decimal("0"), Decimal("40")
            )
            self.assertEqual(saved, [expected])
            self.assertEqual(position_repository.all(), [expected])

    def test_all_attaches_the_stored_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            position_repository = PositionRepository(root / "positions.csv")
            asset_repository = AssetRepository(root / "assets.csv")
            expected_asset = Asset("asset_001", "Example Asset")
            expected_position = Position(
                "asset_001", Decimal("2"), Decimal("2"), Decimal("0"), Decimal("20")
            )
            position_repository.save([expected_position])
            asset_repository.save([expected_asset])
            service = PositionService(
                TransactionRepository(root / "transactions.csv"),
                position_repository,
                asset_repository,
            )

            positions = service.all()

            self.assertEqual(positions[0], expected_position.with_asset(expected_asset))

    def test_all_raises_when_position_asset_is_not_stored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            position_repository = PositionRepository(root / "positions.csv")
            position_repository.save([
                Position("asset_001", Decimal("1"), Decimal("1"), Decimal("0"), Decimal("10"))
            ])
            asset_repository = AssetRepository(root / "assets.csv")
            asset_repository.save([])
            service = PositionService(
                position_repository=position_repository,
                asset_repository=asset_repository,
            )

            with self.assertRaisesRegex(ValueError, "No stored asset"):
                service.all()


if __name__ == "__main__":
    unittest.main()
