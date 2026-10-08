from __future__ import annotations

from dataclasses import dataclass

from .position_value import PositionValue


@dataclass(frozen=True, slots=True)
class Portfolio:
    """A collection of position values for one evaluation date."""

    position_values: tuple[PositionValue, ...]
