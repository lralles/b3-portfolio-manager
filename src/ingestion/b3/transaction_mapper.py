from __future__ import annotations

from datetime import date
from typing import Mapping

from ...core.models.transaction import (
    IOFlow,
    Transaction,
    TransactionOperationType,
    parse_decimal,
)


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


def transaction_from_sanitized_row(
    row: Mapping[str, str], asset_id: str, holding_id: str
) -> Transaction:
    """Map one sanitized B3 row to the canonical transaction model."""
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
        raise ValueError(f"Invalid transaction date: {date_value!r}") from exc

    return Transaction(
        io_flow=io_flow,
        date=transaction_date,
        operation_type=operation_type,
        asset_id=asset_id,
        holding_id=holding_id,
        quantity=parse_decimal(row["quantidade"]),
        unit_price=parse_decimal(row["preco_unitario"]),
        operation_value=parse_decimal(row["valor_operacao"]),
    )
