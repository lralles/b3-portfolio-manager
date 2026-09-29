from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
import re

from src.core.models.transaction import IOFlow, Transaction, TransactionOperationType


CUSTOM_OPERATION_COLUMNS = [
    "corporate_action_id",
    "date",
    "holding",
    "source_product",
    "source_quantity",
    "target_product",
    "target_quantity",
    "redemption_product",
    "redemption_date",
    "redemption_value",
    "fraction_settlement_date",
]


@dataclass(frozen=True, slots=True)
class CorporateAction:
    corporate_action_id: str
    date: date
    holding: str
    source_product: str
    source_quantity: Decimal
    target_product: str
    target_quantity: Decimal
    redemption_product: str
    redemption_date: date
    redemption_value: Decimal
    fraction_settlement_date: date


def asset_key(name: str) -> str:
    match = re.match(r"^([A-Z0-9]{4,6})\s+-\s+", name.strip())
    return match.group(1) if match else name.strip()


def load(path: Path) -> list[CorporateAction]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return [
            CorporateAction(
                corporate_action_id=row["corporate_action_id"].strip(),
                date=date.fromisoformat(row["date"].strip()),
                holding=row["holding"].strip(),
                source_product=row["source_product"].strip(),
                source_quantity=Decimal(row["source_quantity"].strip()),
                target_product=row["target_product"].strip(),
                target_quantity=Decimal(row["target_quantity"].strip()),
                redemption_product=row["redemption_product"].strip(),
                redemption_date=date.fromisoformat(row["redemption_date"].strip()),
                redemption_value=Decimal(row["redemption_value"].strip()),
                fraction_settlement_date=date.fromisoformat(
                    row["fraction_settlement_date"].strip()
                ),
            )
            for row in csv.DictReader(fh)
        ]


def transactions_for(
    action: CorporateAction,
    assets: dict[str, object],
    holdings: dict[str, object],
    transaction_number_start: int,
) -> list[Transaction]:
    source_asset = assets[asset_key(action.source_product)]
    target_asset = assets[asset_key(action.target_product)]
    redemption_asset = assets[asset_key(action.redemption_product)]
    holding = holdings[action.holding]
    transaction_number = transaction_number_start

    def next_id() -> str:
        nonlocal transaction_number
        value = f"transaction_{transaction_number:03d}"
        transaction_number += 1
        return value

    return [
        Transaction(
            transaction_id=next_id(),
            io_flow=IOFlow.OUTFLOW,
            date=action.date,
            operation_type=TransactionOperationType.INCORPORATION,
            asset_id=source_asset.asset_id,
            holding_id=holding.holding_id,
            quantity=action.source_quantity,
            unit_price=None,
            operation_value=None,
            corporate_action_id=action.corporate_action_id,
            corporate_action_related_asset_id=target_asset.asset_id,
        ),
        Transaction(
            transaction_id=next_id(),
            io_flow=IOFlow.INFLOW,
            date=action.date,
            operation_type=TransactionOperationType.INCORPORATION,
            asset_id=target_asset.asset_id,
            holding_id=holding.holding_id,
            quantity=action.target_quantity,
            unit_price=None,
            operation_value=None,
            corporate_action_id=action.corporate_action_id,
            corporate_action_related_asset_id=source_asset.asset_id,
        ),
        Transaction(
            transaction_id=next_id(),
            io_flow=IOFlow.INFLOW,
            date=action.redemption_date,
            operation_type=TransactionOperationType.REDEMPTION,
            asset_id=redemption_asset.asset_id,
            holding_id=holding.holding_id,
            quantity=None,
            unit_price=None,
            operation_value=action.redemption_value,
            corporate_action_id=action.corporate_action_id,
            corporate_action_related_asset_id=target_asset.asset_id,
        ),
        Transaction(
            transaction_id=next_id(),
            io_flow=IOFlow.OUTFLOW,
            date=action.fraction_settlement_date,
            operation_type=TransactionOperationType.FRACTION_SETTLEMENT,
            asset_id=target_asset.asset_id,
            holding_id=holding.holding_id,
            quantity=None,
            unit_price=None,
            operation_value=None,
            corporate_action_id=action.corporate_action_id,
            corporate_action_related_asset_id=None,
        ),
    ]
