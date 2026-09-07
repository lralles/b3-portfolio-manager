from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping

from ..models.account import Account


ACCOUNT_COLUMNS = ["account_id", "account_name"]


class AccountRepository:
    def __init__(
        self,
        csv_path: Path = Path("data/store/accounts/accounts.csv"),
    ) -> None:
        self.csv_path = csv_path

    def all(self) -> list[Account]:
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            return [_from_store_row(row) for row in csv.DictReader(fh)]

    def save(self, accounts: Iterable[Account]) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=ACCOUNT_COLUMNS)
            writer.writeheader()
            writer.writerows(_to_store_row(account) for account in accounts)


def _from_store_row(row: Mapping[str, str]) -> Account:
    try:
        account_id = row["account_id"].strip()
        account_name = row["account_name"].strip()
    except KeyError as exc:
        raise ValueError(f"Missing stored account field: {exc.args[0]}") from exc

    if not account_id:
        raise ValueError("Stored account has an empty account_id")
    if not account_name:
        raise ValueError(f"Stored account {account_id!r} has an empty account_name")

    return Account(account_id=account_id, account_name=account_name)


def _to_store_row(account: Account) -> dict[str, str]:
    return {
        "account_id": account.account_id,
        "account_name": account.account_name,
    }
