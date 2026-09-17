from __future__ import annotations

import csv
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

    def all(self) -> list[Position]:
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            return [Position.from_store_row(row) for row in csv.DictReader(fh)]

    def save(self, positions: Iterable[Position]) -> None:
        positions = sorted(positions, key=lambda position: position.key)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=POSITION_COLUMNS)
            writer.writeheader()
            writer.writerows(position.to_store_row() for position in positions)
