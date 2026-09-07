from __future__ import annotations

import csv
from pathlib import Path

from ..models.asset import Asset


class AssetRepository:
    def __init__(
        self,
        csv_path: Path = Path("data/store/assets/assets.csv"),
    ) -> None:
        self.csv_path = csv_path

    def all(self) -> list[Asset]:
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            return [Asset.from_store_row(row) for row in csv.DictReader(fh)]
