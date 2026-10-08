from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .position_value import PositionValue


@dataclass(frozen=True, slots=True)
class Portfolio:
    """A collection of position values for one evaluation date."""

    position_values: tuple[PositionValue, ...]

    @property
    def portfolio_value(self) -> Decimal:
        total = Decimal("0")
        for position_value in self.position_values:
            total += position_value.value
        return total

    @property
    def value(self) -> Decimal:
        """Alias for the total value of the portfolio."""
        return self.portfolio_value
