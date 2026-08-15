"""Local regenerable SQLite index — opt-in cache rebuilt from ledger + stay-set.

The binary DB lives under gitignored ``.sdlc/index.sqlite``. Multi-user sync stays
git (ledger JSONL + registry JSONL + markdown). Rebuild anytime from on-disk artifacts.
"""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from . import canvas as canvas_mod
from .db_query import IndexQueryMixin, format_rows
from .db_rebuild import IndexRebuildMixin
from .db_schema import (
    DEFAULT_DB_NAME,
    NODE_AREA,
    NODE_CANVAS,
    NODE_CLAIM,
    NODE_REQUIREMENT,
    NODE_SESSION,
    NODE_WORK,
    REL_AREA,
    REL_CANVAS,
    REL_FOR_WORK,
    REL_REASONS,
    REL_REQUIREMENT,
    SCHEMA_VERSION,
    RebuildStats,
    init_schema,
)
from .lessons_ledger import LessonRecord
from .links import collect_links, parse_canvas_metadata, parse_milestone_requirement
from .project import Project
from .registry import TeamRegistry
from .timeutil import utc_now as _utc_now

# Re-export the public surface so existing `from sdlc_engine.db import …` keeps working.
__all__ = [
    "DEFAULT_DB_NAME",
    "LocalIndex",
    "RebuildStats",
    "SCHEMA_VERSION",
    "format_rows",
]


class LocalIndex(IndexRebuildMixin, IndexQueryMixin):
    """Regenerable SQLite index of Work IDs, registry, and artifact paths."""

    def __init__(self, project: Project | None = None, db_path: Path | None = None) -> None:
        self.project = project or Project.resolve()
        self.project.ensure_runtime_dirs()
        self.db_path = db_path or (self.project.sdlc_dir / DEFAULT_DB_NAME)

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _git_head(self) -> str:
        try:
            return subprocess.check_output(
                ["git", "-C", str(self.project.root), "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        init_schema(conn)

    def _rel(self, path: Path) -> str:
        return self.project.rel(path)

    def _meta(self, conn: sqlite3.Connection, key: str) -> str:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else ""

    def status_dict(self) -> dict[str, Any]:
        """Machine-readable index status for CLI JSON / ops dashboard."""
        base: dict[str, Any] = {
            "path": str(self.db_path),
            "exists": self.db_path.is_file(),
            "schema": None,
            "fts": None,
            "rebuilt_at": None,
            "source_commit": None,
            "work_items": 0,
            "requirements": 0,
            "canvases": 0,
            "areas": 0,
            "lessons": 0,
            "staged_lessons": 0,
            "context_entries": 0,
            "domain_keywords": 0,
            "edges": 0,
            "artifacts": 0,
            "local_sessions": 0,
            "by_registry_status": {},
            "error": None,
        }
        if not self.db_path.is_file():
            base["error"] = "missing"
            return base
        with self.connect() as conn:
            try:
                base["work_items"] = conn.execute(
                    "SELECT COUNT(*) AS n FROM work_items"
                ).fetchone()["n"]
                base["artifacts"] = conn.execute(
                    "SELECT COUNT(*) AS n FROM artifacts"
                ).fetchone()["n"]
                base["local_sessions"] = conn.execute(
                    "SELECT COUNT(*) AS n FROM local_sessions"
                ).fetchone()["n"]
                base["schema"] = self._meta(conn, "schema_version") or None
                base["fts"] = self._meta(conn, "fts") or None
                base["rebuilt_at"] = self._meta(conn, "rebuilt_at") or None
                base["source_commit"] = self._meta(conn, "source_commit") or None
                for key, table in (
                    ("requirements", "requirements"),
                    ("canvases", "canvases"),
                    ("areas", "areas"),
                    ("lessons", "lessons"),
                    ("context_entries", "context_entries"),
                    ("domain_keywords", "domain_keywords"),
                    ("edges", "edges"),
                ):
                    try:
                        base[key] = conn.execute(
                            f"SELECT COUNT(*) AS n FROM {table}"
                        ).fetchone()["n"]
                    except sqlite3.Error:
                        base[key] = 0
                try:
                    base["staged_lessons"] = conn.execute(
                        "SELECT COUNT(*) AS n FROM lessons WHERE staged = 1"
                    ).fetchone()["n"]
                    base["lessons"] = conn.execute(
                        "SELECT COUNT(*) AS n FROM lessons WHERE staged = 0"
                    ).fetchone()["n"]
                except sqlite3.Error:
                    base["staged_lessons"] = 0
                rows = conn.execute(
                    "SELECT COALESCE(NULLIF(registry_status, ''), '(none)') AS s, "
                    "COUNT(*) AS n FROM work_items GROUP BY s ORDER BY n DESC"
                ).fetchall()
                base["by_registry_status"] = {r["s"]: r["n"] for r in rows}
            except sqlite3.Error as exc:
                base["error"] = str(exc)
        return base

    def status_text(self) -> str:
        info = self.status_dict()
        if info.get("error") == "missing":
            return (
                f"SQLite index missing: {info['path']}\n"
                "Rebuild: ./scripts/sdlc.sh db rebuild\n"
            )
        if info.get("error"):
            return (
                f"SQLite index unreadable ({info['error']}). "
                "Run: ./scripts/sdlc.sh db rebuild\n"
            )
        return (
            f"SQLite index: {info['path']}\n"
            f"  schema: {info['schema'] or '?'}\n"
            f"  fts: {info['fts'] or '?'}\n"
            f"  rebuilt_at: {info['rebuilt_at'] or '?'}\n"
            f"  source_commit: {info['source_commit'] or '?'}\n"
            f"  work_items: {info['work_items']}\n"
            f"  requirements: {info.get('requirements', 0)}\n"
            f"  canvases: {info.get('canvases', 0)}\n"
            f"  areas: {info.get('areas', 0)}\n"
            f"  lessons: {info.get('lessons', 0)}\n"
            f"  staged_lessons: {info.get('staged_lessons', 0)}\n"
            f"  context_entries: {info.get('context_entries', 0)}\n"
            f"  domain_keywords: {info.get('domain_keywords', 0)}\n"
            f"  edges: {info.get('edges', 0)}\n"
            f"  artifacts: {info['artifacts']}\n"
            f"  local_sessions: {info['local_sessions']}\n"
            "\n"
            "Multi-user sync: git (ledger JSONL + registry JSONL), not this file.\n"
            "Before GUIDE/Neo4j this is a local query cache only.\n"
        )

    def ensure(self) -> None:
        if not self.db_path.is_file():
            self.rebuild()

    def ensure_schema(self) -> None:
        """Ensure DB exists at current schema (full rebuild if missing/legacy)."""
        if not self.db_path.is_file():
            self.rebuild()
            return
        with self.connect() as conn:
            ver = self._meta(conn, "schema_version")
        if ver != SCHEMA_VERSION:
            self.rebuild()

    def ensure_work_item(self, work_id: str, *, title: str = "") -> None:
        """Insert a stub work_items row so graph FKs can attach."""
        self.ensure_schema()
        wid = (work_id or "").strip()
        if not wid:
            raise ValueError("work_id is required")
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO work_items(work_id, title, updated) VALUES (?,?,?)",
                (wid, title or wid, _utc_now()),
            )
            conn.commit()

    @staticmethod
    def _insert_edge(
        conn: sqlite3.Connection,
        src_kind: str,
        src_id: str,
        rel: str,
        dst_kind: str,
        dst_id: str,
    ) -> None:
        conn.execute(
            "INSERT OR IGNORE INTO edges(src_kind, src_id, rel, dst_kind, dst_id) "
            "VALUES (?,?,?,?,?)",
            (src_kind, src_id, rel, dst_kind, dst_id),
        )

    def upsert_edge(
        self,
        *,
        src_kind: str,
        src_id: str,
        rel: str,
        dst_kind: str,
        dst_id: str,
    ) -> None:
        """Insert a typed graph edge (idempotent)."""
        self.ensure_schema()
        if not all(
            [
                (src_kind or "").strip(),
                (src_id or "").strip(),
                (rel or "").strip(),
                (dst_kind or "").strip(),
                (dst_id or "").strip(),
            ]
        ):
            raise ValueError("src_kind, src_id, rel, dst_kind, dst_id are required")
        with self.connect() as conn:
            self._insert_edge(
                conn,
                src_kind.strip(),
                src_id.strip(),
                rel.strip(),
                dst_kind.strip(),
                dst_id.strip(),
            )
            conn.commit()

    def upsert_area(self, area: str, *, description: str = "") -> str:
        """Ensure a first-class area node exists; returns area id."""
        self.ensure_schema()
        name = (area or "").strip()
        if not name:
            raise ValueError("area is required")
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO areas(id, name, description) VALUES (?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "name=excluded.name, "
                "description=CASE WHEN excluded.description != '' "
                "THEN excluded.description ELSE areas.description END",
                (name, name, description or ""),
            )
            conn.commit()
        return name

    def upsert_requirement(
        self,
        *,
        work_id: str,
        path: str = "",
        title: str = "",
        summary: str = "",
        jira_key: str = "",
        ts: str = "",
        link_canvas: bool = True,
    ) -> str:
        """Upsert requirement node and work→requirement (+ optional reasons) edges."""
        self.ensure_work_item(work_id, title=title)
        wid = work_id.strip()
        req_id = f"{wid}:requirement"
        when = ts or _utc_now()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO requirements(id, work_id, path, title, summary, jira_key, updated) "
                "VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "path=excluded.path, title=excluded.title, summary=excluded.summary, "
                "jira_key=excluded.jira_key, updated=excluded.updated",
                (req_id, wid, path or "", title or "", summary or "", jira_key or "", when),
            )
            if path:
                conn.execute(
                    "UPDATE work_items SET requirement_path=?, has_requirement=1, "
                    "title=CASE WHEN ? != '' THEN ? ELSE title END, updated=? "
                    "WHERE work_id=?",
                    (path, title, title or wid, when, wid),
                )
            self._insert_edge(
                conn, NODE_WORK, wid, REL_REQUIREMENT, NODE_REQUIREMENT, req_id
            )
            if link_canvas:
                canvas_id = f"{wid}:canvas"
                row = conn.execute(
                    "SELECT id FROM canvases WHERE id = ?", (canvas_id,)
                ).fetchone()
                if row:
                    self._insert_edge(
                        conn,
                        NODE_REQUIREMENT,
                        req_id,
                        REL_REASONS,
                        NODE_CANVAS,
                        canvas_id,
                    )
            conn.commit()
        return req_id

    def upsert_canvas(
        self,
        *,
        work_id: str,
        path: str = "",
        title: str = "",
        status: str = "",
        readiness: str = "",
        final_status: str = "",
        ts: str = "",
        link_requirement: bool = True,
    ) -> str:
        """Upsert REASONS canvas node and work→canvas (+ optional reasons) edges."""
        self.ensure_work_item(work_id, title=title)
        wid = work_id.strip()
        canvas_id = f"{wid}:canvas"
        when = ts or _utc_now()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO canvases("
                "id, work_id, path, title, status, readiness, final_status, updated) "
                "VALUES (?,?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "path=excluded.path, title=excluded.title, status=excluded.status, "
                "readiness=excluded.readiness, final_status=excluded.final_status, "
                "updated=excluded.updated",
                (
                    canvas_id,
                    wid,
                    path or "",
                    title or "",
                    status or "",
                    readiness or "",
                    final_status or "",
                    when,
                ),
            )
            if path:
                conn.execute(
                    "UPDATE work_items SET canvas_path=?, has_canvas=1, "
                    "canvas_status=?, final_status=?, "
                    "title=CASE WHEN ? != '' THEN ? ELSE title END, updated=? "
                    "WHERE work_id=?",
                    (
                        path,
                        status or "",
                        final_status or "",
                        title,
                        title or wid,
                        when,
                        wid,
                    ),
                )
            self._insert_edge(
                conn, NODE_WORK, wid, REL_CANVAS, NODE_CANVAS, canvas_id
            )
            if link_requirement:
                req_id = f"{wid}:requirement"
                row = conn.execute(
                    "SELECT id FROM requirements WHERE id = ?", (req_id,)
                ).fetchone()
                if row:
                    self._insert_edge(
                        conn,
                        NODE_REQUIREMENT,
                        req_id,
                        REL_REASONS,
                        NODE_CANVAS,
                        canvas_id,
                    )
            conn.commit()
        return canvas_id

    def link_section_to_area(
        self,
        *,
        section_kind: str,
        section_id: str,
        area: str,
        work_id: str = "",
    ) -> None:
        """Link a requirement or REASONS canvas (and optionally work) to a context area."""
        kind = (section_kind or "").strip().lower()
        if kind not in {NODE_REQUIREMENT, NODE_CANVAS, NODE_WORK}:
            raise ValueError("section_kind must be work|requirement|canvas")
        sid = (section_id or "").strip()
        if not sid:
            raise ValueError("section_id is required")
        area_id = self.upsert_area(area)
        with self.connect() as conn:
            self._insert_edge(conn, kind, sid, REL_AREA, NODE_AREA, area_id)
            if work_id:
                self._insert_edge(
                    conn, NODE_WORK, work_id.strip(), REL_AREA, NODE_AREA, area_id
                )
                conn.execute(
                    "INSERT OR IGNORE INTO work_areas(work_id, area) VALUES (?,?)",
                    (work_id.strip(), area_id),
                )
            conn.commit()

    def sync_stay_set(self, work_id: str) -> dict[str, Any]:
        """Sync requirement + REASONS canvas nodes/edges from on-disk stay-set for one work id."""
        self.ensure_schema()
        wid = (work_id or "").strip()
        if not wid:
            raise ValueError("work_id is required")
        reg = None
        try:
            registry = TeamRegistry(self.project)
            reg = next((r for r in registry.rows() if r.work_id == wid), None)
        except Exception:  # noqa: BLE001
            reg = None
        links = collect_links(self.project, wid, reg)
        out: dict[str, Any] = {"work_id": wid, "requirement_id": "", "canvas_id": ""}
        meta: dict[str, str] = {}
        if links.canvas and links.canvas.is_file():
            meta = parse_canvas_metadata(links.canvas)
        req_parsed: dict[str, str] = {}
        if links.milestone_req and links.milestone_req.is_file():
            req_parsed = parse_milestone_requirement(links.milestone_req)
        title = meta.get("title") or req_parsed.get("jira_summary") or wid
        jira = links.jira_key or ""
        if links.milestone_req and links.milestone_req.is_file():
            out["requirement_id"] = self.upsert_requirement(
                work_id=wid,
                path=self._rel(links.milestone_req),
                title=title,
                summary=req_parsed.get("summary") or req_parsed.get("jira_summary") or "",
                jira_key=jira,
            )
        if links.canvas and links.canvas.is_file():
            final = canvas_mod.final_kind(links.canvas) or ""
            out["canvas_id"] = self.upsert_canvas(
                work_id=wid,
                path=self._rel(links.canvas),
                title=title,
                status=meta.get("status") or "",
                readiness=meta.get("readiness") or "",
                final_status=final,
            )
        return out

    def upsert_lesson_record(self, record: LessonRecord, *, staged: bool) -> None:
        """Upsert one ledger record + edges (hot-path projection write)."""
        record.validate()
        self.ensure_work_item(record.work_id)
        try:
            self.sync_stay_set(record.work_id)
        except Exception:  # noqa: BLE001
            pass
        stats = RebuildStats()
        with self.connect() as conn:
            self._ingest_lesson_row(conn, record, staged=staged, stats=stats)
            conn.commit()

    def upsert_claim(
        self,
        *,
        work_id: str,
        owner: str = "",
        status: str = "",
        phase: str = "",
        note: str = "",
        ts: str = "",
    ) -> int:
        self.ensure_work_item(work_id)
        when = ts or _utc_now()
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO claims(work_id, owner, status, phase, note, ts) "
                "VALUES (?,?,?,?,?,?)",
                (work_id, owner, status, phase, note, when),
            )
            claim_id = int(cur.lastrowid)
            conn.execute(
                "UPDATE work_items SET registry_status=?, registry_owner=?, "
                "registry_phase=?, registry_note=?, updated=? WHERE work_id=?",
                (status, owner, phase, note, when, work_id),
            )
            self._insert_edge(
                conn, NODE_CLAIM, str(claim_id), REL_FOR_WORK, NODE_WORK, work_id
            )
            conn.commit()
            return claim_id

    def upsert_context_session(
        self,
        *,
        session_id: str,
        work_id: str = "",
        phase: str = "",
        path: str = "",
        summary: str = "",
        ts: str = "",
    ) -> None:
        self.ensure_schema()
        sid = (session_id or "").strip()
        if not sid:
            raise ValueError("session_id is required")
        when = ts or _utc_now()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO context_sessions(id, work_id, phase, path, summary, ts) "
                "VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "work_id=excluded.work_id, phase=excluded.phase, path=excluded.path, "
                "summary=excluded.summary, ts=excluded.ts",
                (sid, work_id, phase, path, summary, when),
            )
            if work_id:
                self._insert_edge(
                    conn, NODE_SESSION, sid, REL_FOR_WORK, NODE_WORK, work_id
                )
            conn.commit()

    def upsert_context_entry(
        self,
        *,
        kind: str,
        work_id: str = "",
        area: str = "",
        phase: str = "",
        path: str = "",
        title: str = "",
        body: str = "",
        source: str = "",
        ts: str = "",
        entry_id: str = "",
    ) -> str:
        """Upsert any agent-context capability row + section/area edges."""
        from .context_model import CONTEXT_KINDS

        kind_n = (kind or "").strip().lower()
        if kind_n not in CONTEXT_KINDS:
            raise ValueError(f"kind must be one of {sorted(CONTEXT_KINDS)}")
        self.ensure_schema()
        if work_id:
            self.ensure_work_item(work_id)
            try:
                self.sync_stay_set(work_id)
            except Exception:  # noqa: BLE001
                pass
        with self.connect() as conn:
            eid = self._upsert_entry_row(
                conn,
                kind=kind_n,
                work_id=work_id,
                area=area,
                phase=phase,
                path=path,
                title=title,
                body=body,
                source=source,
                ts=ts,
                entry_id=entry_id,
            )
            conn.commit()
            return eid

