from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Mapping

from ...core.models.source_position import SourcePosition


def source_position_from_sanitized_row(
    row: Mapping[str, str], asset_id: str | None
) -> SourcePosition:
    try:
        evaluation_date = date.fromisoformat(row["evaluation_date"].strip())
        asset_name = row["Produto"].strip()
        quantity_value = row["Quantidade"].strip().replace(",", ".")
        quantity = Decimal(quantity_value)
    except KeyError as exc:
        raise ValueError(
            f"Missing sanitized source position field: {exc.args[0]}"
        ) from exc
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid sanitized source position: {row!r}") from exc

    if not asset_name:
        raise ValueError("Sanitized source position has an empty Produto")

    return SourcePosition(evaluation_date, asset_id, asset_name, quantity)
