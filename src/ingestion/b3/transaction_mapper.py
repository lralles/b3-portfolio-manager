from __future__ import annotations

from datetime import date
from decimal import Decimal
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
    "bonificação em ativos": TransactionOperationType.ASSET_BONUS,
    "desdobro": TransactionOperationType.ASSET_SPLIT,
    "dividendo": TransactionOperationType.DIVIDEND,
    "dividendo - transferido": TransactionOperationType.DIVIDEND,
    "juros sobre capital próprio": TransactionOperationType.INTEREST_ON_EQUITY,
    "juros sobre capital próprio - transferido": TransactionOperationType.INTEREST_ON_EQUITY,
    "rendimento": TransactionOperationType.INCOME,
    "direito de subscrição": TransactionOperationType.SUBSCRIPTION_RIGHT_GRANT,
    "transferência": TransactionOperationType.TRANSFER,
    "cessão de direitos": TransactionOperationType.RIGHTS_TRANSFER,
    "cessão de direitos - solicitada": TransactionOperationType.SUBSCRIPTION_RIGHT_DISPOSAL,
    "evento em dinheiro - transferido": TransactionOperationType.CASH_EVENT_TRANSFER,
    "venda": TransactionOperationType.SALE,
    "direitos de subscrição - não exercido": TransactionOperationType.SUBSCRIPTION_RIGHT_EXPIRY,
    "leilão de fração": TransactionOperationType.FRACTION_AUCTION,
    "incorporação": TransactionOperationType.INCORPORATION,
    "resgate": TransactionOperationType.REDEMPTION,
    "vencimento": TransactionOperationType.REDEMPTION,
    "fração em ativos": TransactionOperationType.FRACTION_SETTLEMENT,
}

SOURCE_SETTLEMENT_TRANSFER = "transferência - liquidação"
SOURCE_BUY_SELL = "compra / venda"

POSITION_OUTFLOW_OPERATION_TYPES = {
    TransactionOperationType.SALE,
    TransactionOperationType.DIVIDEND,
    TransactionOperationType.INTEREST_ON_EQUITY,
    TransactionOperationType.INCOME,
    TransactionOperationType.REDEMPTION,
    TransactionOperationType.FRACTION_AUCTION,
}

def transaction_from_sanitized_row(
    row: Mapping[str, str], transaction_id: str, asset_id: str, holding_id: str
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

    if operation_value in (SOURCE_SETTLEMENT_TRANSFER, SOURCE_BUY_SELL):
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

    if operation_type in POSITION_OUTFLOW_OPERATION_TYPES:
        io_flow = IOFlow.OUTFLOW
    elif operation_type is TransactionOperationType.PURCHASE:
        io_flow = IOFlow.INFLOW

    try:
        transaction_date = date.fromisoformat(date_value)
    except ValueError as exc:
        raise ValueError(f"Invalid transaction date: {date_value!r}") from exc

    quantity = parse_decimal(row["quantidade"])
    unit_price = parse_decimal(row["preco_unitario"])
    operation_amount = parse_decimal(row["valor_operacao"])
    if operation_value == "vencimento" and (
        unit_price is None
        or unit_price <= Decimal("0")
        or operation_amount is None
        or operation_amount <= Decimal("0")
    ):
        raise ValueError(
            "VENCIMENTO transaction is missing a positive price: "
            f"{transaction_id!r}"
        )

    return Transaction(
        transaction_id=transaction_id,
        io_flow=io_flow,
        date=transaction_date,
        operation_type=operation_type,
        asset_id=asset_id,
        holding_id=holding_id,
        quantity=quantity,
        unit_price=unit_price,
        operation_value=operation_amount,
    )
