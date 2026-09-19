from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar


@dataclass(frozen=True, init=False)
class Config:
    """Application paths loaded from the repository configuration file."""

    raw_transactions_dir: Path
    raw_position_file: Path
    sanitized_dir: Path
    sanitized_transactions_file: Path
    sanitized_positions_file: Path
    store_dir: Path
    assets_file: Path
    holdings_file: Path
    transactions_file: Path
    source_positions_file: Path
    positions_file: Path
    profit_losses_file: Path
    trading_prices_file: Path

    _CONFIG_FILE: ClassVar[Path] = Path(__file__).with_name("config.yaml")
    _PATH_FIELDS: ClassVar[tuple[str, ...]] = (
        "raw_transactions_dir",
        "raw_position_file",
        "sanitized_dir",
        "sanitized_transactions_file",
        "sanitized_positions_file",
        "store_dir",
        "assets_file",
        "holdings_file",
        "transactions_file",
        "source_positions_file",
        "positions_file",
        "profit_losses_file",
        "trading_prices_file",
    )

    def __init__(self) -> None:
        values = _load_yaml_paths(self._CONFIG_FILE)
        project_root = self._CONFIG_FILE.parent.parent
        missing = set(self._PATH_FIELDS) - values.keys()
        unexpected = values.keys() - set(self._PATH_FIELDS)
        if missing or unexpected:
            problems = []
            if missing:
                problems.append(f"missing fields: {sorted(missing)}")
            if unexpected:
                problems.append(f"unexpected fields: {sorted(unexpected)}")
            raise ValueError("Invalid configuration (" + "; ".join(problems) + ")")

        for name in self._PATH_FIELDS:
            configured_path = Path(values[name])
            resolved_path = (
                configured_path
                if configured_path.is_absolute()
                else project_root / configured_path
            )
            object.__setattr__(self, name, resolved_path)


def _load_yaml_paths(path: Path) -> dict[str, str]:
    """Load the small, dependency-free YAML mapping used by this application."""
    values: dict[str, str] = {}
    in_paths = False
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "paths:":
            in_paths = True
            continue
        if not in_paths or not line.startswith("  ") or ":" not in stripped:
            raise ValueError(f"Invalid config entry on line {line_number}: {line!r}")
        name, value = stripped.split(":", 1)
        value = value.strip()
        if not name or not value:
            raise ValueError(f"Invalid config entry on line {line_number}: {line!r}")
        values[name.strip()] = value.strip("'\"")
    if not values:
        raise ValueError(f"No paths found in configuration file: {path}")
    return values
