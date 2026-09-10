from datetime import date
from decimal import Decimal
import unittest

from src.core.models.position import Position
from src.core.models.source_position import SourcePosition
from src.core.services.portfolio_reconciliation import PortfolioReconciliationService


class StubRepository:
    def __init__(self, positions):
        self.positions = positions

    def all(self):
        return self.positions


def source_position(asset_id: str | None, quantity: str) -> SourcePosition:
    return SourcePosition(date(2020, 12, 31), asset_id, "Example Asset", Decimal(quantity))


def position(asset_id: str, quantity: str) -> Position:
    return Position(asset_id, Decimal(quantity), Decimal("0"), Decimal("0"), Decimal("0"))


class PortfolioReconciliationServiceTests(unittest.TestCase):
    def test_success_when_source_and_computed_quantities_match(self) -> None:
        result = PortfolioReconciliationService(
            StubRepository([source_position("asset_001", "2")]),
            StubRepository([position("asset_001", "2")]),
        ).reconcile()

        self.assertEqual(result.status, "success")
        self.assertEqual(result.conflicts, [])

    def test_reports_quantity_conflict(self) -> None:
        source = source_position("asset_001", "2")
        computed = position("asset_001", "3")
        result = PortfolioReconciliationService(
            StubRepository([source]), StubRepository([computed])
        ).reconcile()

        self.assertEqual(result.status, "error")
        self.assertEqual(result.conflicts[0].position, computed)
        self.assertEqual(result.conflicts[0].source_position, source)

    def test_reports_source_position_missing_from_computed_positions(self) -> None:
        source = source_position("asset_001", "2")
        result = PortfolioReconciliationService(
            StubRepository([source]), StubRepository([])
        ).reconcile()

        self.assertEqual(result.status, "error")
        self.assertIsNone(result.conflicts[0].position)
        self.assertEqual(result.conflicts[0].source_position, source)


if __name__ == "__main__":
    unittest.main()

