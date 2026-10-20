from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Iterable

from config import Config
from ..models.position import POSITION_COLUMNS, Position


class PositionRepository:
    def __init__(
        self,
        csv_path: Path | None = None,
        config: Config | None = None,
    ) -> None:
        self.config = config or Config()
        self.csv_path = csv_path or self.config.positions_file

    def all(self, reference_date: date | None = None) -> list[Position]:
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            stored_positions = [
                Position.from_store_row(row) for row in csv.DictReader(fh)
            ]

        available_positions = [
            position
            for position in stored_positions
            if position.reference_date is None
            or position.reference_date <= (reference_date or date.today())
        ]
        latest_by_asset: dict[str, Position] = {}
        for position in available_positions:
            previous = latest_by_asset.get(position.asset_id)
            if previous is None or (
                position.reference_date or date.min
            ) >= (previous.reference_date or date.min):
                latest_by_asset[position.asset_id] = position
        return sorted(latest_by_asset.values(), key=lambda position: position.key)

    def save(self, positions: Iterable[Position]) -> None:
        positions = sorted(
            positions,
            key=lambda position: (position.key, position.reference_date or date.min),
        )
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=POSITION_COLUMNS)
            writer.writeheader()
            writer.writerows(position.to_store_row() for position in positions)
