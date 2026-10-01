from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from dataclasses import replace
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from config import Config
from src.core.models.asset import Asset, AssetType
from src.core.models.trading_price import TradingPrice
from src.core.repositories.trading_price_repository import TradingPriceRepository
from src.core.services.asset_service import AssetService
from src.core.services.source_position_service import SourcePositionService
from src.ingestion.b3.source_position_mapper import source_position_from_sanitized_row


PREFIX_FALLBACK_ASSET_TYPES = {
    AssetType.STOCKS.value,
    AssetType.FII.value,
    AssetType.ETF.value,
}


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def ingest(
    input_path: Path,
    output_path: Path,
    assets_path: Path,
    config: Config | None = None,
    trading_prices_path: Path | None = None,
):
    config = config or Config()
    trading_prices_path = trading_prices_path or config.trading_prices_file
    with input_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    rows.sort(key=lambda row: date.fromisoformat(row["evaluation_date"].strip()))

    asset_service = AssetService(assets_path, config)
    assets = asset_service.all()
    assets_by_id = {asset.asset_id: asset for asset in assets}
    lookup: dict[str, Asset] = {}
    for asset in assets:
        lookup[normalized(asset.asset_name)] = asset
        lookup.setdefault(normalized(asset.asset_name.split(" - ", 1)[0]), asset)
    positions = []
    trading_prices = []
    for row in rows:
        asset = lookup.get(normalized(row["Produto"]))
        if (
            asset is None
            and row.get("asset_type", "").strip() in PREFIX_FALLBACK_ASSET_TYPES
        ):
            asset = lookup.get(normalized(row["Produto"].split(" - ", 1)[0]))
        if asset:
            asset = assets_by_id[asset.asset_id]
        isin = row.get("Código ISIN", "").strip()
        asset_type_value = row.get("asset_type", "").strip()
        if asset:
            row_asset_type = AssetType(asset_type_value) if asset_type_value else None
            enriched_asset = replace(
                asset,
                isin=asset.isin or isin,
                asset_type=row_asset_type or asset.asset_type,
            )
            assets_by_id[asset.asset_id] = enriched_asset
            trading_price = _trading_price_from_row(row, asset.asset_id, row_asset_type)
            if trading_price:
                trading_prices.append(trading_price)
        positions.append(
            source_position_from_sanitized_row(row, asset.asset_id if asset else None)
        )
    asset_service.save(list(assets_by_id.values()))
    SourcePositionService(output_path, config).save(positions)
    
    trading_price_repository = TradingPriceRepository(trading_prices_path, config)
    existing_prices = (
        trading_price_repository.all() if trading_prices_path.exists() else []
    )
    prices_by_key = {
        (price.asset_id, price.evaluation_date): price for price in existing_prices
    }
    # Position prices are more recent/authoritative than transaction prices.
    prices_by_key.update(
        {(price.asset_id, price.evaluation_date): price for price in trading_prices}
    )
    trading_price_repository.save(prices_by_key.values())
    return positions


def _trading_price_from_row(
    row: dict[str, str], asset_id: str, asset_type: AssetType | None
) -> TradingPrice | None:
    if asset_type in (AssetType.STOCKS, AssetType.FII, AssetType.ETF):
        if "Preço de Fechamento" not in row:
            return None
        value = _parse_decimal(row.get("Preço de Fechamento", ""))
    elif asset_type == AssetType.TREASURY_BOND:
        if "Quantidade" not in row or "Valor Atualizado" not in row:
            return None
        quantity = _parse_decimal(row.get("Quantidade", ""))
        updated_value = _parse_decimal(row.get("Valor Atualizado", ""))
        if quantity == 0:
            raise ValueError(f"Cannot extract trading price for {asset_id!r} with zero quantity")
        value = updated_value / quantity
    else:
        return None

    return TradingPrice(
        asset_id=asset_id,
        evaluation_date=date.fromisoformat(row["evaluation_date"].strip()),
        value=value,
    )


def _parse_decimal(value: str) -> Decimal:
    normalized_value = value.strip().replace(",", ".")
    if not normalized_value or normalized_value == "-":
        raise ValueError("Trading price source value is empty")
    try:
        return Decimal(normalized_value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid trading price source value: {value!r}") from exc


def main() -> int:
    config = Config()
    parser = argparse.ArgumentParser(description="Ingest source positions for quality checks.")
    parser.add_argument("--input", type=Path, default=config.sanitized_positions_file)
    parser.add_argument("--output", type=Path, default=config.source_positions_file)
    parser.add_argument("--assets", type=Path, default=config.assets_file)
    args = parser.parse_args()
    positions = ingest(args.input, args.output, args.assets, config=config)
    print(f"Wrote {len(positions)} source positions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
