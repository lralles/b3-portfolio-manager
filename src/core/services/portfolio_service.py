from __future__ import annotations

from datetime import date

from ..models.portfolio import Portfolio
from .position_service import PositionService
from .position_value_service import PositionValueService


class PortfolioService:
    """Builds a portfolio by valuing every stored position."""

    def __init__(
        self,
        position_service: PositionService | None = None,
        position_value_service: PositionValueService | None = None,
    ) -> None:
        self.position_service = position_service or PositionService()
        self.position_value_service = (
            position_value_service or PositionValueService()
        )

    def get(self, price_date: date) -> Portfolio:
        positions = self.position_service.all()
        position_values = []
        for position in positions:
            position_value = self.position_value_service.get(position, price_date)
            position_values.append(position_value)
        return Portfolio(tuple(position_values))

    def build(self, price_date: date) -> Portfolio:
        """Alias for callers that prefer the construction operation's name."""
        return self.get(price_date)
