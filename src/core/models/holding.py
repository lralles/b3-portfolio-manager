from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Holding:
    holding_id: str
    holding_name: str
