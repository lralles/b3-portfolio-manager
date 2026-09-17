from __future__ import annotations

from pathlib import Path


class Config:
    """Application paths loaded from the repository configuration file."""

    _CONFIG_FILE = Path(__file__).with_name("config.yaml")

    def __init__(self) -> None:
        values = _load_yaml_paths(self._CONFIG_FILE)
        project_root = self._CONFIG_FILE.parent.parent
        for name, value in values.items():
            path = Path(value)
            setattr(self, name, path if path.is_absolute() else project_root / path)


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
