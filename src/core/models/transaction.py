from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Mapping


class TransactionDirection(StrEnum):
    CREDIT = "credit"
    DEBIT = "debit"


class IOFlow(StrEnum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"


class TransactionOperationType(StrEnum):
    PURCHASE = "purchase"
    DIVIDEND = "dividend"
    INTEREST_ON_EQUITY = "interest_on_equity"
    INCOME = "income"
    TRANSFER = "transfer"
    SETTLEMENT_TRANSFER = "settlement_transfer"
    SALE = "sale"


SOURCE_DIRECTION_MAP = {
    "credito": TransactionDirection.CREDIT,
    "debito": TransactionDirection.DEBIT,
}

SOURCE_OPERATION_TYPE_MAP = {
    "compra": TransactionOperationType.PURCHASE,
    "dividendo": TransactionOperationType.DIVIDEND,
    "juros sobre capital próprio": TransactionOperationType.INTEREST_ON_EQUITY,
    "rendimento": TransactionOperationType.INCOME,
    "transferência": TransactionOperationType.TRANSFER,
    "transferência - liquidação": TransactionOperationType.SETTLEMENT_TRANSFER,
    "venda": TransactionOperationType.SALE,
}

OPERATION_TYPES_WITH_OUTFLOW = {
    TransactionOperationType.DIVIDEND,
    TransactionOperationType.INTEREST_ON_EQUITY,
}


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
    direction: TransactionDirection
    date: date
    operation_type: TransactionOperationType
    asset_id: str
    account_id: str
    quantity: Decimal | None
    unit_price: Decimal | None
    operation_value: Decimal | None

    @property
    def io_flow(self) -> IOFlow:
        if self.operation_type in OPERATION_TYPES_WITH_OUTFLOW:
            return IOFlow.OUTFLOW
        return IOFlow.INFLOW if self.direction is TransactionDirection.CREDIT else IOFlow.OUTFLOW

    @classmethod
    def from_store_row(cls, row: Mapping[str, str]) -> Transaction:
        try:
            direction = TransactionDirection(row["direction"])
            operation_type = TransactionOperationType(row["operation_type"])
            transaction_date = date.fromisoformat(row["date"])
            asset_id = row["asset_id"].strip()
            account_id = row["account_id"].strip()
        except KeyError as exc:
            raise ValueError(f"Missing stored transaction field: {exc.args[0]}") from exc
        except ValueError as exc:
            raise ValueError(
                f"Invalid stored transaction enum or date: "
                f"{row.get('direction')!r}, {row.get('operation_type')!r}, "
                f"{row.get('date')!r}"
            ) from exc

        if not asset_id:
            raise ValueError("Stored transaction has an empty asset_id")
        if not account_id:
            raise ValueError("Stored transaction has an empty account_id")

        return cls(
            direction=direction,
            date=transaction_date,
            operation_type=operation_type,
            asset_id=asset_id,
            account_id=account_id,
            quantity=parse_decimal(row["quantity"]),
            unit_price=parse_decimal(row["unit_price"]),
            operation_value=parse_decimal(row["operation_value"]),
        )

    @classmethod
    def from_sanitized_row(
        cls, row: Mapping[str, str], asset_id: str, account_id: str
    ) -> Transaction:
        try:
            direction_value = row["entrada_saida"].strip().lower()
            operation_value = row["movimentacao"].strip().lower()
            date_value = row["data"].strip()
        except KeyError as exc:
            raise ValueError(f"Missing sanitized transaction field: {exc.args[0]}") from exc

        try:
            direction = SOURCE_DIRECTION_MAP[direction_value]
        except KeyError as exc:
            raise ValueError(f"Unknown transaction direction: {direction_value!r}") from exc

        try:
            operation_type = SOURCE_OPERATION_TYPE_MAP[operation_value]
        except KeyError as exc:
            raise ValueError(f"Unknown transaction operation type: {operation_value!r}") from exc

        try:
            transaction_date = date.fromisoformat(date_value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid transaction date: {date_value!r}"
            ) from exc

        return cls(
            direction=direction,
            date=transaction_date,
            operation_type=operation_type,
            asset_id=asset_id,
            account_id=account_id,
            quantity=parse_decimal(row["quantidade"]),
            unit_price=parse_decimal(row["preco_unitario"]),
            operation_value=parse_decimal(row["valor_operacao"]),
        )

    def to_formatted_row(self) -> dict[str, str]:
        return {
            "direction": self.direction.value,
            "date": self.date.isoformat(),
            "operation_type": self.operation_type.value,
            "asset_id": self.asset_id,
            "account_id": self.account_id,
            "quantity": format_decimal(self.quantity),
            "unit_price": format_decimal(self.unit_price),
            "operation_value": format_decimal(self.operation_value),
        }


def format_decimal(value: Decimal | None) -> str:
    return "" if value is None else format(value, "f")


FORMATTED_COLUMNS = [
    "direction",
    "date",
    "operation_type",
    "asset_id",
    "account_id",
    "quantity",
    "unit_price",
    "operation_value",
]
