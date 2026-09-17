from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Asset:
    asset_id: str
    asset_name: str
    isin: str | None = None
