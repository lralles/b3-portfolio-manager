from __future__ import annotations

from datetime import date

from ..models.position import Position
from ..models.position_value import PositionValue
from ..repositories.trading_price_repository import TradingPriceRepository


class PositionValueService:
    """Associates a position with its trading price on a requested date."""

    def __init__(
        self,
        trading_price_repository: TradingPriceRepository | None = None,
    ) -> None:
        self.trading_price_repository = (
            trading_price_repository or TradingPriceRepository()
        )

    def get(self, position: Position, price_date: date) -> PositionValue:
        latest_price = self.trading_price_repository.latest_for_asset_on_or_before(
            position.asset_id, price_date
        )
        return PositionValue(position, latest_price)

    def value(self, position: Position, price_date: date) -> PositionValue:
        """Alias for callers that prefer the domain operation's name."""
        return self.get(position, price_date)
