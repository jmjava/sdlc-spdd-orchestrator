"""Team Work ID registry — lean JSONL (#84) + legacy TSV during transition."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import canvas as canvas_mod
from .project import Project
from .workflow import WorkflowEngine

LEAN_REGISTRY_REL = Path("spdd/memory/registry.jsonl")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


REGISTRY_HEADER = """# Team Work Registry — tab-separated. Commit updates so teammates see who is on which Work ID.
# Columns: work_id status phase operation owner updated note
# status: active | shelved | done | cancelled | archived | available
# note tokens: branch:<name> pr:<url-or-#> jira:<KEY> <free text>
# Prefer lean spdd/memory/registry.jsonl for new events (#84); TSV remains readable.
work_id\tstatus\tphase\toperation\towner\tupdated\tnote
"""


@dataclass
class RegistryRow:
    work_id: str
    status: str
    phase: str = ""
    operation: str = ""
    owner: str = ""
    updated: str = ""
    note: str = ""

    def as_tsv(self) -> str:
        return "\t".join(
            [
                self.work_id,
                self.status,
                self.phase,
                self.operation,
                self.owner,
                self.updated,
                self.note,
            ]
        )


class TeamRegistry:
    def __init__(self, project: Project | None = None, workflow: WorkflowEngine | None = None) -> None:
        self.project = project or Project.resolve()
        self.workflow = workflow or WorkflowEngine(self.project)
        self.project.ensure_runtime_dirs()

    @property
    def path(self) -> Path:
        return self.project.registry_path

    @property
    def lean_path(self) -> Path:
        return self.project.root / LEAN_REGISTRY_REL

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
        if not self.path.is_file():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(REGISTRY_HEADER, encoding="utf-8")

    def rows(self) -> list[RegistryRow]:
        self.ensure()
        out: list[RegistryRow] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or line.startswith("work_id"):
                continue
            parts = line.split("\t")
            while len(parts) < 7:
                parts.append("")
            out.append(
                RegistryRow(
                    work_id=parts[0],
                    status=parts[1],
                    phase=parts[2],
                    operation=parts[3],
                    owner=parts[4],
                    updated=parts[5],
                    note=parts[6],
                )
            )
        return out

    def upsert(self, row: RegistryRow) -> None:
        self.ensure()
        rows = self.rows()
        found = False
        for i, existing in enumerate(rows):
            if existing.work_id == row.work_id:
                if not row.note:
                    row.note = existing.note
                rows[i] = row
                found = True
                break
        if not found:
            rows.append(row)
        comments = [ln for ln in self.path.read_text(encoding="utf-8").splitlines() if ln.startswith("#")]
        body = comments + ["work_id\tstatus\tphase\toperation\towner\tupdated\tnote"] + [r.as_tsv() for r in rows]
        tmp = self.path.with_suffix(".tsv.tmp")
        tmp.write_text("\n".join(body) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def append_lean_event(
        self,
        *,
        event: str,
        work_id: str,
        status: str = "",
        phase: str = "",
        owner: str = "",
        note: str = "",
        ts: str = "",
    ) -> dict:
        """Append claim/release/shelf event to lean git registry.jsonl (#84)."""
        payload = {
            "event": event,
            "work_id": work_id,
            "status": status,
            "phase": phase,
            "owner": owner or self._owner(),
            "note": note,
            "ts": ts or _utc_now(),
        }
        self.lean_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lean_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return payload

    def lean_events(self, *, work_id: str = "") -> list[dict]:
        if not self.lean_path.is_file():
            return []
        out: list[dict] = []
        for line in self.lean_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if work_id and row.get("work_id") != work_id:
                continue
            out.append(row)
        return out

    def _fanout_claim_sqlite(self, row: "RegistryRow") -> None:
        try:
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
            # Soft-fail: git registry remains source of truth for multi-user.
            pass

    def discover_work_ids(self) -> list[str]:
        seen: set[str] = set()
        features = self.project.root / "agent-context" / "features"
        if features.is_dir():
            for child in features.iterdir():
                if child.is_dir() and child.name not in {"archive"} and not child.name.startswith("."):
                    seen.add(child.name)
        canvas_dir = self.project.root / "spdd" / "canvas"
        if canvas_dir.is_dir():
            for child in canvas_dir.glob("*.md"):
                if child.name != "README.md":
                    seen.add(child.stem)
        milestones = self.project.root / "requirements" / "milestones"
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
                )
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
        # Auto-read links from requirements/milestones/<WORK-ID>.md (shell parity).
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
        tokens: list[str] = []
        composed = note or (existing.note if existing else "")
        if branch:
            composed = upsert_note_token(composed, "branch", branch)
        if pr:
            composed = upsert_note_token(composed, "pr", pr)
        if auto_jira:
            composed = upsert_note_token(composed, "jira", auto_jira)
        if auto_github:
            composed = upsert_note_token(composed, "github", f"#{auto_github}")
        # Preserve leftover free-text tokens not managed above.
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
        self.upsert(row)
        self.append_lean_event(
            event="claim",
            work_id=work_id,
            status=row.status,
            phase=row.phase,
            owner=row.owner,
            note=row.note,
            ts=row.updated,
        )
        self._fanout_claim_sqlite(row)
        return row

    def release(self, reason: str = "released") -> None:
        wid = self.workflow.pointer.get()
        if not wid:
            raise ValueError("release requires an active pointer")
        from .local_sessions import LocalSessionService, is_local_id

        if is_local_id(wid):
            # Keep LOCAL sessions out of the committed team registry.
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
        self.upsert(row)
        self.append_lean_event(
            event="release",
            work_id=wid,
            status=row.status,
            phase=row.phase,
            owner=row.owner,
            note=row.note,
            ts=row.updated,
        )
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
            if self.project.feature_dir(wid).is_dir():
                arts.append("feature")
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
        lines = [
            "SDLC Team View",
            "==============",
            f"You: {me}",
            f"Your local pointer: {pointer or '(none)'}",
            "",
            "Team registry (commit agent-context/work-registry.tsv to share):",
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
