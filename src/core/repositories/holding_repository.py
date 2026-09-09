from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping

from ..models.holding import Holding


HOLDING_COLUMNS = ["holding_id", "holding_name"]


class HoldingRepository:
    def __init__(
        self,
        csv_path: Path = Path("data/store/holdings/holdings.csv"),
    ) -> None:
        self.csv_path = csv_path

    def all(self) -> list[Holding]:
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            return [_from_store_row(row) for row in csv.DictReader(fh)]

    def save(self, holdings: Iterable[Holding]) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=HOLDING_COLUMNS)
            writer.writeheader()
            writer.writerows(_to_store_row(holding) for holding in holdings)


def _from_store_row(row: Mapping[str, str]) -> Holding:
    try:
        holding_id = row["holding_id"].strip()
        holding_name = row["holding_name"].strip()
    except KeyError as exc:
        raise ValueError(f"Missing stored holding field: {exc.args[0]}") from exc

    if not holding_id:
        raise ValueError("Stored holding has an empty holding_id")
    if not holding_name:
        raise ValueError(f"Stored holding {holding_id!r} has an empty holding_name")

    return Holding(holding_id=holding_id, holding_name=holding_name)


def _to_store_row(holding: Holding) -> dict[str, str]:
    return {
        "holding_id": holding.holding_id,
        "holding_name": holding.holding_name,
    }
