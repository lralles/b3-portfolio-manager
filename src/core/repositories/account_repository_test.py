from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.core.models.account import Account
from src.core.repositories.account_repository import AccountRepository


class AccountRepositoryTests(unittest.TestCase):
    def test_repository_round_trip(self) -> None:
        account = Account("account_001", "Example Account")

        with tempfile.TemporaryDirectory() as directory:
            repository = AccountRepository(Path(directory) / "accounts.csv")
            repository.save([account])

            self.assertEqual(repository.all(), [account])


if __name__ == "__main__":
    unittest.main()
