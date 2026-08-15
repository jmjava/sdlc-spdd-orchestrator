"""List and restore framework upgrade backups."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from ..timeutil import utc_stamp

BACKUP_DIRNAME = ".sdlc-spdd-upgrade-backups"


def backups_root(target: Path | str) -> Path:
    return Path(target).expanduser().resolve() / BACKUP_DIRNAME


def list_backups(target: Path | str) -> list[dict[str, Any]]:
    root = backups_root(target)
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for child in sorted(root.iterdir(), reverse=True):
        if not child.is_dir():
            continue
        files = [p for p in child.rglob("*") if p.is_file()]
        size = sum(p.stat().st_size for p in files)
        out.append(
            {
                "id": child.name,
                "path": str(child),
                "file_count": len(files),
                "bytes": size,
                "files": sorted(str(p.relative_to(child)) for p in files)[:80],
                "truncated": len(files) > 80,
            }
        )
    return out


def restore_backup(
    target: Path | str,
    backup_id: str,
    *,
    dry_run: bool = False,
    safety_backup: bool = True,
) -> dict[str, Any]:
    """Restore files from an upgrade backup into the target project.

    Optionally snapshots currently-overwritten files into a new safety backup
    under ``.sdlc-spdd-upgrade-backups/pre-rollback-<timestamp>/``.
    """
    target_root = Path(target).expanduser().resolve()
    backup_dir = backups_root(target_root) / backup_id
    if not backup_dir.is_dir():
        return {
            "ok": False,
            "error": f"Backup not found: {backup_id}",
            "restored": [],
            "safety_backup": None,
        }

    files = [p for p in backup_dir.rglob("*") if p.is_file()]
    if not files:
        return {
            "ok": False,
            "error": "Backup is empty",
            "restored": [],
            "safety_backup": None,
        }

    safety_path: Path | None = None
    restored: list[str] = []
    if safety_backup and not dry_run:
        stamp = utc_stamp()
        safety_path = backups_root(target_root) / f"pre-rollback-{stamp}"
        safety_path.mkdir(parents=True, exist_ok=True)

    for src in files:
        rel = src.relative_to(backup_dir)
        dest = target_root / rel
        restored.append(str(rel))
        if dry_run:
            continue
        if safety_path is not None and dest.is_file():
            safety_dest = safety_path / rel
            safety_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dest, safety_dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    return {
        "ok": True,
        "error": None,
        "backup_id": backup_id,
        "dry_run": dry_run,
        "restored": restored,
        "safety_backup": str(safety_path) if safety_path else None,
        "count": len(restored),
    }
