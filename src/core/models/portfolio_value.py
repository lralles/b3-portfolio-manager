from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PortfolioValue:
    """The total portfolio value for one evaluation date."""

    evaluation_date: date
    value: Decimal
