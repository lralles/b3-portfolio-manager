from __future__ import annotations

import argparse
from pathlib import Path

from src.core.repositories.asset_repository import AssetRepository
from src.core.repositories.position_repository import PositionRepository
from src.core.repositories.transaction_repository import TransactionRepository
from src.core.services.position_service import PositionService
from src.core.services.portfolio_reconciliation import PortfolioReconciliationService
from src.core.services.source_position_service import SourcePositionService


def reconcile(
    transactions_path: Path,
    positions_path: Path,
    assets_path: Path,
    source_positions_path: Path,
):
    position_service = PositionService(
        TransactionRepository(transactions_path),
        PositionRepository(positions_path),
        AssetRepository(assets_path),
    )
    position_service.build_and_save()
    return PortfolioReconciliationService(
        SourcePositionService(source_positions_path),
        position_service,
    ).reconcile()


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild and reconcile portfolio positions.")
    parser.add_argument("--transactions", type=Path, default=Path("data/store/transactions/transactions.csv"))
    parser.add_argument("--positions", type=Path, default=Path("data/store/computed_positions/positions.csv"))
    parser.add_argument("--assets", type=Path, default=Path("data/store/assets/assets.csv"))
    parser.add_argument("--source-positions", type=Path, default=Path("data/store/source_positions/source_positions.csv"))
    args = parser.parse_args()
    status = reconcile(args.transactions, args.positions, args.assets, args.source_positions)
    print(f"Position reconciliation: {status.status}")
    if status.status != "success":
        for conflict in status.conflicts:
            print(conflict)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
