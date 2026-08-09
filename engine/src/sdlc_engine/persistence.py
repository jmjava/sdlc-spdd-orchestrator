"""Persistence backend options for the ledger-first ContextStore (storage v3).

Config file (gitignored runtime): ``.sdlc/persistence-config.json``

Backends:
  - git-pointers — committed ledger + registry JSONL (always required)
  - sqlite       — opt-in local ``.sdlc/index.sqlite`` cache (soft-fail)
  - guide-dice   — Guide SPDD projection load (soft-fail)

Environment overrides (comma-separated set):
  ``CONTEXT_BACKENDS=git-pointers,guide-dice`` or add ``sqlite`` opt-in.
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
DEFAULT_BACKENDS: tuple[str, ...] = (BACKEND_GIT, BACKEND_GUIDE)

_ALIASES = {
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


def _canonical_name(raw: str) -> str:
    name = str(raw or "").strip().lower().replace("_", "-")
    return _ALIASES.get(name, name)


def normalize_backends(
    backends: Iterable[str],
    *,
    strict: bool = False,
) -> tuple[list[str], list[str]]:
    """Return (normalized backends, unknown names).

    Always includes git-pointers. When ``strict``, callers should reject unknowns.
    """
    seen: set[str] = set()
    out: list[str] = []
    unknown: list[str] = []
    for raw in backends:
        name = _canonical_name(raw)
        if not name:
            continue
        if name not in ALL_BACKENDS:
            if name not in unknown:
                unknown.append(name)
            continue
        if name in seen:
            continue
        seen.add(name)
        out.append(name)
    if BACKEND_GIT not in out:
        out = [BACKEND_GIT, *out]
    if strict and unknown:
        raise ValueError(
            "unknown persistence backend(s): "
            + ", ".join(unknown)
            + f" (allowed: {', '.join(ALL_BACKENDS)})"
        )
    return out, unknown


def _normalize(backends: Iterable[str]) -> list[str]:
    normalized, _unknown = normalize_backends(backends, strict=False)
    return normalized


def default_config() -> dict[str, Any]:
    return {
        "backends": list(DEFAULT_BACKENDS),
        "guide_base_url": "",
        "notes": "",
    }


def config_path(project: Project | Path | str) -> Path:
    if isinstance(project, Project):
        return project.sdlc_dir / CONFIG_REL.name
    return Project(Path(project).expanduser().resolve()).sdlc_dir / CONFIG_REL.name


def parse_backends_env(raw: str | None) -> list[str] | None:
    text = (raw or "").strip()
    if not text:
        return None
    parts = [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]
    normalized, unknown = normalize_backends(parts, strict=False)
    # If every token was garbage, treat as unset so defaults/file apply.
    if unknown and not any(_canonical_name(p) in ALL_BACKENDS for p in parts):
        return None
    return normalized


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
                if data.get("guide_base_url") is not None:
                    cfg["guide_base_url"] = str(data.get("guide_base_url") or "").strip()
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
    """Write ``.sdlc/persistence-config.json`` and return operator status shape."""
    project_obj = project if isinstance(project, Project) else Project(Path(project))
    path = config_path(project_obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    backends, _unknown = normalize_backends(
        cfg.get("backends") or DEFAULT_BACKENDS, strict=True
    )
    out = {
        "backends": backends,
        "guide_base_url": str(cfg.get("guide_base_url") or "").strip(),
        "notes": str(cfg.get("notes") or ""),
    }
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    status = status_dict(project_obj)
    status["path"] = str(path)
    status["saved"] = True
    status["guide_base_url"] = out["guide_base_url"]
    return status


def enabled(project: Project | Path | str, backend: str) -> bool:
    return backend in set(load_config(project).get("backends") or [])


def status_dict(project: Project) -> dict[str, Any]:
    """Operator-facing status for CLI + ops console."""
    cfg = load_config(project)
    backends = list(cfg.get("backends") or [])
    sqlite_path = project.sdlc_dir / "index.sqlite"
    configured_url = str(cfg.get("guide_base_url") or "").strip()
    env_url = os.environ.get("GUIDE_BASE_URL", "").strip()
    port = os.environ.get("GUIDE_PORT", "21337").strip() or "21337"
    effective_url = (configured_url or env_url or f"http://localhost:{port}").rstrip("/")
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
            "ledger": "spdd/memory/lessons.jsonl",
            "staged": ".sdlc/staged/lessons.jsonl",
            "registry": "spdd/memory/registry.jsonl",
        },
        "sqlite": {
            "enabled": BACKEND_SQLITE in backends,
            "path": str(sqlite_path),
            "exists": sqlite_path.is_file(),
        },
        "guide": {
            "enabled": BACKEND_GUIDE in backends,
            # Configured value only — do not round-trip the effective default into the form.
            "base_url": configured_url,
            "effective_base_url": effective_url,
        },
        "notes": cfg.get("notes") or "",
        "env": {
            "CONTEXT_BACKENDS": os.environ.get("CONTEXT_BACKENDS", ""),
            "GUIDE_BASE_URL": os.environ.get("GUIDE_BASE_URL", ""),
            "GUIDE_PORT": os.environ.get("GUIDE_PORT", ""),
        },
    }
