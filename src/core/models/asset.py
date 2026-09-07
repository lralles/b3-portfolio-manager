from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class Asset:
    asset_id: str
    asset_name: str

    @classmethod
    def from_store_row(cls, row: Mapping[str, str]) -> Asset:
        try:
            asset_id = row["asset_id"].strip()
            asset_name = row["asset_name"].strip()
        except KeyError as exc:
            raise ValueError(f"Missing stored asset field: {exc.args[0]}") from exc

        if not asset_id:
            raise ValueError("Stored asset has an empty asset_id")
        if not asset_name:
            raise ValueError(f"Stored asset {asset_id!r} has an empty asset_name")

        return cls(asset_id=asset_id, asset_name=asset_name)
