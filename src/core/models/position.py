from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping

from .asset import Asset


def parse_position_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid position decimal value: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class Position:
    """The consolidated position for an asset across all holdings."""

    asset_id: str
    current_quantity: Decimal
    total_acquired_quantity: Decimal
    total_sold_quantity: Decimal
    invested_capital: Decimal
    asset: Asset | None = None

    @property
    def key(self) -> str:
        return self.asset_id

    def with_asset(self, asset: Asset) -> Position:
        if asset.asset_id != self.asset_id:
            raise ValueError(
                f"Asset {asset.asset_id!r} does not match position {self.asset_id!r}"
            )
        return Position(
            asset_id=self.asset_id,
            current_quantity=self.current_quantity,
            total_acquired_quantity=self.total_acquired_quantity,
            total_sold_quantity=self.total_sold_quantity,
            invested_capital=self.invested_capital,
            asset=asset,
        )

    @classmethod
    def from_store_row(cls, row: Mapping[str, str]) -> Position:
        try:
            asset_id = row["asset_id"].strip()
            current_quantity = parse_position_decimal(row["current_quantity"])
            total_acquired_quantity = parse_position_decimal(
                row["total_acquired_quantity"]
            )
            total_sold_quantity = parse_position_decimal(row["total_sold_quantity"])
            invested_capital = parse_position_decimal(row["invested_capital"])
        except KeyError as exc:
            raise ValueError(f"Missing stored position field: {exc.args[0]}") from exc

        if not asset_id:
            raise ValueError("Stored position has an empty asset_id")

        return cls(
            asset_id,
            current_quantity,
            total_acquired_quantity,
            total_sold_quantity,
            invested_capital,
        )

    def to_store_row(self) -> dict[str, str]:
        return {
            "asset_id": self.asset_id,
            "current_quantity": format(self.current_quantity, "f"),
            "total_acquired_quantity": format(self.total_acquired_quantity, "f"),
            "total_sold_quantity": format(self.total_sold_quantity, "f"),
            "invested_capital": format(self.invested_capital, "f"),
        }


POSITION_COLUMNS = [
    "asset_id",
    "current_quantity",
    "total_acquired_quantity",
    "total_sold_quantity",
    "invested_capital",
]
