from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from config import Config
from ...models.source_position import SourcePosition
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
        latest_source_positions = list(
            source_position
            for source_position in source_positions
            if source_position.evaluation_date == latest_evaluation_date
        )
        grouped_source_positions: dict[str, SourcePosition] = {}
        unresolved_source_positions: list[SourcePosition] = []
        for source_position in latest_source_positions:
            if source_position.asset_id is None:
                unresolved_source_positions.append(source_position)
                continue
            existing = grouped_source_positions.get(source_position.asset_id)
            if existing is None:
                grouped_source_positions[source_position.asset_id] = source_position
            else:
                grouped_source_positions[source_position.asset_id] = replace(
                    existing,
                    quantity=existing.quantity + source_position.quantity,
                )
        reconciled_source_positions = list(grouped_source_positions.values())
        reconciled_source_positions.extend(unresolved_source_positions)
        source_positions_by_asset = {
            source_position.asset_id: source_position
            for source_position in reconciled_source_positions
            if source_position.asset_id is not None
        }

        for source_position in reconciled_source_positions:
            position = (
                computed_positions.get(source_position.asset_id)
                if source_position.asset_id is not None
                else None
            )
            if position is None or position.current_quantity != source_position.quantity:
                conflicts.append(PositionConflict(position, source_position))

        if latest_evaluation_date is not None:
            for asset_id, position in computed_positions.items():
                if position.current_quantity == 0 or asset_id in source_positions_by_asset:
                    continue
                asset_name = position.asset.asset_name if position.asset else ""
                conflicts.append(
                    PositionConflict(
                        position,
                        SourcePosition(
                            evaluation_date=latest_evaluation_date,
                            asset_id=asset_id,
                            asset_name=asset_name,
                            quantity=Decimal("0"),
                        ),
                    )
                )

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
