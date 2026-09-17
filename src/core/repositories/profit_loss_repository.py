from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Mapping

from config import Config
from ..models.profit_loss import (
    PROFIT_LOSS_COLUMNS,
    ProfitLoss,
    ProfitLossType,
)


class ProfitLossRepository:
    def __init__(
        self,
        csv_path: Path | None = None,
        config: Config | None = None,
    ) -> None:
        self.config = config or Config()
        self.csv_path = csv_path or self.config.profit_losses_file

    def all(self) -> list[ProfitLoss]:
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            return [_from_store_row(row) for row in csv.DictReader(fh)]

    def save(self, profit_losses: Iterable[ProfitLoss]) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=PROFIT_LOSS_COLUMNS)
            writer.writeheader()
            writer.writerows(_to_store_row(profit_loss) for profit_loss in profit_losses)


def _to_store_row(profit_loss: ProfitLoss) -> dict[str, str]:
    # Only realized profit/loss is currently produced by the position build.
    return {
        "asset_id": profit_loss.asset_id,
        "transaction_id": profit_loss.transaction_id,
        "holding_id": profit_loss.holding_id,
        "value": format(profit_loss.value, "f"),
        "type": ProfitLossType.REALIZED.value,
    }


def _from_store_row(row: Mapping[str, str]) -> ProfitLoss:
    try:
        asset_id = row["asset_id"].strip()
        transaction_id = row["transaction_id"].strip()
        holding_id = row["holding_id"].strip()
        value = _parse_decimal(row["value"])
        profit_loss_type = ProfitLossType(row["type"].strip())
    except KeyError as exc:
        raise ValueError(f"Missing stored profit/loss field: {exc.args[0]}") from exc
    except ValueError as exc:
        raise ValueError("Invalid stored profit/loss type or value") from exc

    for field_name, field_value in (
        ("asset_id", asset_id),
        ("transaction_id", transaction_id),
        ("holding_id", holding_id),
    ):
        if not field_value:
            raise ValueError(f"Stored profit/loss has an empty {field_name}")

    return ProfitLoss(asset_id, transaction_id, holding_id, value, profit_loss_type)


def _parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid profit/loss decimal value: {value!r}") from exc
