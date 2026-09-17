from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Mapping

from config import Config
from ..models.source_position import SourcePosition


SOURCE_POSITION_COLUMNS = ["evaluation_date", "asset_id", "asset_name", "quantity"]


class SourcePositionRepository:
    def __init__(
        self,
        csv_path: Path | None = None,
        config: Config | None = None,
    ) -> None:
        self.config = config or Config()
        self.csv_path = csv_path or self.config.source_positions_file

    def all(self) -> list[SourcePosition]:
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            return [_from_store_row(row) for row in csv.DictReader(fh)]

    def save(self, positions: Iterable[SourcePosition]) -> None:
        positions = sorted(
            positions, key=lambda position: (position.evaluation_date, position.asset_name)
        )
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=SOURCE_POSITION_COLUMNS)
            writer.writeheader()
            writer.writerows(_to_store_row(position) for position in positions)


def _from_store_row(row: Mapping[str, str]) -> SourcePosition:
    try:
        evaluation_date = date.fromisoformat(row["evaluation_date"].strip())
        asset_id = row["asset_id"].strip() or None
        asset_name = row["asset_name"].strip()
        quantity = _parse_quantity(row["quantity"])
    except KeyError as exc:
        raise ValueError(f"Missing stored source position field: {exc.args[0]}") from exc
    except ValueError as exc:
        raise ValueError(f"Invalid stored source position: {row!r}") from exc

    if not asset_name:
        raise ValueError("Stored source position has an empty asset_name")

    return SourcePosition(evaluation_date, asset_id, asset_name, quantity)


def _to_store_row(position: SourcePosition) -> dict[str, str]:
    return {
        "evaluation_date": position.evaluation_date.isoformat(),
        "asset_id": position.asset_id or "",
        "asset_name": position.asset_name,
        "quantity": format(position.quantity, "f"),
    }


def _parse_quantity(value: str) -> Decimal:
    value = value.strip()
    if not value or value == "-":
        raise ValueError("Source position has an empty quantity")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid source position quantity: {value!r}") from exc
