from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ...repositories.transaction_repository import TransactionRepository
from ..cash_flow import calculate_daily_cash_flow
from ..portfolio_service import PortfolioService


@dataclass(frozen=True, slots=True)
class RunningPerformance:
    """Performance and inputs for one consecutive observation interval."""

    previous_date: date
    date: date
    start_value: Decimal
    inflow: Decimal
    outflow: Decimal
    net_io: Decimal
    end_value: Decimal
    period_performance: Decimal | None
    performance: Decimal | None


class RunningPerformanceService:
    """Calculates continuously compounded performance over relevant dates.

    Relevant dates are the transaction and trading-price dates returned by the
    portfolio service. Each interval return removes the net I/O recorded on
    its ending date before the interval returns are compounded.
    """

    def __init__(
        self,
        portfolio_service: PortfolioService | None = None,
        transaction_repository: TransactionRepository | None = None,
    ) -> None:
        self.transaction_repository = transaction_repository or TransactionRepository()
        self.portfolio_service = portfolio_service or PortfolioService(
            transaction_repository=self.transaction_repository
        )

    def calculate(self) -> list[RunningPerformance]:
        portfolio_history = self.portfolio_service.get_over_time()
        if len(portfolio_history) < 2:
            return []

        cash_flow_by_date = {
            flow.date: flow
            for flow in calculate_daily_cash_flow(self.transaction_repository.all())
        }

        performance: list[RunningPerformance] = []
        running_performance: Decimal | None = None
        for previous, current in zip(portfolio_history, portfolio_history[1:]):
            flow = cash_flow_by_date.get(current.evaluation_date)
            inflow = flow.inflow if flow else Decimal("0")
            outflow = flow.outflow if flow else Decimal("0")
            net_io = inflow - outflow
            period_performance = _calculate_return(
                start_value=previous.value,
                net_io=net_io,
                end_value=current.value,
            )
            if period_performance is not None:
                running_performance = (
                    period_performance
                    if running_performance is None
                    else (Decimal("1") + running_performance)
                    * (Decimal("1") + period_performance)
                    - Decimal("1")
                )

            performance.append(
                RunningPerformance(
                    previous_date=previous.evaluation_date,
                    date=current.evaluation_date,
                    start_value=previous.value,
                    inflow=inflow,
                    outflow=outflow,
                    net_io=net_io,
                    end_value=current.value,
                    period_performance=period_performance,
                    performance=running_performance,
                )
            )
        return performance


def _calculate_return(
    start_value: Decimal,
    net_io: Decimal,
    end_value: Decimal,
) -> Decimal | None:
    if start_value == 0:
        return None
    return (end_value - net_io) / start_value - Decimal("1")
