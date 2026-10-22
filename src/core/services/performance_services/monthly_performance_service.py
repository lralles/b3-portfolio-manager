from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ...models.transaction import Transaction
from ...repositories.transaction_repository import TransactionRepository
from ..cash_flow import calculate_monthly_cash_flow, next_month
from ..portfolio_service import PortfolioService


@dataclass(frozen=True, slots=True)
class MonthlyPerformance:
    """Performance and inputs for one calendar month."""

    month: date
    start_month_end: date
    end_month_end: date
    start_value: Decimal
    inflow: Decimal
    outflow: Decimal
    net_io: Decimal
    end_value: Decimal
    performance: Decimal | None


class MonthlyPerformanceService:
    """Calculates portfolio performance between consecutive month ends."""

    def __init__(
        self,
        portfolio_service: PortfolioService | None = None,
        transaction_repository: TransactionRepository | None = None,
    ) -> None:
        self.transaction_repository = transaction_repository or TransactionRepository()
        self.portfolio_service = portfolio_service or PortfolioService(
            transaction_repository=self.transaction_repository
        )

    def calculate(self) -> list[MonthlyPerformance]:
        transactions = self.transaction_repository.all()
        if not transactions:
            return []

        month_ends = _month_ends(transactions)
        portfolio_values = {
            month_end: self.portfolio_service.get_value(
                price_date=month_end,
                reference_date=month_end,
            ).value
            for month_end in month_ends
        }
        cash_flow_by_month = {
            flow.month: flow
            for flow in calculate_monthly_cash_flow(transactions)
        }

        performance = []
        for start_month_end, end_month_end in zip(month_ends, month_ends[1:]):
            month = end_month_end.replace(day=1)
            flow = cash_flow_by_month.get(month)
            inflow = flow.inflow if flow else Decimal("0")
            outflow = flow.outflow if flow else Decimal("0")
            net_io = inflow - outflow
            start_value = portfolio_values[start_month_end]
            end_value = portfolio_values[end_month_end]
            monthly_performance = (
                None
                if start_value == 0
                else (end_value - net_io) / start_value - 1
            )
            performance.append(
                MonthlyPerformance(
                    month=month,
                    start_month_end=start_month_end,
                    end_month_end=end_month_end,
                    start_value=start_value,
                    inflow=inflow,
                    outflow=outflow,
                    net_io=net_io,
                    end_value=end_value,
                    performance=monthly_performance,
                )
            )
        return performance


def _month_ends(transactions: list[Transaction]) -> list[date]:
    first_month = min(transaction.date for transaction in transactions).replace(day=1)
    last_month = max(transaction.date for transaction in transactions).replace(day=1)
    month_ends = []
    month = first_month
    while month <= last_month:
        month_ends.append(
            month.replace(day=calendar.monthrange(month.year, month.month)[1])
        )
        month = next_month(month)
    return month_ends
