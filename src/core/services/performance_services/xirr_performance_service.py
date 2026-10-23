from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from ...models.transaction import IOFlow, Transaction
from ...repositories.transaction_repository import TransactionRepository
from ..portfolio_service import PortfolioService


@dataclass(frozen=True, slots=True)
class XirrPerformance:
    """The cash flows and XIRR for one portfolio period."""

    start_date: date
    end_date: date
    start_value: Decimal
    end_value: Decimal
    cash_flows: tuple[tuple[date, Decimal], ...]
    xirr: float


class XirrPerformanceService:
    """Calculates money-weighted portfolio performance using dated cash flows."""

    def __init__(
        self,
        portfolio_service: PortfolioService | None = None,
        transaction_repository: TransactionRepository | None = None,
    ) -> None:
        self.transaction_repository = transaction_repository or TransactionRepository()
        self.portfolio_service = portfolio_service or PortfolioService(
            transaction_repository=self.transaction_repository
        )

    def calculate(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> XirrPerformance:
        transactions = self.transaction_repository.all()
        if not transactions:
            raise ValueError("No transactions are available to calculate XIRR.")

        first_transaction_date = min(transaction.date for transaction in transactions)
        start_date = start_date or first_transaction_date
        end_date = end_date or self._latest_available_date(transactions)
        if start_date >= end_date:
            raise ValueError("XIRR requires start_date to be before end_date.")

        period_transactions = [
            transaction
            for transaction in transactions
            if start_date <= transaction.date <= end_date
        ]
        start_value = self.portfolio_service.get_value(
            price_date=start_date - timedelta(days=1),
            reference_date=start_date - timedelta(days=1),
        ).value
        end_value = self.portfolio_service.get_value(
            price_date=end_date,
            reference_date=end_date,
        ).value

        cash_flows = [(start_date, -start_value)]
        cash_flows.extend(_cash_flows(period_transactions))
        cash_flows.append((end_date, end_value))
        cash_flows = _aggregate_cash_flows(cash_flows)
        xirr = _calculate_xirr(cash_flows)
        return XirrPerformance(
            start_date=start_date,
            end_date=end_date,
            start_value=start_value,
            end_value=end_value,
            cash_flows=tuple(cash_flows),
            xirr=xirr,
        )

    def _latest_available_date(self, transactions: list[Transaction]) -> date:
        dates = [transaction.date for transaction in transactions]
        position_value_service = getattr(
            self.portfolio_service, "position_value_service", None
        )
        trading_price_repository = getattr(
            position_value_service, "trading_price_repository", None
        )
        if trading_price_repository is not None:
            dates.extend(
                trading_price.evaluation_date
                for trading_price in trading_price_repository.all()
                if trading_price.evaluation_date is not None
            )
        return max(dates)


def _cash_flows(transactions: list[Transaction]) -> list[tuple[date, Decimal]]:
    cash_flows = []
    for transaction in transactions:
        if transaction.operation_value is None:
            continue
        # IOFlow describes the portfolio direction. Investor cash flows use
        # the opposite sign: an asset entering the portfolio is an investment.
        sign = -1 if transaction.io_flow is IOFlow.INFLOW else 1
        cash_flows.append((transaction.date, sign * transaction.operation_value))
    return cash_flows


def _aggregate_cash_flows(
    cash_flows: list[tuple[date, Decimal]],
) -> list[tuple[date, Decimal]]:
    totals: dict[date, Decimal] = {}
    for flow_date, value in cash_flows:
        totals[flow_date] = totals.get(flow_date, Decimal("0")) + value
    return sorted(totals.items())


def _calculate_xirr(cash_flows: list[tuple[date, Decimal]]) -> float:
    if not cash_flows or not any(value < 0 for _, value in cash_flows):
        raise ValueError("XIRR requires at least one negative cash flow.")
    if not any(value > 0 for _, value in cash_flows):
        raise ValueError("XIRR requires at least one positive cash flow.")

    start_date = cash_flows[0][0]
    values = [
        (float(value), (flow_date - start_date).days / 365.0)
        for flow_date, value in cash_flows
    ]

    def npv(rate: float) -> float:
        return sum(value / (1 + rate) ** years for value, years in values)

    lower = -0.999999999
    lower_value = npv(lower)
    upper = 1.0
    upper_value = npv(upper)
    while lower_value * upper_value > 0 and upper < 1_000_000:
        upper *= 2
        upper_value = npv(upper)
    if lower_value * upper_value > 0:
        raise ValueError("Unable to find an XIRR solution for the cash flows.")

    for _ in range(200):
        midpoint = (lower + upper) / 2
        midpoint_value = npv(midpoint)
        if abs(midpoint_value) < 1e-10:
            return midpoint
        if lower_value * midpoint_value <= 0:
            upper, upper_value = midpoint, midpoint_value
        else:
            lower, lower_value = midpoint, midpoint_value
    return (lower + upper) / 2
