"""Local planning sync: ROADMAP summary, link drift check/repair, milestone Linked Work."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import canvas as canvas_mod
from .links import (
    WorkLinks,
    collect_links,
    ensure_github_section,
    ensure_jira_section,
    parse_canvas_metadata,
    set_canvas_metadata_bullet,
    set_milestone_bullet,
    upsert_note_token,
)
from .project import Project
from .registry import RegistryRow, TeamRegistry
from .timeutil import utc_now as _utc_now


START_MARKER = "<!-- SDLC-SPDD-ROADMAP-SUMMARY:START -->"
END_MARKER = "<!-- SDLC-SPDD-ROADMAP-SUMMARY:END -->"


@dataclass
class DriftFinding:
    work_id: str
    code: str
    message: str
    repairable: bool = True


class LocalSyncService:
    def __init__(self, project: Project | None = None, registry: TeamRegistry | None = None) -> None:
        self.project = project or Project.resolve()
        self.registry = registry or TeamRegistry(self.project)

    def sync_roadmap(self, *, roadmap: str = "ROADMAP.md", dry_run: bool = False) -> str:
        roadmap_path = Path(roadmap)
        if not roadmap_path.is_absolute():
            roadmap_path = self.project.root / roadmap_path
        canvas_dir = self.project.root / "spdd" / "canvas"
        rows: list[str] = []
        files = sorted(canvas_dir.glob("*.md")) if canvas_dir.is_dir() else []
        for path in files:
            meta = parse_canvas_metadata(path)
            work_id = meta.get("work_id") or path.stem
            title = meta.get("title") or "TBD"
            work_type = meta.get("work_type") or "TBD"
            status = meta.get("status") or "TBD"
            milestone = meta.get("milestone") or "TBD"
            source_url = meta.get("source_url") or "TBD"
            rel = str(path.relative_to(self.project.root))
            rows.append(
                f"| {work_id} | {title} | {work_type} | {status} | {milestone} | {source_url} | {rel} |"
            )
        if not rows:
            rows = ["| none | - | - | - | - | - | - |"]
        summary = "\n".join(
            [
                "",
                "## SDLC-SPDD Work Summary",
                "",
                f"Generated: {_utc_now()}",
                "",
                "| Work ID | Title | Type | Status | Milestone | Source | Canvas |",
                "|---------|-------|------|--------|-----------|--------|--------|",
                *rows,
                "",
            ]
        )
        block = f"{START_MARKER}\n{summary}{END_MARKER}"
        if dry_run:
            return block
        if not roadmap_path.is_file():
            roadmap_path.write_text(f"# Roadmap\n\n{block}\n", encoding="utf-8")
            return block
        text = roadmap_path.read_text(encoding="utf-8")
        if START_MARKER in text and END_MARKER in text:
            pattern = re.compile(
                re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
                re.DOTALL,
            )
            text = pattern.sub(block, text, count=1)
        else:
            text = text.rstrip() + "\n\n" + block + "\n"
        roadmap_path.write_text(text, encoding="utf-8")
        return block

    def _all_work_ids(self) -> list[str]:
        return self.registry.discover_work_ids()

    def check_links(self, work_id: str | None = None) -> list[DriftFinding]:
        findings: list[DriftFinding] = []
        ids = [work_id] if work_id else self._all_work_ids()
        rows = {r.work_id: r for r in self.registry.rows()}
        for wid in ids:
            links = collect_links(self.project, wid, rows.get(wid))
            findings.extend(self._findings_for(links))
        # ROADMAP staleness: if markers missing or summary older than newest canvas mtime — soft check
        roadmap = self.project.root / "ROADMAP.md"
        if roadmap.is_file():
            text = roadmap.read_text(encoding="utf-8")
            if START_MARKER not in text or END_MARKER not in text:
                findings.append(
                    DriftFinding(
                        work_id="*",
                        code="roadmap_summary_missing",
                        message="ROADMAP.md missing SDLC-SPDD summary markers; run sync-roadmap",
                    )
                )
        return findings

    def _findings_for(self, links: WorkLinks) -> list[DriftFinding]:
        out: list[DriftFinding] = []
        wid = links.work_id
        if links.milestone_req is None:
            out.append(
                DriftFinding(
                    wid,
                    "missing_milestone_req",
                    "no requirements/milestones/<WORK-ID>.md",
                    repairable=False,
                )
            )
        else:
            text = links.milestone_req.read_text(encoding="utf-8")
            if "## Jira" not in text:
                out.append(DriftFinding(wid, "missing_jira_section", "milestone requirement missing ## Jira"))
            elif not links.has_real_jira:
                out.append(
                    DriftFinding(
                        wid,
                        "jira_key_tbd",
                        "Jira Key is TBD/missing — create issue then set Key",
                        repairable=False,
                    )
                )
            if "## GitHub" not in text:
                out.append(
                    DriftFinding(
                        wid,
                        "missing_github_section",
                        "milestone requirement missing ## GitHub (optional but recommended)",
                    )
                )
        if links.has_real_jira and links.registry_status and not links.registry_jira:
            out.append(
                DriftFinding(
                    wid,
                    "registry_missing_jira",
                    f"registry row lacks jira:{links.jira_key}",
                )
            )
        if links.has_real_jira and links.canvas and links.canvas_source_issue != links.jira_key:
            out.append(
                DriftFinding(
                    wid,
                    "canvas_source_issue_mismatch",
                    f"canvas Source Issue '{links.canvas_source_issue}' != Jira Key '{links.jira_key}'",
                )
            )
        if links.has_github and links.registry_status and not links.registry_github:
            out.append(
                DriftFinding(
                    wid,
                    "registry_missing_github",
                    f"registry row lacks github:#{links.github_number}",
                )
            )
        if links.planning_milestone:
            status = self._linked_work_status(links.planning_milestone, wid)
            desired = self._desired_linked_status(links)
            if status is not None and desired and status != desired and status.split()[0].lower() != desired.split()[0].lower():
                out.append(
                    DriftFinding(
                        wid,
                        "linked_work_status_drift",
                        f"milestone Linked Work status '{status}' vs derived '{desired}'",
                    )
                )
        elif links.milestone_req is not None:
            out.append(
                DriftFinding(
                    wid,
                    "not_in_planning_milestone",
                    "Work ID not referenced in any milestone-*.md Linked Work/checklist",
                    repairable=False,
                )
            )
        return out

    def _desired_linked_status(self, links: WorkLinks) -> str:
        if links.registry_status in {"done", "archived"}:
            return "Complete"
        if links.registry_status == "cancelled":
            return "Cancelled"
        if links.canvas:
            kind = canvas_mod.final_kind(links.canvas)
            if kind == "complete":
                return "Complete"
            if kind == "cancelled":
                return "Cancelled"
            if links.canvas_status:
                return links.canvas_status
        if links.registry_status == "active":
            return "In Progress"
        return links.canvas_status or links.registry_status or ""

    def _linked_work_status(self, milestone: Path, work_id: str) -> str | None:
        lines = milestone.read_text(encoding="utf-8").splitlines()
        status_idx = 3  # default for | Work ID | Canvas | Requirement | Status | ...
        for line in lines:
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not cells:
                continue
            lower = [c.lower() for c in cells]
            if "work id" in lower and "status" in lower:
                status_idx = lower.index("status")
                continue
            if cells[0].startswith("---"):
                continue
            if cells[0] == work_id and len(cells) > status_idx:
                return cells[status_idx]
        return None

    def repair_links(self, work_id: str | None = None, *, dry_run: bool = False) -> list[str]:
        actions: list[str] = []
        ids = [work_id] if work_id else self._all_work_ids()
        rows = {r.work_id: r for r in self.registry.rows()}
        for wid in ids:
            links = collect_links(self.project, wid, rows.get(wid))
            if links.milestone_req:
                if ensure_jira_section(links.milestone_req):
                    actions.append(f"{wid}: added ## Jira section")
                if ensure_github_section(links.milestone_req):
                    actions.append(f"{wid}: added ## GitHub section")
            if links.has_real_jira:
                if links.canvas:
                    if dry_run:
                        actions.append(f"{wid}: would set canvas Source Issue/System/URL from Jira")
                    else:
                        if set_canvas_metadata_bullet(links.canvas, "Source System", "Jira"):
                            actions.append(f"{wid}: canvas Source System=Jira")
                        if set_canvas_metadata_bullet(links.canvas, "Source Issue", links.jira_key):
                            actions.append(f"{wid}: canvas Source Issue={links.jira_key}")
                        url = links.canvas_source_url
                        if not url:
                            # leave URL blank unless already known; optional env base
                            import os

                            base = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
                            if base:
                                url = f"{base}/browse/{links.jira_key}"
                                if set_canvas_metadata_bullet(links.canvas, "Source URL", url):
                                    actions.append(f"{wid}: canvas Source URL set")
                row = rows.get(wid)
                if row and not links.registry_jira:
                    note = upsert_note_token(row.note, "jira", links.jira_key)
                    if dry_run:
                        actions.append(f"{wid}: would set registry jira:{links.jira_key}")
                    else:
                        self.registry.upsert(
                            RegistryRow(
                                work_id=wid,
                                status=row.status,
                                phase=row.phase,
                                operation=row.operation,
                                owner=row.owner or self.registry._owner(),
                                updated=_utc_now(),
                                note=note,
                            )
                        )
                        actions.append(f"{wid}: registry jira:{links.jira_key}")
            if links.has_github:
                row = rows.get(wid)
                if row and not links.registry_github:
                    note = upsert_note_token(row.note, "github", f"#{links.github_number}")
                    if dry_run:
                        actions.append(f"{wid}: would set registry github:#{links.github_number}")
                    else:
                        self.registry.upsert(
                            RegistryRow(
                                work_id=wid,
                                status=row.status,
                                phase=row.phase,
                                operation=row.operation,
                                owner=row.owner or self.registry._owner(),
                                updated=_utc_now(),
                                note=note,
                            )
                        )
                        actions.append(f"{wid}: registry github:#{links.github_number}")
                if links.canvas and not links.canvas_source_issue and not links.has_real_jira:
                    if dry_run:
                        actions.append(f"{wid}: would set canvas Source from GitHub #{links.github_number}")
                    else:
                        set_canvas_metadata_bullet(links.canvas, "Source System", "GitHub")
                        set_canvas_metadata_bullet(links.canvas, "Source Issue", f"#{links.github_number}")
                        if links.github_url:
                            set_canvas_metadata_bullet(links.canvas, "Source URL", links.github_url)
                        actions.append(f"{wid}: canvas Source Issue=#{links.github_number}")
            if links.planning_milestone:
                desired = self._desired_linked_status(links)
                if desired:
                    changed = self._set_linked_work_status(
                        links.planning_milestone, wid, desired, dry_run=dry_run
                    )
                    if changed:
                        actions.append(f"{wid}: Linked Work status -> {desired}")
        return actions

    def _set_linked_work_status(
        self, milestone: Path, work_id: str, status: str, *, dry_run: bool
    ) -> bool:
        lines = milestone.read_text(encoding="utf-8").splitlines()
        status_idx = 3
        changed = False
        for i, line in enumerate(lines):
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not cells:
                continue
            lower = [c.lower() for c in cells]
            if "work id" in lower and "status" in lower:
                status_idx = lower.index("status")
                continue
            if cells[0].startswith("---"):
                continue
            if cells[0] != work_id or len(cells) <= status_idx:
                continue
            if cells[status_idx] == status:
                return False
            if dry_run:
                return True
            cells[status_idx] = status
            lines[i] = "| " + " | ".join(cells) + " |"
            changed = True
            break
        if changed:
            milestone.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return changed

    def links_report(self, work_id: str | None = None) -> str:
        ids = [work_id] if work_id else self._all_work_ids()
        rows = {r.work_id: r for r in self.registry.rows()}
        lines = [
            "Work link map",
            "=============",
            f"{'WORK-ID':<40} {'JIRA':<12} {'GITHUB':<10} {'REG':<10} {'CANVAS-SRC':<14} DRIFT",
        ]
        findings = {f.work_id: [] for f in self.check_links(work_id)}
        for f in self.check_links(work_id):
            findings.setdefault(f.work_id, []).append(f.code)
        for wid in ids:
            links = collect_links(self.project, wid, rows.get(wid))
            drift = ",".join(findings.get(wid, [])) or "-"
            lines.append(
                f"{wid:<40} {(links.jira_key or ('TBD' if links.jira_draft else '-')):<12} "
                f"{('#' + links.github_number) if links.github_number else '-':<10} "
                f"{(links.registry_status or '-'):<10} "
                f"{(links.canvas_source_issue or '-'):<14} {drift}"
            )
        return "\n".join(lines) + "\n"
