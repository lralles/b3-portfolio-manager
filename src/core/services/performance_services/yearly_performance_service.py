from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ...models.transaction import Transaction
from ...repositories.transaction_repository import TransactionRepository
from ..cash_flow import calculate_monthly_cash_flow
from ..portfolio_service import PortfolioService


@dataclass(frozen=True, slots=True)
class YearlyPerformance:
    """Performance and inputs for one calendar year."""

    year: date
    start_year_end: date
    end_year_end: date
    start_value: Decimal
    inflow: Decimal
    outflow: Decimal
    net_io: Decimal
    end_value: Decimal
    performance: Decimal | None


class YearlyPerformanceService:
    """Calculates portfolio performance between consecutive year ends."""

    def __init__(
        self,
        portfolio_service: PortfolioService | None = None,
        transaction_repository: TransactionRepository | None = None,
    ) -> None:
        self.transaction_repository = transaction_repository or TransactionRepository()
        self.portfolio_service = portfolio_service or PortfolioService(
            transaction_repository=self.transaction_repository
        )

    def calculate(self) -> list[YearlyPerformance]:
        transactions = self.transaction_repository.all()
        if not transactions:
            return []

        year_ends = _year_ends(transactions)
        portfolio_values = {
            year_end: self.portfolio_service.get_value(
                price_date=year_end,
                reference_date=year_end,
            ).value
            for year_end in year_ends
        }
        yearly_cash_flow = _yearly_cash_flow(transactions)

        performance = []
        for start_year_end, end_year_end in zip(year_ends, year_ends[1:]):
            year = end_year_end.replace(month=1, day=1)
            inflow, outflow = yearly_cash_flow.get(
                year.year, (Decimal("0"), Decimal("0"))
            )
            net_io = inflow - outflow
            start_value = portfolio_values[start_year_end]
            end_value = portfolio_values[end_year_end]
            yearly_performance = (
                None
                if start_value == 0
                else (end_value - net_io) / start_value - 1
            )
            performance.append(
                YearlyPerformance(
                    year=year,
                    start_year_end=start_year_end,
                    end_year_end=end_year_end,
                    start_value=start_value,
                    inflow=inflow,
                    outflow=outflow,
                    net_io=net_io,
                    end_value=end_value,
                    performance=yearly_performance,
                )
            )
        return performance


def _year_ends(transactions: list[Transaction]) -> list[date]:
    first_year = min(transaction.date for transaction in transactions).year
    last_year = max(transaction.date for transaction in transactions).year
    return [
        date(year, 12, 31)
        for year in range(first_year, last_year + 1)
    ]


def _yearly_cash_flow(
    transactions: list[Transaction],
) -> dict[int, tuple[Decimal, Decimal]]:
    totals: dict[int, list[Decimal]] = {}
    for flow in calculate_monthly_cash_flow(transactions):
        year = flow.month.year
        if year not in totals:
            totals[year] = [Decimal("0"), Decimal("0")]
        totals[year][0] += flow.inflow
        totals[year][1] += flow.outflow
    return {year: (values[0], values[1]) for year, values in totals.items()}
