from __future__ import annotations

from ...repositories.position_repository import PositionRepository
from ...repositories.source_position_repository import SourcePositionRepository
from .position_conflict import PositionConflict
from .status import PortfolioReconciliationStatus


class PortfolioReconciliationService:
    """Compares source position quantities with computed position quantities."""

    def __init__(
        self,
        source_position_repository: SourcePositionRepository | None = None,
        position_repository: PositionRepository | None = None,
    ) -> None:
        self.source_position_repository = (
            source_position_repository or SourcePositionRepository()
        )
        self.position_repository = position_repository or PositionRepository()

    def reconcile(self) -> PortfolioReconciliationStatus:
        computed_positions = {
            position.asset_id: position for position in self.position_repository.all()
        }
        conflicts = []

        for source_position in self.source_position_repository.all():
            position = (
                computed_positions.get(source_position.asset_id)
                if source_position.asset_id is not None
                else None
            )
            if position is None or position.current_quantity != source_position.quantity:
                conflicts.append(PositionConflict(position, source_position))

        return PortfolioReconciliationStatus(
            status="error" if conflicts else "success",
            conflicts=conflicts,
        )


def reconcile_portfolio(
    source_position_repository: SourcePositionRepository | None = None,
    position_repository: PositionRepository | None = None,
) -> PortfolioReconciliationStatus:
    return PortfolioReconciliationService(
        source_position_repository, position_repository
    ).reconcile()
