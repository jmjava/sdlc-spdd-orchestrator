"""Team Work ID registry — JSONL event log (storage v3).

``spdd/memory/registry.jsonl`` is the only write store: append-only events
``{"event","work_id","status","phase","operation","owner","note","ts"}``.
``rows()`` derives current state = latest event per ``work_id``.

During transition, if ``registry.jsonl`` is missing and legacy
``agent-context/work-registry.tsv`` exists, ``rows()`` falls back to a
read-only TSV parse (no writes to TSV).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import canvas as canvas_mod
from .project import Project
from .workflow import WorkflowEngine


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class RegistryRow:
    work_id: str
    status: str
    phase: str = ""
    operation: str = ""
    owner: str = ""
    updated: str = ""
    note: str = ""

    def as_event(self, *, event: str = "update") -> dict[str, str]:
        return {
            "event": event,
            "work_id": self.work_id,
            "status": self.status,
            "phase": self.phase,
            "operation": self.operation,
            "owner": self.owner,
            "note": self.note,
            "ts": self.updated or _utc_now(),
        }


class TeamRegistry:
    def __init__(self, project: Project | None = None, workflow: WorkflowEngine | None = None) -> None:
        self.project = project or Project.resolve()
        self.workflow = workflow or WorkflowEngine(self.project)
        self.project.ensure_runtime_dirs()

    @property
    def path(self) -> Path:
        return self.project.registry_jsonl_path

    @property
    def legacy_tsv_path(self) -> Path:
        # Read-only transition fallback (see module docstring).
        return self.project.home / "agent-context" / "work-registry.tsv"

    def _owner(self) -> str:
        if os.environ.get("SDLC_USER"):
            return os.environ["SDLC_USER"]
        try:
            import subprocess

            name = subprocess.check_output(
                ["git", "-C", str(self.project.root), "config", "user.name"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            if name:
                return name
        except Exception:
            pass
        return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"

    def ensure(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.is_file():
            self.path.write_text("", encoding="utf-8")

    def _read_events(self) -> list[dict[str, str]]:
        if self.path.is_file():
            out: list[dict[str, str]] = []
            for line in self.path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    if isinstance(row, dict) and row.get("work_id"):
                        out.append({k: str(v or "") for k, v in row.items()})
                except json.JSONDecodeError:
                    continue
            return out
        # Transition read-only fallback: legacy TSV when JSONL absent.
        tsv = self.legacy_tsv_path
        if not tsv.is_file():
            return []
        out = []
        for line in tsv.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or line.startswith("work_id"):
                continue
            parts = line.split("\t")
            while len(parts) < 7:
                parts.append("")
            out.append(
                {
                    "event": "legacy-tsv",
                    "work_id": parts[0],
                    "status": parts[1],
                    "phase": parts[2],
                    "operation": parts[3],
                    "owner": parts[4],
                    "ts": parts[5],
                    "note": parts[6],
                }
            )
        return out

    def rows(self) -> list[RegistryRow]:
        """Current registry state = latest event per work_id."""
        by_id: dict[str, RegistryRow] = {}
        for ev in self._read_events():
            wid = (ev.get("work_id") or "").strip()
            if not wid:
                continue
            by_id[wid] = RegistryRow(
                work_id=wid,
                status=ev.get("status") or "available",
                phase=ev.get("phase") or "",
                operation=ev.get("operation") or "",
                owner=ev.get("owner") or "",
                updated=ev.get("ts") or "",
                note=ev.get("note") or "",
            )
        return list(by_id.values())

    def _append_event(self, payload: dict[str, str]) -> None:
        self.ensure()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def upsert(self, row: RegistryRow, *, event: str = "update") -> None:
        """Append a registry event (never rewrite history)."""
        if not row.updated:
            row.updated = _utc_now()
        existing = next((r for r in self.rows() if r.work_id == row.work_id), None)
        if existing and not row.note:
            row.note = existing.note
        self._append_event(row.as_event(event=event))

    def lean_events(self, *, work_id: str = "") -> list[dict]:
        """Alias for ``_read_events`` filtered by work_id."""
        events = self._read_events()
        if work_id:
            return [e for e in events if e.get("work_id") == work_id]
        return events

    def _fanout_claim_sqlite(self, row: RegistryRow) -> None:
        try:
            from .persistence import BACKEND_SQLITE, enabled

            if not enabled(self.project, BACKEND_SQLITE):
                return
            from .db import LocalIndex

            LocalIndex(self.project).upsert_claim(
                work_id=row.work_id,
                owner=row.owner,
                status=row.status,
                phase=row.phase,
                note=row.note,
                ts=row.updated,
            )
        except Exception:
            pass

    def discover_work_ids(self) -> list[str]:
        seen: set[str] = set()
        canvas_dir = self.project.spdd_dir / "canvas"
        if canvas_dir.is_dir():
            for child in canvas_dir.glob("*.md"):
                if child.name != "README.md":
                    seen.add(child.stem)
        milestones = self.project.requirements_dir / "milestones"
        if milestones.is_dir():
            for child in milestones.glob("*.md"):
                if child.name != "README.md":
                    seen.add(child.stem)
        return sorted(seen)

    def refresh_done_status(self) -> None:
        for work_id in self.discover_work_ids():
            kind = canvas_mod.final_kind(self.project.canvas_path(work_id))
            if kind == "complete":
                target, note = "done", "canvas Final Status: Complete"
            elif kind == "cancelled":
                target, note = "cancelled", "canvas Final Status: Cancelled"
            else:
                continue
            existing = next((r for r in self.rows() if r.work_id == work_id), None)
            if existing and existing.status == "archived":
                continue
            if existing and existing.status == target:
                continue
            self.upsert(
                RegistryRow(
                    work_id=work_id,
                    status=target,
                    phase=existing.phase if existing else "sync",
                    operation=existing.operation if existing else "",
                    owner=self._owner(),
                    updated=_utc_now(),
                    note=note,
                ),
                event="refresh",
            )

    def claim(
        self,
        work_id: str,
        *,
        force: bool = False,
        phase: str | None = None,
        branch: str = "",
        pr: str = "",
        jira: str = "",
        note: str = "",
    ) -> RegistryRow:
        if not work_id:
            raise ValueError("claim requires a Work ID")
        from .local_sessions import is_local_id

        if is_local_id(work_id):
            raise PermissionError(
                f"claim refused: {work_id} is a local/offline session (machine-private). "
                "Promote it into a documented Work ID first:\n"
                f'  ./scripts/sdlc.sh local promote --type feature --name "..."'
            )
        existing = next((r for r in self.rows() if r.work_id == work_id), None)
        me = self._owner()
        if existing and existing.status == "active" and existing.owner and existing.owner != me and not force:
            raise PermissionError(
                f"claim refused: {work_id} is active under {existing.owner}. Use --force after coordinating."
            )
        state = self.workflow.resume(work_id, phase=phase, force=force)
        from .links import collect_links, upsert_note_token

        auto_jira = jira
        auto_github = ""
        if os.environ.get("SDLC_TEAM_AUTO_JIRA", "1") != "0" or os.environ.get(
            "SDLC_TEAM_AUTO_GITHUB", "1"
        ) != "0":
            links = collect_links(self.project, work_id, existing)
            if not auto_jira and os.environ.get("SDLC_TEAM_AUTO_JIRA", "1") != "0" and links.has_real_jira:
                auto_jira = links.jira_key
            if os.environ.get("SDLC_TEAM_AUTO_GITHUB", "1") != "0" and links.has_github:
                auto_github = links.github_number
        composed = note or (existing.note if existing else "")
        if branch:
            composed = upsert_note_token(composed, "branch", branch)
        if pr:
            composed = upsert_note_token(composed, "pr", pr)
        if auto_jira:
            composed = upsert_note_token(composed, "jira", auto_jira)
        if auto_github:
            composed = upsert_note_token(composed, "github", f"#{auto_github}")
        for tok in (note or "").split():
            if ":" not in tok and tok not in composed.split():
                composed = f"{composed} {tok}".strip()
        row = RegistryRow(
            work_id=work_id,
            status="active",
            phase=state.phase,
            operation=state.operation,
            owner=me,
            updated=_utc_now(),
            note=composed,
        )
        self.upsert(row, event="claim")
        self._fanout_claim_sqlite(row)
        return row

    def release(self, reason: str = "released") -> None:
        wid = self.workflow.pointer.get()
        if not wid:
            raise ValueError("release requires an active pointer")
        from .local_sessions import LocalSessionService, is_local_id

        if is_local_id(wid):
            LocalSessionService(self.project, self).shelf(reason, session_id=wid)
            return
        self.workflow.shelf(reason)
        row = RegistryRow(
            work_id=wid,
            status="shelved",
            phase=self.workflow.load_state(wid).phase,
            owner=self._owner(),
            updated=_utc_now(),
            note=reason,
        )
        self.upsert(row, event="release")
        self._fanout_claim_sqlite(row)

    def list_work_text(self) -> str:
        self.refresh_done_status()
        rows = {r.work_id: r for r in self.rows()}
        lines = [
            "Work IDs in this repository:",
            "",
            f"  {'WORK-ID':<40} {'REGISTRY':<12} {'PHASE':<8} {'OWNER':<10} ARTIFACTS",
        ]
        for wid in self.discover_work_ids():
            reg = rows.get(wid)
            status = reg.status if reg else "available"
            phase = reg.phase if reg else "-"
            owner = reg.owner if reg else "-"
            arts = []
            if self.project.canvas_path(wid).is_file():
                arts.append("canvas")
            if self.project.milestone_path(wid).is_file():
                arts.append("milestone")
            lines.append(
                f"  {wid:<40} {status:<12} {phase or '-':<8} {owner or '-':<10} {','.join(arts) or '-'}"
            )
        lines.extend(
            [
                "",
                "Claim: ./scripts/sdlc.sh claim <WORK-ID> [--branch NAME] [--pr #N] [--jira KEY]",
                "Team:  ./scripts/sdlc.sh team",
                "Local: ./scripts/sdlc.sh local list   # offline sessions (not in registry)",
            ]
        )
        try:
            from .local_sessions import LocalSessionService

            local_rows = LocalSessionService(self.project).list_sessions()
            if local_rows:
                lines.extend(["", "Local/offline sessions on this machine:"])
                for s in local_rows:
                    lines.append(f"  {s.id:<40} {s.status:<10} {s.title}")
        except OSError:
            pass
        return "\n".join(lines) + "\n"

    def team_text(self) -> str:
        self.refresh_done_status()
        me = self._owner()
        pointer = self.workflow.pointer.get()
        reg_path = self.path
        try:
            rel = reg_path.resolve().relative_to(self.project.root.resolve())
            reg_label = str(rel)
        except ValueError:
            reg_label = str(reg_path)
        lines = [
            "SDLC Team View",
            "==============",
            f"You: {me}",
            f"Your local pointer: {pointer or '(none)'}",
            "",
            f"Team registry (commit {reg_label} to share):",
        ]
        rows = self.rows()
        if not rows:
            lines.append("  (empty)")
        else:
            lines.append(
                f"  {'WORK-ID':<36} {'STATUS':<14} {'PHASE':<10} {'OP':<6} {'OWNER':<16} NOTE"
            )
            for r in rows:
                mark = " (you)" if r.owner == me and r.work_id == pointer else ""
                lines.append(
                    f"  {r.work_id:<36} {r.status:<14} {(r.phase or '-'):<10} {(r.operation or '-'):<6} "
                    f"{(r.owner or '-'):<16} {r.updated}{mark}"
                )
        return "\n".join(lines) + "\n"
