from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .position_conflict import PositionConflict


ReconciliationStatus = Literal["success", "error"]


@dataclass(frozen=True, slots=True)
class PortfolioReconciliationStatus:
    status: ReconciliationStatus
    conflicts: list[PositionConflict]

