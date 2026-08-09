"""Upgrade/re-init noisy agent-context runtime off git (#80, #86).

Prefer ``sdlc-engine storage migrate`` for storage v3; this class remains for
``agent-context upgrade`` CLI compatibility and delegates to :class:`StorageMigration`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .db import LocalIndex
from .project import Project
from .storage_migrate import StorageMigration


@dataclass
class UpgradeResult:
    ok: bool
    dry_run: bool
    export_dir: str = ""
    moved: list[str] = field(default_factory=list)
    copied_memory: list[str] = field(default_factory=list)
    created: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dry_run": self.dry_run,
            "export_dir": self.export_dir,
            "moved": list(self.moved),
            "copied_memory": list(self.copied_memory),
            "created": list(self.created),
            "notes": list(self.notes),
            "errors": list(self.errors),
        }


class AgentContextUpgrade:
    """Delegate to storage v3 migration; keep legacy CLI surface."""

    def __init__(self, project: Project | None = None) -> None:
        self.project = project or Project.resolve()
        self._migration = StorageMigration(self.project)

    def detect(self) -> dict[str, Any]:
        mig = self._migration.detect()
        found: dict[str, Any] = {
            "noise": mig.get("legacy_present") or [],
            "memory_files": [
                p for p in (mig.get("legacy_present") or []) if "memory" in p
            ],
            "lean_present": [],
            "needs_upgrade": mig.get("needs_migration", False),
            "already_upgraded": mig.get("migrated", False),
            "storage_v3": mig,
            "prefer_command": "storage migrate",
        }
        home = self.project.home
        for rel in (
            "agent-context/harness",
            "agent-context/playbooks",
            "agent-context/extensions",
            "harness",
        ):
            if (home / rel).is_dir():
                found["lean_present"].append(rel)
        return found

    def run(self, *, dry_run: bool = False, rebuild_db: bool = True) -> UpgradeResult:
        result = UpgradeResult(ok=True, dry_run=dry_run)
        mig_out = self._migration.run(dry_run=dry_run)
        result.export_dir = mig_out.get("export_dir") or ""
        result.moved = list(mig_out.get("exported") or [])
        result.notes.append("Delegated to storage v3 migration.")
        if mig_out.get("records_migrated"):
            result.notes.append(f"records_migrated={mig_out['records_migrated']}")
        self.project.ensure_runtime_dirs()
        result.created = [
            str(self.project.hot_session_dir().relative_to(self.project.root)),
        ]
        if rebuild_db and not dry_run and not mig_out.get("sqlite_rebuilt"):
            try:
                stats = LocalIndex(self.project).rebuild()
                result.notes.append(
                    f"Rebuilt SQLite: work_items={stats.work_items} lessons={stats.lessons}"
                )
            except Exception as exc:  # noqa: BLE001
                result.ok = False
                result.errors.append(f"db rebuild: {exc}")
        return result
