from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


CUSTOM_REDEMPTION_COLUMNS = ["date", "asset_name", "value"]


def load(path: Path) -> dict[tuple[date, str], Decimal]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != CUSTOM_REDEMPTION_COLUMNS:
            raise ValueError(
                "Custom redemptions must have columns: "
                + ", ".join(CUSTOM_REDEMPTION_COLUMNS)
            )
        redemptions: dict[tuple[date, str], Decimal] = {}
        for row in reader:
            try:
                redemption_date = date.fromisoformat(row["date"].strip())
                asset_name = row["asset_name"].strip()
                value = Decimal(row["value"].strip())
            except (KeyError, InvalidOperation, ValueError) as exc:
                raise ValueError(f"Invalid custom redemption row: {row!r}") from exc
            if not asset_name or value <= 0:
                raise ValueError(f"Invalid custom redemption row: {row!r}")
            key = (redemption_date, asset_name)
            if key in redemptions:
                raise ValueError(f"Duplicate custom redemption: {row!r}")
            redemptions[key] = value
    return redemptions
