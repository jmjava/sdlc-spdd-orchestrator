"""Local/offline work sessions — machine-private until promoted to a Work ID.

Detached agents often start coding without a FEAT/SPIKE. Local sessions give that
work a first-class identity (LOCAL-NNN-slug) under gitignored `.sdlc/local-sessions/`
so it can be shelved, resumed, and later promoted into a documented feature.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .pointer import PointerStore
from .project import Project
from .registry import TeamRegistry

LOCAL_PREFIX = "LOCAL"
_STATUS_OPEN = "open"
_STATUS_SHELVED = "shelved"
_STATUS_PROMOTED = "promoted"
_STATUS_ABANDONED = "abandoned"

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


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_local_id(work_id: str | None) -> bool:
    return bool(work_id) and work_id.upper().startswith(f"{LOCAL_PREFIX}-")


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[\s_/]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "session"


@dataclass
class LocalSession:
    id: str
    title: str
    intent: str = ""
    status: str = _STATUS_OPEN
    owner: str = ""
    created: str = ""
    updated: str = ""
    shelved_reason: str = ""
    promoted_to: str = ""
    branch: str = ""
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict) -> "LocalSession":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            intent=data.get("intent", ""),
            status=data.get("status", _STATUS_OPEN),
            owner=data.get("owner", ""),
            created=data.get("created", ""),
            updated=data.get("updated", ""),
            shelved_reason=data.get("shelved_reason", ""),
            promoted_to=data.get("promoted_to", ""),
            branch=data.get("branch", ""),
            notes=list(data.get("notes") or []),
        )


class LocalSessionService:
    def __init__(
        self,
        project: Project | None = None,
        registry: TeamRegistry | None = None,
    ) -> None:
        self.project = project or Project.resolve()
        self.project.ensure_runtime_dirs()
        self.pointer = PointerStore(self.project)
        self.registry = registry or TeamRegistry(self.project)
        self.root = self.project.sdlc_dir / "local-sessions"
        self.root.mkdir(parents=True, exist_ok=True)

    def _owner(self) -> str:
        return (
            os.environ.get("SDLC_USER")
            or os.environ.get("USER")
            or os.environ.get("USERNAME")
            or "unknown"
        )

    def _dir(self, session_id: str) -> Path:
        return self.root / session_id

    def _meta_path(self, session_id: str) -> Path:
        return self._dir(session_id) / "session.json"

    def _intent_path(self, session_id: str) -> Path:
        return self._dir(session_id) / "intent.md"

    def _notes_path(self, session_id: str) -> Path:
        return self._dir(session_id) / "notes.md"

    def load(self, session_id: str) -> LocalSession:
        path = self._meta_path(session_id)
        if not path.is_file():
            raise FileNotFoundError(f"local session not found: {session_id}")
        return LocalSession.from_json(json.loads(path.read_text(encoding="utf-8")))

    def save(self, session: LocalSession) -> None:
        d = self._dir(session.id)
        d.mkdir(parents=True, exist_ok=True)
        session.updated = _utc_now()
        tmp = self._meta_path(session.id).with_suffix(".json.tmp")
        tmp.write_text(json.dumps(session.to_json(), indent=2) + "\n", encoding="utf-8")
        tmp.replace(self._meta_path(session.id))

    def list_sessions(self, *, include_closed: bool = False) -> list[LocalSession]:
        rows: list[LocalSession] = []
        if not self.root.is_dir():
            return rows
        for path in sorted(self.root.glob("*/session.json")):
            session = LocalSession.from_json(json.loads(path.read_text(encoding="utf-8")))
            if include_closed or session.status in {_STATUS_OPEN, _STATUS_SHELVED}:
                rows.append(session)
        return rows

    def _next_number(self, prefix: str) -> int:
        max_n = 0
        pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)-", re.IGNORECASE)
        roots = [
            self.project.root / "agent-context" / "features",
            self.project.root / "spdd" / "canvas",
            self.project.root / "requirements" / "milestones",
            self.root,
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

    def allocate_id(self, slug: str, *, prefix: str = LOCAL_PREFIX) -> str:
        n = self._next_number(prefix)
        return f"{prefix}-{n:03d}-{slugify(slug)}"

    def start(
        self,
        *,
        name: str = "",
        title: str = "",
        intent: str = "",
        branch: str = "",
    ) -> LocalSession:
        slug = slugify(name or title or intent or "offline-work")
        session_id = self.allocate_id(slug)
        now = _utc_now()
        session = LocalSession(
            id=session_id,
            title=title or name or slug.replace("-", " "),
            intent=intent.strip(),
            status=_STATUS_OPEN,
            owner=self._owner(),
            created=now,
            updated=now,
            branch=branch,
        )
        self._dir(session_id).mkdir(parents=True, exist_ok=True)
        self.save(session)
        intent_body = (
            f"# Local session: {session_id}\n\n"
            f"## Title\n\n{session.title}\n\n"
            f"## Intent\n\n{session.intent or '(not set — capture as you go)'}\n\n"
            "## Status\n\n"
            "Machine-private offline work. Not in team registry or milestones until promoted.\n\n"
            "```bash\n"
            f"./scripts/sdlc.sh local capture --summary \"...\"\n"
            f"./scripts/sdlc.sh local promote --type feature --name \"{session.title}\"\n"
            "```\n"
        )
        self._intent_path(session_id).write_text(intent_body, encoding="utf-8")
        self._notes_path(session_id).write_text(
            f"# Notes: {session_id}\n\n- Started {now}\n",
            encoding="utf-8",
        )
        # Auto-shelf previous pointer work without claiming into team registry for LOCAL.
        current = self.pointer.get()
        if current and current != session_id:
            if is_local_id(current):
                try:
                    prev = self.load(current)
                    if prev.status == _STATUS_OPEN:
                        prev.status = _STATUS_SHELVED
                        prev.shelved_reason = f"auto-shelf for local-start {session_id}"
                        self.save(prev)
                except FileNotFoundError:
                    pass
        self.pointer.set(session_id)
        self._write_session_brief(session)
        return session

    def _write_session_brief(self, session: LocalSession) -> None:
        # Default: keep briefs machine-private under .sdlc/ (offline until promote).
        brief = "\n".join(
            [
                f"# Current Session — {session.id}",
                "",
                "## Framework Orientation",
                "",
                f"- Work ID: `{session.id}` (**local/offline** — not a team Work ID)",
                f"- Title: {session.title}",
                f"- Status: {session.status}",
                f"- Owner: {session.owner}",
                f"- Intent: {session.intent or '(unset)'}",
                f"- Artifacts: `.sdlc/local-sessions/{session.id}/`",
                "",
                "## Resume Prompt",
                "",
                "This is a machine-private offline session. Do not invent a FEAT/SPIKE or",
                "write committed canvas/milestone artifacts until the human asks to promote.",
                "",
                "When ready to document:",
                f"  ./scripts/sdlc.sh local promote --type feature --name \"{session.title}\"",
                "",
                "Capture interim notes:",
                "  ./scripts/sdlc.sh local capture --summary \"what changed\"",
                "",
            ]
        )
        self._dir(session.id).mkdir(parents=True, exist_ok=True)
        (self._dir(session.id) / "brief.md").write_text(brief, encoding="utf-8")
        (self.project.sdlc_dir / "current-local-session.md").write_text(brief, encoding="utf-8")
        # Opt-in only: also write committed agent-context/sessions (usually unwanted).
        if os.environ.get("SDLC_LOCAL_WRITE_SESSION_BRIEF", "0") == "1":
            sessions = self.project.root / "agent-context" / "sessions"
            sessions.mkdir(parents=True, exist_ok=True)
            (sessions / "current-session.md").write_text(brief, encoding="utf-8")
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            (sessions / f"{stamp}-local-{session.id}.md").write_text(brief, encoding="utf-8")

    def status_text(self, session_id: str | None = None) -> str:
        sid = session_id or self.pointer.get()
        if not sid or not is_local_id(sid):
            open_rows = [s for s in self.list_sessions() if s.status == _STATUS_OPEN]
            lines = [
                "No active local session pointer.",
                "",
                "Start one:",
                '  ./scripts/sdlc.sh local start --name <slug> --intent "..."',
            ]
            if open_rows:
                lines.append("")
                lines.append("Open local sessions:")
                for s in open_rows:
                    lines.append(f"  {s.id}  {s.title}")
            return "\n".join(lines) + "\n"
        session = self.load(sid)
        notes_tail = ""
        notes_path = self._notes_path(sid)
        if notes_path.is_file():
            lines = notes_path.read_text(encoding="utf-8").splitlines()
            notes_tail = "\n".join(lines[-8:])
        return (
            f"Local session: {session.id}\n"
            f"Title: {session.title}\n"
            f"Status: {session.status}\n"
            f"Owner: {session.owner}\n"
            f"Intent: {session.intent or '(unset)'}\n"
            f"Promoted to: {session.promoted_to or '-'}\n"
            f"Path: .sdlc/local-sessions/{session.id}/\n"
            f"\nRecent notes:\n{notes_tail or '(none)'}\n"
        )

    def list_text(self, *, include_closed: bool = False) -> str:
        rows = self.list_sessions(include_closed=include_closed)
        if not rows:
            return (
                "No local/offline sessions.\n"
                'Start: ./scripts/sdlc.sh local start --name <slug> --intent "..."\n'
            )
        lines = [
            "Local/offline sessions (machine-private under .sdlc/local-sessions/)",
            "",
            f"{'ID':<40} {'STATUS':<10} TITLE",
        ]
        for s in rows:
            lines.append(f"{s.id:<40} {s.status:<10} {s.title}")
        lines.extend(
            [
                "",
                "Resume:  ./scripts/sdlc.sh local resume <LOCAL-ID>",
                "Promote: ./scripts/sdlc.sh local promote --type feature --name \"...\"",
            ]
        )
        return "\n".join(lines) + "\n"

    def capture(self, summary: str, *, session_id: str | None = None) -> LocalSession:
        sid = session_id or self.pointer.get()
        if not sid or not is_local_id(sid):
            raise ValueError("local capture requires an active LOCAL-* pointer or --session")
        session = self.load(sid)
        if session.status not in {_STATUS_OPEN, _STATUS_SHELVED}:
            raise ValueError(f"cannot capture into {session.status} session {sid}")
        now = _utc_now()
        line = f"- [{now}] {summary.strip()}"
        session.notes.append(line)
        if session.status == _STATUS_SHELVED:
            session.status = _STATUS_OPEN
            session.shelved_reason = ""
        self.save(session)
        with self._notes_path(sid).open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        self.pointer.set(sid)
        self._write_session_brief(session)
        # Optional daily session-notes tag (committed) — only when explicitly wanted via env
        if os.environ.get("SDLC_LOCAL_SESSION_NOTES", "0") == "1":
            day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            notes_dir = self.project.root / "session-notes"
            notes_dir.mkdir(parents=True, exist_ok=True)
            path = notes_dir / f"{day}.md"
            block = f"\n### local:{sid}\n\n{summary.strip()}\n"
            if path.is_file():
                path.write_text(path.read_text(encoding="utf-8") + block, encoding="utf-8")
            else:
                path.write_text(f"# Session notes {day}\n{block}", encoding="utf-8")
        return session

    def shelf(self, reason: str = "manual shelf", *, session_id: str | None = None) -> LocalSession:
        sid = session_id or self.pointer.get()
        if not sid or not is_local_id(sid):
            raise ValueError("local shelf requires an active LOCAL-* pointer or --session")
        session = self.load(sid)
        session.status = _STATUS_SHELVED
        session.shelved_reason = reason
        self.save(session)
        if self.pointer.get() == sid:
            self.pointer.reset()
        return session

    def resume(self, session_id: str) -> LocalSession:
        session = self.load(session_id)
        if session.status == _STATUS_PROMOTED:
            raise ValueError(
                f"{session_id} already promoted to {session.promoted_to}; claim that Work ID instead"
            )
        if session.status == _STATUS_ABANDONED:
            raise ValueError(f"{session_id} was abandoned; start a new local session")
        current = self.pointer.get()
        if current and current != session_id and is_local_id(current):
            try:
                prev = self.load(current)
                if prev.status == _STATUS_OPEN:
                    prev.status = _STATUS_SHELVED
                    prev.shelved_reason = f"auto-shelf for resume {session_id}"
                    self.save(prev)
            except FileNotFoundError:
                pass
        session.status = _STATUS_OPEN
        session.shelved_reason = ""
        self.save(session)
        self.pointer.set(session_id)
        self._write_session_brief(session)
        return session

    def abandon(self, *, session_id: str | None = None, force: bool = False) -> LocalSession:
        sid = session_id or self.pointer.get()
        if not sid or not is_local_id(sid):
            raise ValueError("local abandon requires an active LOCAL-* pointer or --session")
        session = self.load(sid)
        if session.status == _STATUS_PROMOTED and not force:
            raise ValueError(f"{sid} already promoted; use --force to mark abandoned")
        session.status = _STATUS_ABANDONED
        self.save(session)
        if self.pointer.get() == sid:
            self.pointer.reset()
        return session

    def promote(
        self,
        *,
        work_type: str = "feature",
        name: str = "",
        session_id: str | None = None,
        milestone: str = "",
        claim: bool = True,
        dry_run: bool = False,
    ) -> tuple[LocalSession, str]:
        sid = session_id or self.pointer.get()
        if not sid or not is_local_id(sid):
            raise ValueError("local promote requires an active LOCAL-* pointer or --session")
        session = self.load(sid)
        if session.status == _STATUS_PROMOTED:
            raise ValueError(f"{sid} already promoted to {session.promoted_to}")
        if session.status == _STATUS_ABANDONED:
            raise ValueError(f"cannot promote abandoned session {sid}")
        prefix = _TYPE_PREFIX.get(work_type.lower(), "FEAT")
        title = name or session.title or session.id
        slug = slugify(title)
        work_id = f"{prefix}-{self._next_number(prefix):03d}-{slug}"
        if dry_run:
            return session, work_id

        intent = session.intent or "(promoted from local offline session — fill in)"
        notes_text = ""
        if self._notes_path(sid).is_file():
            notes_text = self._notes_path(sid).read_text(encoding="utf-8").strip()

        # Milestone requirement
        req_dir = self.project.root / "requirements" / "milestones"
        req_dir.mkdir(parents=True, exist_ok=True)
        req_path = req_dir / f"{work_id}.md"
        req_path.write_text(
            "\n".join(
                [
                    f"# Requirement: {work_id}",
                    "",
                    "## Summary",
                    "",
                    intent,
                    "",
                    "## Acceptance Criteria",
                    "",
                    "- [ ] Documented after local offline exploration",
                    "",
                    "## Provenance",
                    "",
                    f"- Promoted from local session `{sid}`",
                    f"- Local title: {session.title}",
                    "",
                    "## Jira",
                    "",
                    "- Key: TBD",
                    f"- Summary: {title}",
                    "",
                    "## GitHub",
                    "",
                    "- Number: TBD",
                    f"- Title: {title}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        # Stay-set progress only (#86) — do not create agent-context/features mirrors.
        progress = self.project.progress_log_path(work_id)
        progress.parent.mkdir(parents=True, exist_ok=True)
        if not progress.is_file():
            progress.write_text("# Progress Entries\n\n", encoding="utf-8")
        with progress.open("a", encoding="utf-8") as fh:
            fh.write(
                f"\n## {work_id}\n\n"
                f"- Promoted from local session `{sid}` at {_utc_now()}\n"
                f"- Intent: {intent}\n"
            )
            if notes_text:
                fh.write(f"\n### Notes from {sid}\n\n{notes_text}\n")

        # Canvas
        canvas_dir = self.project.root / "spdd" / "canvas"
        canvas_dir.mkdir(parents=True, exist_ok=True)
        work_type_label = {
            "FEAT": "Feature",
            "BUG": "Bugfix",
            "REF": "Refactor",
            "SPIKE": "Spike",
            "DOC": "Doc",
            "TEST": "Test",
            "CHORE": "Chore",
        }.get(prefix, "Feature")
        canvas = "\n".join(
            [
                f"# REASONS Canvas: {work_id} - {title}",
                "",
                "## Metadata",
                "",
                f"- Work ID: {work_id}",
                f"- Work Type: {work_type_label}",
                "- Status: Draft",
                f"- Created: {_utc_now()[:10]}",
                f"- Updated: {_utc_now()[:10]}",
                f"- Owner: {session.owner}",
                "- Source System: Local session",
                f"- Source Issue: {sid}",
                "- Roadmap: ROADMAP.md",
                f"- Milestone: {milestone or 'TBD'}",
                f"- Related local session: .sdlc/local-sessions/{sid}/",
                "",
                "## R - Requirements",
                "",
                "### User Goal",
                "",
                intent,
                "",
                "### Business / Product Goal",
                "",
                f"Promoted from offline exploration (`{sid}`).",
                "",
                "### Acceptance Criteria",
                "",
                "- [ ] Replace this draft with concrete acceptance criteria",
                "",
                "## E - Essentials",
                "",
                "- TBD after promotion",
                "",
                "## A - Architecture",
                "",
                "- TBD",
                "",
                "## S - Safeguards",
                "",
                "- Keep local-session provenance until first sync",
                "",
                "## Operations",
                "",
                "### T01 - Flesh out canvas from local notes",
                "",
                "- Status: Pending",
                "- Description: Incorporate notes from the local offline session.",
                "",
                "## Final Status",
                "",
                "- Status: Draft",
                "",
                "## Local session notes (imported)",
                "",
                notes_text or "(none)",
                "",
            ]
        )
        canvas_path = canvas_dir / f"{work_id}.md"
        canvas_path.write_text(canvas, encoding="utf-8")

        if milestone:
            self._append_linked_work(milestone, work_id, title)

        session.status = _STATUS_PROMOTED
        session.promoted_to = work_id
        self.save(session)
        # Leave a breadcrumb in intent
        with self._intent_path(sid).open("a", encoding="utf-8") as fh:
            fh.write(f"\n\n## Promoted\n\n- To: `{work_id}` at {_utc_now()}\n")

        if claim:
            self.registry.claim(work_id, note=f"promoted-from:{sid}")
        else:
            if self.pointer.get() == sid:
                self.pointer.reset()
        return session, work_id

    def _append_linked_work(self, milestone: str, work_id: str, title: str) -> None:
        path = Path(milestone)
        if not path.is_absolute():
            path = self.project.root / path
        if not path.is_file():
            return
        text = path.read_text(encoding="utf-8")
        if work_id in text:
            return
        row = (
            f"| {work_id} | spdd/canvas/{work_id}.md | "
            f"requirements/milestones/{work_id}.md | Draft | "
            f"Promoted from local session |"
        )
        if "## Linked Work" in text:
            # insert after header separator line of the table if present
            lines = text.splitlines()
            insert_at = None
            in_table = False
            for i, line in enumerate(lines):
                if line.strip() == "## Linked Work":
                    in_table = True
                    continue
                if in_table and line.startswith("|") and "---" in line:
                    insert_at = i + 1
                    # find end of table
                    j = i + 1
                    while j < len(lines) and lines[j].startswith("|"):
                        j += 1
                    insert_at = j
                    break
            if insert_at is None:
                text = text.rstrip() + "\n\n" + row + "\n"
            else:
                lines.insert(insert_at, row)
                text = "\n".join(lines) + "\n"
        else:
            text = (
                text.rstrip()
                + "\n\n## Linked Work\n\n"
                + "| Work ID | Canvas | Requirement | Status | Notes |\n"
                + "|---------|--------|-------------|--------|-------|\n"
                + row
                + "\n"
            )
        path.write_text(text, encoding="utf-8")

    def next_hint_lines(self) -> list[str]:
        """Extra lines for `sdlc next` when no documented Work ID is active."""
        open_rows = [s for s in self.list_sessions() if s.status in {_STATUS_OPEN, _STATUS_SHELVED}]
        lines = [
            "",
            "Offline / detached agent work:",
            '  ./scripts/sdlc.sh local start --name <slug> --intent "why this scratch work"',
            "  ./scripts/sdlc.sh local list",
        ]
        if open_rows:
            lines.append("  # open local sessions:")
            for s in open_rows[:5]:
                lines.append(f"  #   {s.id} ({s.status}) — {s.title}")
        return lines

    def next_text_for_active(self, session_id: str) -> str:
        session = self.load(session_id)
        return "\n".join(
            [
                "== SDLC: what to do now ==",
                f"Local offline session: {session.id}",
                f"Title: {session.title}",
                f"Status: {session.status}",
                f"Intent: {session.intent or '(unset — capture as you go)'}",
                "",
                "This work is machine-private (under .sdlc/local-sessions/).",
                "It is NOT in the team registry or milestones until promoted.",
                "",
                "Do now:",
                "  Keep coding against this LOCAL session id in your brief.",
                '  ./scripts/sdlc.sh local capture --summary "what changed"',
                "",
                "When ready to document as a feature:",
                f'  ./scripts/sdlc.sh local promote --type feature --name "{session.title}"',
                "  # optional: --milestone milestone-1.md",
                "",
                "Park without documenting:",
                '  ./scripts/sdlc.sh local shelf --reason "pause"',
                "",
            ]
        )
