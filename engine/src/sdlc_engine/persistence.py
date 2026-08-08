"""Persistence backend options for the triple-path ContextStore (#79/#90).

Config file (gitignored runtime): ``.sdlc/persistence-config.json``

Backends:
  - git-pointers — lean stay-set files + pointers.jsonl (required when enabled)
  - sqlite       — local ``.sdlc/index.sqlite`` upsert (soft-fail)
  - guide-dice   — Guide SPDD projection load (soft-fail)

Environment overrides (comma-separated set):
  ``CONTEXT_BACKENDS=git-pointers,sqlite,guide-dice``
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

from .project import Project

CONFIG_REL = Path(".sdlc") / "persistence-config.json"

BACKEND_GIT = "git-pointers"
BACKEND_SQLITE = "sqlite"
BACKEND_GUIDE = "guide-dice"

ALL_BACKENDS: tuple[str, ...] = (BACKEND_GIT, BACKEND_SQLITE, BACKEND_GUIDE)
DEFAULT_BACKENDS: tuple[str, ...] = ALL_BACKENDS


def _normalize(backends: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in backends:
        name = str(raw or "").strip().lower().replace("_", "-")
        aliases = {
            "git": BACKEND_GIT,
            "git-pointer": BACKEND_GIT,
            "pointers": BACKEND_GIT,
            "files": BACKEND_GIT,
            "db": BACKEND_SQLITE,
            "local-sqlite": BACKEND_SQLITE,
            "guide": BACKEND_GUIDE,
            "dice": BACKEND_GUIDE,
            "guide-dice": BACKEND_GUIDE,
        }
        name = aliases.get(name, name)
        if name not in ALL_BACKENDS or name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def default_config() -> dict[str, Any]:
    return {
        "backends": list(DEFAULT_BACKENDS),
        "guide_base_url": "",
        "notes": "",
    }


def config_path(project: Project | Path | str) -> Path:
    root = project.root if isinstance(project, Project) else Path(project)
    return Path(root).expanduser().resolve() / CONFIG_REL


def parse_backends_env(raw: str | None) -> list[str] | None:
    text = (raw or "").strip()
    if not text:
        return None
    parts = [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]
    return _normalize(parts) or None


def load_config(project: Project | Path | str) -> dict[str, Any]:
    """Load persistence options: env CONTEXT_BACKENDS > config file > defaults."""
    cfg = default_config()
    path = config_path(project)
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if "backends" in data and data["backends"] is not None:
                    normalized = _normalize(data["backends"])
                    if normalized:
                        cfg["backends"] = normalized
                if data.get("guide_base_url"):
                    cfg["guide_base_url"] = str(data["guide_base_url"]).strip()
                if data.get("notes") is not None:
                    cfg["notes"] = str(data.get("notes") or "")
        except (OSError, json.JSONDecodeError):
            pass
    env_backends = parse_backends_env(os.environ.get("CONTEXT_BACKENDS"))
    if env_backends is not None:
        cfg["backends"] = env_backends
        cfg["source"] = "env:CONTEXT_BACKENDS"
    else:
        cfg["source"] = "file" if path.is_file() else "defaults"
    # git-pointers is the stay-set baseline; always include when any persist runs
    if BACKEND_GIT not in cfg["backends"]:
        cfg["backends"] = [BACKEND_GIT, *cfg["backends"]]
    return cfg


def save_config(project: Project | Path | str, cfg: dict[str, Any]) -> dict[str, Any]:
    """Write ``.sdlc/persistence-config.json`` and return the normalized config."""
    root = project.root if isinstance(project, Project) else Path(project)
    root = Path(root).expanduser().resolve()
    path = root / CONFIG_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    backends = _normalize(cfg.get("backends") or DEFAULT_BACKENDS)
    if BACKEND_GIT not in backends:
        backends = [BACKEND_GIT, *backends]
    out = {
        "backends": backends,
        "guide_base_url": str(cfg.get("guide_base_url") or "").strip(),
        "notes": str(cfg.get("notes") or ""),
    }
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    loaded = load_config(root)
    loaded["path"] = str(path)
    loaded["saved"] = True
    return loaded


def enabled(project: Project | Path | str, backend: str) -> bool:
    return backend in set(load_config(project).get("backends") or [])


def status_dict(project: Project) -> dict[str, Any]:
    """Operator-facing status for CLI + ops console."""
    cfg = load_config(project)
    backends = list(cfg.get("backends") or [])
    sqlite_path = project.sdlc_dir / "index.sqlite"
    guide_url = (cfg.get("guide_base_url") or "").strip()
    if not guide_url:
        env_url = os.environ.get("GUIDE_BASE_URL", "").strip()
        port = os.environ.get("GUIDE_PORT", "21337").strip() or "21337"
        guide_url = env_url or f"http://localhost:{port}"
    return {
        "ok": True,
        "backends": backends,
        "enabled": {
            BACKEND_GIT: BACKEND_GIT in backends,
            BACKEND_SQLITE: BACKEND_SQLITE in backends,
            BACKEND_GUIDE: BACKEND_GUIDE in backends,
        },
        "source": cfg.get("source"),
        "config_path": str(config_path(project)),
        "config_exists": config_path(project).is_file(),
        "git": {
            "ok": True,
            "stay_set": "spdd/memory/",
            "pointers": "spdd/memory/pointers.jsonl",
            "entries": "spdd/memory/entries/",
            "lessons": "spdd/memory/lessons/",
        },
        "sqlite": {
            "enabled": BACKEND_SQLITE in backends,
            "path": str(sqlite_path),
            "exists": sqlite_path.is_file(),
        },
        "guide": {
            "enabled": BACKEND_GUIDE in backends,
            "base_url": guide_url.rstrip("/"),
        },
        "notes": cfg.get("notes") or "",
        "env": {
            "CONTEXT_BACKENDS": os.environ.get("CONTEXT_BACKENDS", ""),
            "GUIDE_BASE_URL": os.environ.get("GUIDE_BASE_URL", ""),
            "GUIDE_PORT": os.environ.get("GUIDE_PORT", ""),
        },
    }
