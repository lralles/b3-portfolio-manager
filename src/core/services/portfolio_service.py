from __future__ import annotations

from datetime import date
from decimal import Decimal

from ..models.portfolio import Portfolio
from ..models.portfolio_value import PortfolioValue
from ..repositories.transaction_repository import TransactionRepository
from .position_service import PositionService
from .position_value_service import PositionValueService


class PortfolioService:
    """Builds a portfolio by valuing every stored position."""

    def __init__(
        self,
        position_service: PositionService | None = None,
        position_value_service: PositionValueService | None = None,
        transaction_repository: TransactionRepository | None = None,
    ) -> None:
        self.position_service = position_service or PositionService()
        self.position_value_service = (
            position_value_service or PositionValueService()
        )
        self.transaction_repository = transaction_repository or TransactionRepository()

    def get(
        self, price_date: date, reference_date: date | None = None
    ) -> Portfolio:
        positions = self.position_service.all(reference_date)
        position_values = []
        for position in positions:
            position_value = self.position_value_service.get(position, price_date)
            position_values.append(position_value)
        return Portfolio(tuple(position_values))

    def get_over_time(self) -> list[PortfolioValue]:
        """Return only the total value on every relevant date."""
        transaction_dates = {
            transaction.date for transaction in self.transaction_repository.all()
        }
        trading_price_dates = {
            trading_price.evaluation_date
            for trading_price in self.position_value_service.trading_price_repository.all()
        }
        evaluation_dates = sorted(transaction_dates | trading_price_dates)
        return [
            self.get_value(evaluation_date, evaluation_date)
            for evaluation_date in evaluation_dates
        ]

    def get_value(
        self, price_date: date, reference_date: date | None = None
    ) -> PortfolioValue:
        """Return the total portfolio value without retaining position details."""
        positions = self.position_service.all(reference_date)
        total = sum(
            (
                self.position_value_service.get(position, price_date).value
                for position in positions
            ),
            start=Decimal("0"),
        )
        return PortfolioValue(price_date, total)

    def build(self, price_date: date) -> Portfolio:
        """Alias for callers that prefer the construction operation's name."""
        return self.get(price_date)
