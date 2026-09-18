from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AssetType(str, Enum):
    STOCKS = "stocks"
    FII = "fii"
    TREASURY_BOND = "treasury_bond"


@dataclass(frozen=True, slots=True)
class Asset:
    asset_id: str
    asset_name: str
    isin: str | None = None
    asset_type: AssetType | None = None
