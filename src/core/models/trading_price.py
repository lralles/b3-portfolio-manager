from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


DEFAULT_CURRENCY = "BRL"


@dataclass(frozen=True, slots=True)
class TradingPrice:
    asset_id: str
    evaluation_date: date | None
    value: Decimal
    currency: str = DEFAULT_CURRENCY
