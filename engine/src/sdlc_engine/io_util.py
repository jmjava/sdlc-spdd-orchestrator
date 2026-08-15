"""Small JSON/path helpers shared by persistence, installer runtimes, and indexes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_dict(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk. Missing/invalid files become ``{}``."""
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_json_dict(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def clear_file(path: Path) -> None:
    if path.is_file():
        path.unlink()


def rel_to(root: Path, path: Path | str) -> str:
    """Return ``path`` relative to ``root``, or the original string if it is outside."""
    candidate = Path(path)
    try:
        return str(candidate.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(candidate)
