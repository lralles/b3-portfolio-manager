from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping


def parse_position_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid position decimal value: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class Position:
    """The current holding for an asset within an account."""

    asset_id: str
    account_id: str
    quantity: Decimal
    invested_capital: Decimal

    @property
    def key(self) -> tuple[str, str]:
        return self.asset_id, self.account_id

    @property
    def total_invested_capital(self) -> Decimal:
        return self.invested_capital

    @classmethod
    def from_store_row(cls, row: Mapping[str, str]) -> Position:
        try:
            asset_id = row["asset_id"].strip()
            account_id = row["account_id"].strip()
            quantity = parse_position_decimal(row["quantity"])
            invested_capital = parse_position_decimal(row["invested_capital"])
        except KeyError as exc:
            raise ValueError(f"Missing stored position field: {exc.args[0]}") from exc

        if not asset_id or not account_id:
            raise ValueError("Stored position must have asset_id and account_id")

        return cls(asset_id, account_id, quantity, invested_capital)

    def to_store_row(self) -> dict[str, str]:
        return {
            "asset_id": self.asset_id,
            "account_id": self.account_id,
            "quantity": format(self.quantity, "f"),
            "invested_capital": format(self.invested_capital, "f"),
        }


POSITION_COLUMNS = ["asset_id", "account_id", "quantity", "invested_capital"]
