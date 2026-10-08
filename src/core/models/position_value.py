from __future__ import annotations

from dataclasses import dataclass

from .position import Position
from .trading_price import TradingPrice


@dataclass(frozen=True, slots=True)
class PositionValue:
    """A position together with its trading price for an evaluation date."""

    position: Position
    trading_price: TradingPrice

    def __post_init__(self) -> None:
        if self.position.asset_id != self.trading_price.asset_id:
            raise ValueError(
                f"Trading price asset {self.trading_price.asset_id!r} does not "
                f"match position {self.position.asset_id!r}"
            )
