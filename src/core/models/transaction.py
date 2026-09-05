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


SOURCE_IO_FLOW_MAP = {
    "credito": IOFlow.INFLOW,
    "debito": IOFlow.OUTFLOW,
}

SOURCE_OPERATION_TYPE_MAP = {
    "compra": TransactionOperationType.PURCHASE,
    "dividendo": TransactionOperationType.DIVIDEND,
    "juros sobre capital próprio": TransactionOperationType.INTEREST_ON_EQUITY,
    "rendimento": TransactionOperationType.INCOME,
    "transferência": TransactionOperationType.TRANSFER,
    "venda": TransactionOperationType.SALE,
}

SOURCE_SETTLEMENT_TRANSFER = "transferência - liquidação"

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
    io_flow: IOFlow
    date: date
    operation_type: TransactionOperationType
    asset_id: str
    account_id: str
    quantity: Decimal | None
    unit_price: Decimal | None
    operation_value: Decimal | None

    @classmethod
    def from_store_row(cls, row: Mapping[str, str]) -> Transaction:
        try:
            io_flow = IOFlow(row["io_flow"])
            operation_type = TransactionOperationType(row["operation_type"])
            transaction_date = date.fromisoformat(row["date"])
            asset_id = row["asset_id"].strip()
            account_id = row["account_id"].strip()
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
        if not account_id:
            raise ValueError("Stored transaction has an empty account_id")

        return cls(
            io_flow=io_flow,
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
            io_flow = SOURCE_IO_FLOW_MAP[direction_value]
        except KeyError as exc:
            raise ValueError(f"Unknown transaction direction: {direction_value!r}") from exc

        if operation_value == SOURCE_SETTLEMENT_TRANSFER:
            operation_type = (
                TransactionOperationType.PURCHASE
                if io_flow is IOFlow.INFLOW
                else TransactionOperationType.SALE
            )
        else:
            try:
                operation_type = SOURCE_OPERATION_TYPE_MAP[operation_value]
            except KeyError as exc:
                raise ValueError(
                    f"Unknown transaction operation type: {operation_value!r}"
                ) from exc

        if operation_type in OPERATION_TYPES_WITH_OUTFLOW:
            io_flow = IOFlow.OUTFLOW

        try:
            transaction_date = date.fromisoformat(date_value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid transaction date: {date_value!r}"
            ) from exc

        return cls(
            io_flow=io_flow,
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
            "io_flow": self.io_flow.value,
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
    "io_flow",
    "date",
    "operation_type",
    "asset_id",
    "account_id",
    "quantity",
    "unit_price",
    "operation_value",
]
