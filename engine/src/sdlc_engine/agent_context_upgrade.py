"""Upgrade/re-init noisy agent-context runtime off git (#80, #86)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .db import LocalIndex
from .project import Project

RUNTIME_NOISE_DIRS = (
    Path("agent-context/sessions"),
    Path("agent-context/features"),
    Path("agent-context/memory/sessions"),
)

LEAN_KEEP_DIRS = (
    Path("agent-context/harness"),
    Path("agent-context/playbooks"),
    Path("agent-context/extensions"),
)

MEMORY_EXPORT_FILES = (
    "context-index.md",
    "domain-index.md",
    "phase-index.md",
    "code-areas.md",
    "project-memory.md",
    "prompt-optimization-log.md",
    "architecture-decisions.md",
    "known-pitfalls.md",
    "reusable-patterns.md",
    "session-history.md",
    "session-index.md",
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


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
    """Archive sessions/features mirrors; seed lean runtime; rebuild SQLite."""

    def __init__(self, project: Project | None = None) -> None:
        self.project = project or Project.resolve()

    def detect(self) -> dict[str, Any]:
        root = self.project.root
        found: dict[str, Any] = {"noise": [], "memory_files": [], "lean_present": []}
        for rel in RUNTIME_NOISE_DIRS:
            path = root / rel
            if path.exists():
                found["noise"].append(str(rel))
        mem = root / "agent-context" / "memory"
        if mem.is_dir():
            for name in MEMORY_EXPORT_FILES:
                if (mem / name).is_file():
                    found["memory_files"].append(f"agent-context/memory/{name}")
        for rel in LEAN_KEEP_DIRS:
            if (root / rel).is_dir():
                found["lean_present"].append(str(rel))
        found["needs_upgrade"] = bool(found["noise"]) or bool(found["memory_files"])
        found["already_upgraded"] = (
            self.project.root / "agent-context" / "UPGRADED.md"
        ).is_file()
        return found

    def run(self, *, dry_run: bool = False, rebuild_db: bool = True) -> UpgradeResult:
        root = self.project.root
        export = self.project.sdlc_dir / "legacy-export" / _utc_stamp()
        result = UpgradeResult(ok=True, dry_run=dry_run, export_dir=str(export))
        detect = self.detect()
        if detect.get("already_upgraded") and not detect["noise"]:
            hot = self.project.hot_session_dir()
            if not dry_run:
                hot.mkdir(parents=True, exist_ok=True)
                (root / "spdd" / "memory" / "entries").mkdir(parents=True, exist_ok=True)
            result.notes.append("Already upgraded (idempotent).")
            result.created = [str(hot.relative_to(root)), "spdd/memory/entries"]
            return result
        if not detect["needs_upgrade"]:
            hot = self.project.hot_session_dir()
            if not dry_run:
                hot.mkdir(parents=True, exist_ok=True)
                (root / "spdd" / "memory" / "entries").mkdir(parents=True, exist_ok=True)
            result.notes.append("No agent-context runtime noise detected (idempotent).")
            result.created = [str(hot.relative_to(root)), "spdd/memory/entries"]
            return result

        if dry_run:
            result.notes.append(f"Would export to {export}")
            result.moved = list(detect["noise"])
            result.copied_memory = list(detect["memory_files"])
            return result

        export.mkdir(parents=True, exist_ok=True)
        # Export durable memory before moving trees.
        mem_src = root / "agent-context" / "memory"
        mem_dst = export / "memory"
        if mem_src.is_dir():
            mem_dst.mkdir(parents=True, exist_ok=True)
            for name in MEMORY_EXPORT_FILES:
                src = mem_src / name
                if src.is_file():
                    shutil.copy2(src, mem_dst / name)
                    result.copied_memory.append(f"agent-context/memory/{name}")
        lean_mem = root / "spdd" / "memory"
        if lean_mem.is_dir():
            dst = export / "spdd-memory"
            shutil.copytree(lean_mem, dst, dirs_exist_ok=True)
            result.notes.append("Copied spdd/memory into legacy-export.")

        for rel in RUNTIME_NOISE_DIRS:
            src = root / rel
            if not src.exists():
                continue
            dest = export / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(src), str(dest))
            result.moved.append(str(rel))

        # Ensure lean session dir + stay-set memory scaffold.
        hot = self.project.hot_session_dir()
        hot.mkdir(parents=True, exist_ok=True)
        result.created.append(str(hot.relative_to(root)))
        lean_entries = root / "spdd" / "memory" / "entries"
        lean_entries.mkdir(parents=True, exist_ok=True)
        result.created.append("spdd/memory/entries")
        for rel in LEAN_KEEP_DIRS:
            path = root / rel
            path.mkdir(parents=True, exist_ok=True)
            result.created.append(str(rel))

        # Marker so quiet/upgrade tooling can see migration happened.
        marker = root / "agent-context" / "UPGRADED.md"
        marker.write_text(
            "# Agent-context upgraded\n\n"
            f"- Exported runtime noise to `{export.relative_to(root)}`\n"
            "- Hot sessions: `.sdlc/sessions/`\n"
            "- Feature mirrors archived; use stay-set requirements + REASONS.\n",
            encoding="utf-8",
        )
        result.created.append("agent-context/UPGRADED.md")

        if rebuild_db:
            try:
                stats = LocalIndex(self.project).rebuild()
                result.notes.append(
                    f"Rebuilt SQLite: work_items={stats.work_items} "
                    f"context_entries={stats.context_entries}"
                )
            except Exception as exc:  # noqa: BLE001
                result.ok = False
                result.errors.append(f"db rebuild: {exc}")

        return result
