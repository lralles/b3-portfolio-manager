from __future__ import annotations

import json
from pathlib import Path


def load(path: Path) -> list[list[str]]:
    """Load groups of names that refer to the same canonical asset."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        groups = json.load(fh)
    if not isinstance(groups, list) or any(
        not isinstance(group, list)
        or not group
        or any(not isinstance(name, str) or not name.strip() for name in group)
        for group in groups
    ):
        raise ValueError("Equivalent asset names must be a JSON array of non-empty arrays")
    return groups
