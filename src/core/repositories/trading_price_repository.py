from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Mapping

from config import Config
from ..models.trading_price import DEFAULT_CURRENCY, TradingPrice


TRADING_PRICE_COLUMNS = ["asset_id", "evaluation_date", "value", "currency"]


class TradingPriceRepository:
    def __init__(
        self,
        csv_path: Path | None = None,
        config: Config | None = None,
    ) -> None:
        self.config = config or Config()
        self.csv_path = csv_path or self.config.trading_prices_file

    def all(self) -> list[TradingPrice]:
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            return [_from_store_row(row) for row in csv.DictReader(fh)]

    def latest_for_asset_on_or_before(
        self, asset_id: str, price_date: date
    ) -> TradingPrice:
        """Return the latest stored price available on or before a date."""
        available_prices = []
        for trading_price in self.all():
            if trading_price.asset_id != asset_id:
                continue
            if trading_price.evaluation_date > price_date:
                continue
            available_prices.append(trading_price)

        if not available_prices:
            raise ValueError(
                f"No trading price found for asset {asset_id!r} "
                f"on or before {price_date.isoformat()}"
            )

        latest_price = available_prices[0]
        for trading_price in available_prices[1:]:
            if trading_price.evaluation_date > latest_price.evaluation_date:
                latest_price = trading_price
                continue
            if trading_price.evaluation_date == latest_price.evaluation_date:
                raise ValueError(
                    f"Multiple trading prices found for asset {asset_id!r} "
                    f"on {latest_price.evaluation_date.isoformat()}"
                )
        return latest_price

    def save(self, trading_prices: Iterable[TradingPrice]) -> None:
        trading_prices = sorted(
            trading_prices,
            key=lambda trading_price: (
                trading_price.evaluation_date,
                trading_price.asset_id,
            ),
        )
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=TRADING_PRICE_COLUMNS)
            writer.writeheader()
            writer.writerows(_to_store_row(trading_price) for trading_price in trading_prices)


def _from_store_row(row: Mapping[str, str]) -> TradingPrice:
    try:
        asset_id = row["asset_id"].strip()
        evaluation_date = date.fromisoformat(row["evaluation_date"].strip())
        value = _parse_decimal(row["value"])
        currency = row.get("currency", DEFAULT_CURRENCY).strip().upper()
    except KeyError as exc:
        raise ValueError(f"Missing stored trading price field: {exc.args[0]}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid stored trading price: {row!r}") from exc

    if not asset_id:
        raise ValueError("Stored trading price has an empty asset_id")
    if not currency:
        raise ValueError("Stored trading price has an empty currency")

    return TradingPrice(asset_id, evaluation_date, value, currency)


def _to_store_row(trading_price: TradingPrice) -> dict[str, str]:
    return {
        "asset_id": trading_price.asset_id,
        "evaluation_date": trading_price.evaluation_date.isoformat(),
        "value": format(trading_price.value, "f"),
        "currency": trading_price.currency,
    }


def _parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except (AttributeError, InvalidOperation) as exc:
        raise ValueError(f"Invalid trading price decimal value: {value!r}") from exc
