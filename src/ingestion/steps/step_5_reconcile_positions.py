from __future__ import annotations

import argparse
from pathlib import Path

from config import Config
from src.core.repositories.asset_repository import AssetRepository
from src.core.repositories.position_repository import PositionRepository
from src.core.repositories.profit_loss_repository import ProfitLossRepository
from src.core.repositories.transaction_repository import TransactionRepository
from src.core.services.position_service import PositionService
from src.core.services.portfolio_reconciliation import PortfolioReconciliationService
from src.core.services.source_position_service import SourcePositionService


def reconcile(
    transactions_path: Path,
    positions_path: Path,
    assets_path: Path,
    source_positions_path: Path,
    profit_losses_path: Path | None = None,
    config: Config | None = None,
):
    config = config or Config()
    profit_losses_path = profit_losses_path or config.profit_losses_file
    position_service = PositionService(
        TransactionRepository(transactions_path, config),
        PositionRepository(positions_path, config),
        AssetRepository(assets_path, config),
        ProfitLossRepository(profit_losses_path, config),
    )
    position_service.build_and_save()
    return PortfolioReconciliationService(
        SourcePositionService(source_positions_path, config),
        position_service,
        config,
    ).reconcile()


def main() -> int:
    config = Config()
    parser = argparse.ArgumentParser(description="Rebuild and reconcile portfolio positions.")
    parser.add_argument("--transactions", type=Path, default=config.transactions_file)
    parser.add_argument("--positions", type=Path, default=config.positions_file)
    parser.add_argument("--assets", type=Path, default=config.assets_file)
    parser.add_argument("--source-positions", type=Path, default=config.source_positions_file)
    parser.add_argument("--profit-losses", type=Path, default=config.profit_losses_file)
    args = parser.parse_args()
    status = reconcile(args.transactions, args.positions, args.assets, args.source_positions, args.profit_losses)
    print(f"Position reconciliation: {status.status}")
    if status.status != "success":
        for conflict in status.conflicts:
            print(conflict)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
