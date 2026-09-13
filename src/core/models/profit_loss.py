from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class ProfitLossType(StrEnum):
    REALIZED = "realized"
    NOT_REALIZED = "not_realized"


@dataclass(frozen=True, slots=True)
class ProfitLoss:
    asset_id: str
    transaction_id: str
    holding_id: str
    value: Decimal
    type: ProfitLossType


PROFIT_LOSS_COLUMNS = [
    "asset_id",
    "transaction_id",
    "holding_id",
    "value",
    "type",
]
