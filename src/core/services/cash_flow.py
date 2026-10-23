from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable

from ..models.transaction import IOFlow, Transaction, TransactionOperationType


# These operations realize value from the investment position.  Their source
# direction can be ``credito`` in the B3 export, but they are still position
# outflows: the asset/value is leaving the position.
POSITION_OUTFLOW_OPERATION_TYPES = {
    TransactionOperationType.DIVIDEND,
    TransactionOperationType.INTEREST_ON_EQUITY,
    TransactionOperationType.INCOME,
    TransactionOperationType.SALE,
    TransactionOperationType.REDEMPTION,
    TransactionOperationType.FRACTION_AUCTION,
}


@dataclass(frozen=True, slots=True)
class MonthlyCashFlow:
    month: date
    inflow: Decimal
    outflow: Decimal
    net: Decimal
    transaction_count: int


@dataclass(frozen=True, slots=True)
class DailyCashFlow:
    date: date
    inflow: Decimal
    outflow: Decimal
    net: Decimal
    transaction_count: int


def calculate_monthly_cash_flow(
    transactions: Iterable[Transaction],
) -> list[MonthlyCashFlow]:
    transactions = list(transactions)
    if not transactions:
        return []

    first_month = min(transaction.date for transaction in transactions).replace(day=1)
    last_month = max(transaction.date for transaction in transactions).replace(day=1)
    totals: dict[date, list[Decimal | int]] = {}

    month = first_month
    while month <= last_month:
        totals[month] = [Decimal("0"), Decimal("0"), 0]
        month = next_month(month)

    for transaction in transactions:
        month = transaction.date.replace(day=1)
        totals[month][2] += 1
        inflow, outflow = _cash_flow_components(transaction)
        totals[month][0] += inflow
        totals[month][1] += outflow

    return [
        MonthlyCashFlow(
            month=month,
            inflow=totals[month][0],
            outflow=totals[month][1],
            net=totals[month][0] - totals[month][1],
            transaction_count=totals[month][2],
        )
        for month in sorted(totals)
    ]


def calculate_daily_cash_flow(
    transactions: Iterable[Transaction],
) -> list[DailyCashFlow]:
    """Calculate normalized I/O totals for each date with transactions."""
    totals: dict[date, list[Decimal | int]] = {}
    for transaction in transactions:
        if transaction.date not in totals:
            totals[transaction.date] = [Decimal("0"), Decimal("0"), 0]

        totals[transaction.date][2] += 1
        inflow, outflow = _cash_flow_components(transaction)
        totals[transaction.date][0] += inflow
        totals[transaction.date][1] += outflow

    return [
        DailyCashFlow(
            date=flow_date,
            inflow=values[0],
            outflow=values[1],
            net=values[0] - values[1],
            transaction_count=values[2],
        )
        for flow_date, values in sorted(totals.items())
    ]


def _cash_flow_components(transaction: Transaction) -> tuple[Decimal, Decimal]:
    value = transaction.operation_value
    if value is None:
        return Decimal("0"), Decimal("0")

    if (
        transaction.operation_type not in POSITION_OUTFLOW_OPERATION_TYPES
        and transaction.io_flow is IOFlow.INFLOW
    ):
        return value, Decimal("0")
    return Decimal("0"), value


def next_month(month: date) -> date:
    if month.month == 12:
        return date(month.year + 1, 1, 1)
    return date(month.year, month.month + 1, 1)
