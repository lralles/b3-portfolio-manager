from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class SourcePosition:
    evaluation_date: date
    asset_id: str | None
    asset_name: str
    quantity: Decimal
