from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable

from ..models.transaction import IOFlow, Transaction


@dataclass(frozen=True, slots=True)
class MonthlyCashFlow:
    month: date
    inflow: Decimal
    outflow: Decimal
    net: Decimal
    transaction_count: int

    def to_row(self) -> dict[str, str | int]:
        return {
            "month": self.month.isoformat(),
            "inflow": format(self.inflow, "f"),
            "outflow": format(self.outflow, "f"),
            "net": format(self.net, "f"),
            "transaction_count": self.transaction_count,
        }


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
        value = transaction.operation_value
        if value is None:
            continue

        if transaction.io_flow is IOFlow.INFLOW:
            totals[month][0] += value
        else:
            totals[month][1] += value

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


def next_month(month: date) -> date:
    if month.month == 12:
        return date(month.year + 1, 1, 1)
    return date(month.year, month.month + 1, 1)
