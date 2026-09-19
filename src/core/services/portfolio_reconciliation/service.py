from __future__ import annotations

from config import Config
from ..position_service import PositionService
from ..source_position_service import SourcePositionService
from .position_conflict import PositionConflict
from .status import PortfolioReconciliationStatus


class PortfolioReconciliationService:
    """Compares source position quantities with computed position quantities."""

    def __init__(
        self,
        source_position_repository=None,
        position_repository=None,
        config: Config | None = None,
    ) -> None:
        self.config = config or Config()
        self.source_position_repository = (
            source_position_repository or SourcePositionService(config=self.config)
        )
        self.position_repository = position_repository or PositionService(config=self.config)

    def reconcile(self) -> PortfolioReconciliationStatus:
        computed_positions = {
            position.asset_id: position for position in self.position_repository.all()
        }
        conflicts = []

        source_positions = self.source_position_repository.all()
        latest_evaluation_date = max(
            (source_position.evaluation_date for source_position in source_positions),
            default=None,
        )
        latest_source_positions = (
            source_position
            for source_position in source_positions
            if source_position.evaluation_date == latest_evaluation_date
        )

        for source_position in latest_source_positions:
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
    source_position_repository=None,
    position_repository=None,
    config: Config | None = None,
) -> PortfolioReconciliationStatus:
    return PortfolioReconciliationService(
        source_position_repository, position_repository, config
    ).reconcile()
