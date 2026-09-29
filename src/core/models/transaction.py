from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Mapping


class IOFlow(StrEnum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"


class TransactionOperationType(StrEnum):
    PURCHASE = "purchase"
    DIVIDEND = "dividend"
    INTEREST_ON_EQUITY = "interest_on_equity"
    INCOME = "income"
    TRANSFER = "transfer"
    SALE = "sale"
    INCORPORATION = "incorporation"
    REDEMPTION = "redemption"
    FRACTION_SETTLEMENT = "fraction_settlement"


def parse_decimal(value: str) -> Decimal | None:
    value = value.strip()
    if not value or value == "-":
        return None
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal value: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class Transaction:
    transaction_id: str
    io_flow: IOFlow
    date: date
    operation_type: TransactionOperationType
    asset_id: str
    holding_id: str
    quantity: Decimal | None
    unit_price: Decimal | None
    operation_value: Decimal | None
    corporate_action_id: str | None = None
    corporate_action_related_asset_id: str | None = None

    @classmethod
    def from_store_row(cls, row: Mapping[str, str]) -> Transaction:
        try:
            transaction_id = row["transaction_id"].strip()
            io_flow = IOFlow(row["io_flow"])
            operation_type = TransactionOperationType(row["operation_type"])
            transaction_date = date.fromisoformat(row["date"])
            asset_id = row["asset_id"].strip()
            holding_id = row["holding_id"].strip()
        except KeyError as exc:
            raise ValueError(f"Missing stored transaction field: {exc.args[0]}") from exc
        except ValueError as exc:
            raise ValueError(
                f"Invalid stored transaction enum or date: "
                f"{row.get('io_flow')!r}, {row.get('operation_type')!r}, "
                f"{row.get('date')!r}"
            ) from exc

        if not asset_id:
            raise ValueError("Stored transaction has an empty asset_id")
        if not holding_id:
            raise ValueError("Stored transaction has an empty holding_id")
        if not transaction_id:
            raise ValueError("Stored transaction has an empty transaction_id")

        return cls(
            transaction_id=transaction_id,
            io_flow=io_flow,
            date=transaction_date,
            operation_type=operation_type,
            asset_id=asset_id,
            holding_id=holding_id,
            quantity=parse_decimal(row["quantity"]),
            unit_price=parse_decimal(row["unit_price"]),
            operation_value=parse_decimal(row["operation_value"]),
            corporate_action_id=row.get("corporate_action_id", "").strip() or None,
            corporate_action_related_asset_id=row.get(
                "corporate_action_related_asset_id", ""
            ).strip()
            or None,
        )
