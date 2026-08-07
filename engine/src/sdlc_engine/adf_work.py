"""Init SDLC-SPDD work (REASONS canvas + requirement) from a local ADF document."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .jira_format import adf_to_markdown, load_adf_document
from .local_sessions import slugify
from .pointer import PointerStore
from .project import Project
from .registry import TeamRegistry

_TYPE_PREFIX = {
    "feature": "FEAT",
    "feat": "FEAT",
    "bug": "BUG",
    "bugfix": "BUG",
    "refactor": "REF",
    "ref": "REF",
    "spike": "SPIKE",
    "doc": "DOC",
    "test": "TEST",
    "chore": "CHORE",
}

_TYPE_LABEL = {
    "FEAT": "Feature",
    "BUG": "Bugfix",
    "REF": "Refactor",
    "SPIKE": "Spike",
    "DOC": "Doc",
    "TEST": "Test",
    "CHORE": "Chore",
}

_ISSUE_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")
_WORK_ID_RE = re.compile(
    r"^(FEAT|BUG|REF|SPIKE|DOC|TEST|CHORE)-\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*$",
    re.IGNORECASE,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _first_heading(doc: dict[str, Any]) -> str:
    for node in doc.get("content") or []:
        if not isinstance(node, dict) or node.get("type") != "heading":
            continue
        parts: list[str] = []
        for child in node.get("content") or []:
            if isinstance(child, dict) and child.get("type") == "text":
                parts.append(str(child.get("text") or ""))
        text = "".join(parts).strip()
        if text:
            return text
    return ""


def _stem_title(path: Path) -> str:
    name = path.name
    if name.endswith(".adf.json"):
        name = name[: -len(".adf.json")]
    else:
        name = path.stem
    return name.replace("_", " ").replace("-", " ").strip() or "adf-work"


def infer_issue_key(path: Path, title: str = "") -> str:
    for candidate in (path.name, path.stem, title):
        m = _ISSUE_KEY_RE.search(candidate or "")
        if m:
            return m.group(1)
    return ""


@dataclass
class AdfInitResult:
    work_id: str
    title: str
    adf_path: str
    canvas_path: str
    requirement_path: str
    feature_dir: str
    source_issue: str
    next_command: str
    dry_run: bool = False


class AdfWorkService:
    """Create draft REASONS canvas + requirement from a browsed ADF file."""

    def __init__(self, project: Project) -> None:
        self.project = project
        self.pointer = PointerStore(project)
        self.registry = TeamRegistry(project)

    def _next_number(self, prefix: str) -> int:
        max_n = 0
        pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)-", re.IGNORECASE)
        roots = [
            self.project.root / "agent-context" / "features",
            self.project.root / "spdd" / "canvas",
            self.project.root / "requirements" / "milestones",
        ]
        for base in roots:
            if not base.is_dir():
                continue
            for child in base.iterdir():
                name = child.stem if child.is_file() else child.name
                m = pattern.match(name)
                if m:
                    max_n = max(max_n, int(m.group(1)))
        return max_n + 1

    def _resolve_adf(self, adf_path: str | Path) -> Path:
        raw = Path(adf_path).expanduser()
        if not raw.is_absolute():
            raw = (self.project.root / raw).resolve()
        else:
            raw = raw.resolve()
        if not raw.is_file():
            raise FileNotFoundError(f"ADF file not found: {raw}")
        return raw

    def _load_markdown(self, path: Path) -> tuple[dict[str, Any], str]:
        data = json.loads(path.read_text(encoding="utf-8"))
        doc = load_adf_document(data)
        return doc, adf_to_markdown(doc).strip()

    def allocate_work_id(self, *, work_type: str, title: str, work_id: str = "") -> str:
        if work_id:
            wid = work_id.strip()
            if not _WORK_ID_RE.match(wid):
                raise ValueError(
                    f"Invalid work_id '{wid}' — expected PREFIX-NNN-slug "
                    "(e.g. FEAT-013-adf-init-reasons-canvas)"
                )
            return wid
        prefix = _TYPE_PREFIX.get(work_type.lower(), "FEAT")
        slug = slugify(title) or "adf-work"
        return f"{prefix}-{self._next_number(prefix):03d}-{slug}"

    def _claim_blocker(self, work_id: str) -> str | None:
        """Return an error message if another owner already holds an active claim."""
        existing = next((r for r in self.registry.rows() if r.work_id == work_id), None)
        if not existing or existing.status != "active" or not existing.owner:
            return None
        me = self.registry._owner()
        if existing.owner != me:
            return (
                f"claim refused: {work_id} is active under {existing.owner}. "
                "Use --no-claim or coordinate / force-claim separately."
            )
        return None

    def init_from_adf(
        self,
        adf_path: str | Path,
        *,
        work_type: str = "feature",
        title: str = "",
        work_id: str = "",
        claim: bool = True,
        dry_run: bool = False,
    ) -> AdfInitResult:
        path = self._resolve_adf(adf_path)
        doc, body_md = self._load_markdown(path)
        resolved_title = (title or _first_heading(doc) or _stem_title(path)).strip()
        wid = self.allocate_work_id(work_type=work_type, title=resolved_title, work_id=work_id)
        prefix = wid.split("-", 1)[0].upper()
        work_type_label = _TYPE_LABEL.get(prefix, "Feature")
        source_issue = infer_issue_key(path, resolved_title)

        try:
            rel_adf = str(path.relative_to(self.project.root))
        except ValueError:
            rel_adf = str(path)

        canvas_rel = f"spdd/canvas/{wid}.md"
        req_rel = f"requirements/milestones/{wid}.md"
        next_cmd = f"/sdlc-spdd-analysis @{req_rel}"

        if dry_run:
            return AdfInitResult(
                work_id=wid,
                title=resolved_title,
                adf_path=rel_adf,
                canvas_path=canvas_rel,
                requirement_path=req_rel,
                feature_dir="",
                source_issue=source_issue,
                next_command=next_cmd,
                dry_run=True,
            )

        existing_canvas = self.project.root / canvas_rel
        if existing_canvas.is_file():
            raise FileExistsError(f"Canvas already exists: {canvas_rel}")

        if claim and not dry_run:
            blocked = self._claim_blocker(wid)
            if blocked:
                raise PermissionError(blocked)

        self.project.ensure_runtime_dirs()
        now = _utc_now()
        body_block = body_md or "(empty ADF body)"

        canvas = "\n".join(
            [
                f"# REASONS Canvas: {wid} - {resolved_title}",
                "",
                "## Metadata",
                "",
                f"- Work ID: {wid}",
                f"- Work Type: {work_type_label}",
                "- Status: Draft",
                "- Readiness: Needs Analysis",
                f"- Created: {now}",
                f"- Updated: {now}",
                "- Owner:",
                "- Target Project:",
                "- Stack:",
                "- Source System: ADF",
                f"- Source Issue: {source_issue}",
                "- Source URL:",
                "- Docs URL:",
                "- Roadmap: ROADMAP.md",
                "- Milestone:",
                f"- Source ADF: {rel_adf}",
                "- Related PR:",
                "",
                "## R - Requirements",
                "",
                "### User Goal",
                "",
                resolved_title,
                "",
                "### Business / Product Goal",
                "",
                f"Seeded from ADF document `{rel_adf}`. Refine during analysis.",
                "",
                "### Acceptance Criteria",
                "",
                "- [ ] Derive acceptance criteria from the ADF source during analysis.",
                "",
                "### Non-Goals",
                "",
                "- TBD",
                "",
                "### Assumptions",
                "",
                f"- Created from local ADF: `{rel_adf}`",
                "",
                "### Open Questions",
                "",
                "- What acceptance criteria and scope boundaries apply?",
                "",
                "### Source ADF (markdown)",
                "",
                body_block,
                "",
                "## E - Entities",
                "",
                "### Domain Entities",
                "",
                "- TBD",
                "",
                "### Application Components",
                "",
                "- TBD",
                "",
                "### External Systems",
                "",
                "- TBD",
                "",
                "### Data / Persistence",
                "",
                "- TBD",
                "",
                "### Files Likely Affected",
                "",
                "- TBD",
                "",
                "## A - Approach",
                "",
                "### Proposed Approach",
                "",
                "TBD during `/sdlc-spdd-plan` and `/sdlc-spdd-architect`.",
                "",
                "### Alternatives Considered",
                "",
                "- TBD",
                "",
                "### Trade-Offs",
                "",
                "- TBD",
                "",
                "### Risks",
                "",
                "- TBD",
                "",
                "### Failure Modes",
                "",
                "- TBD",
                "",
                "## S - Structure",
                "",
                "### Files To Add",
                "",
                "- TBD",
                "",
                "### Files To Modify",
                "",
                "- TBD",
                "",
                "### Package / Module Structure",
                "",
                "TBD",
                "",
                "### Test Structure",
                "",
                "TBD",
                "",
                "### Documentation Structure",
                "",
                "TBD",
                "",
                "## O - Operations",
                "",
                "### T01 - Clarify and plan",
                "",
                "- Status: Not Started",
                "- Description: Convert the ADF-sourced draft into a complete REASONS Canvas via analysis/plan/architect.",
                f"- Files: {canvas_rel}",
                "- Tests: Not applicable",
                "- Validation: Canvas review",
                "",
                "## N - Norms",
                "",
                "### General",
                "",
                "- Follow existing project conventions.",
                "- Keep implementation aligned with this canvas.",
                "- Do not invent requirements that were not requested.",
                "- Update the canvas before behavior changes.",
                "",
                "### Testing",
                "",
                "- Add or update tests for behavior changes.",
                "- Document tests that could not be run.",
                "",
                "## S - Safeguards",
                "",
                "- Do not code until the canvas is Ready For Coding.",
                "- Do not implement behavior changes until this canvas is updated with `/sdlc-spdd-prompt-update`.",
                "- Do not let implementation drift from this canvas without running `/sdlc-spdd-sync`.",
                "",
                "## Review Checklist",
                "",
                "- [ ] Requirements satisfied",
                "- [ ] Entities updated correctly",
                "- [ ] Approach followed or synced",
                "- [ ] Structure followed or synced",
                "- [ ] Operations completed",
                "- [ ] Norms followed",
                "- [ ] Safeguards respected",
                "- [ ] Tests added or updated",
                "- [ ] No unrelated refactors",
                "- [ ] Documentation updated if needed",
                "",
                "## Sync Notes",
                "",
                f"Created from ADF `{rel_adf}`. Use sync notes to track drift between the source ADF, canvas, and implementation.",
                "",
                "## Final Status",
                "",
                "- Status:",
                "- Completed Date:",
                "- PR:",
                "- Follow-Up Tasks:",
                "",
            ]
        )

        req = "\n".join(
            [
                "---",
                f'work_id: "{wid}"',
                f'jira_key: "{source_issue}"',
                'jira_epic: ""',
                'jira_type: "Story"',
                'jira_status: "To Do"',
                'jira_assignee: ""',
                'jira_due_date: ""',
                'jira_sprint: ""',
                'milestone: ""',
                "blocks: []",
                "depends_on: []",
                "related: []",
                "---",
                "",
                f"# Requirement: {wid}",
                "",
                "## Summary",
                "",
                resolved_title,
                "",
                "## Source",
                "",
                f"- ADF: `{rel_adf}`",
                f"- Source Issue: {source_issue or '(none inferred)'}",
                "- Derived from local ADF document",
                "",
                "## Description",
                "",
                body_block,
                "",
                "## Acceptance Criteria",
                "",
                "- [ ] Refine during `/sdlc-spdd-analysis`",
                "",
                "## Next",
                "",
                next_cmd,
                "",
            ]
        )

        canvas_path = self.project.root / canvas_rel
        req_path = self.project.root / req_rel
        # Stay-set only (#86) — do not create agent-context/features mirrors.
        canvas_path.parent.mkdir(parents=True, exist_ok=True)
        req_path.parent.mkdir(parents=True, exist_ok=True)
        progress = self.project.root / "spdd" / "memory" / "entries" / "progress.md"
        progress.parent.mkdir(parents=True, exist_ok=True)

        canvas_path.write_text(canvas, encoding="utf-8")
        req_path.write_text(req, encoding="utf-8")
        if not progress.is_file():
            progress.write_text("# Progress Entries\n\n", encoding="utf-8")
        with progress.open("a", encoding="utf-8") as fh:
            fh.write(
                f"\n## {wid}\n\n"
                f"- {now} — Draft canvas created from ADF `{rel_adf}`\n"
                f"- Next: {next_cmd}\n"
            )

        if claim:
            self.registry.claim(wid, note=f"init-from-adf:{rel_adf}", phase="analysis")
        else:
            self.pointer.set(wid)

        return AdfInitResult(
            work_id=wid,
            title=resolved_title,
            adf_path=rel_adf,
            canvas_path=canvas_rel,
            requirement_path=req_rel,
            feature_dir="",  # deprecated; stay-set only
            source_issue=source_issue,
            next_command=next_cmd,
            dry_run=False,
        )
