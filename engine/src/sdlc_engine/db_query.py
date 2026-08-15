"""Read/query/export surface for the local SQLite index."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from .db_schema import SCHEMA_VERSION


_SELECT_RE = re.compile(r"^\s*select\b", re.IGNORECASE | re.DOTALL)
_FORBIDDEN_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|attach|detach|pragma|create|replace)\b",
    re.IGNORECASE,
)


class IndexQueryMixin:
    """Read-only query helpers and dump/export."""

    def accepted_lesson_ids(self) -> set[str]:
        self.ensure_schema()
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id FROM lessons WHERE staged = 0"
            ).fetchall()
            return {str(r["id"]) for r in rows}

    def lessons_for_area(self, area: str) -> list[dict[str, Any]]:
        self.ensure_schema()
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, kind, work_id, area, title, body, source, phase, "
                "keywords, ts, staged FROM lessons "
                "WHERE area = ? ORDER BY ts DESC, id",
                (area,),
            ).fetchall()
            return [dict(r) for r in rows]

    def lessons_for_work(self, work_id: str) -> list[dict[str, Any]]:
        self.ensure_schema()
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, kind, work_id, area, title, body, source, phase, "
                "keywords, ts, staged FROM lessons "
                "WHERE work_id = ? ORDER BY ts DESC, id",
                (work_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def capability_coverage(self) -> dict[str, Any]:
        """Report which CONTEXT_KINDS are present in the DB (for completion tests)."""
        from . import context_model as cm

        self.ensure_schema()
        present: set[str] = set()
        with self.connect() as conn:
            for row in conn.execute("SELECT DISTINCT kind FROM context_entries"):
                present.add(row["kind"])
            for row in conn.execute("SELECT DISTINCT kind FROM lessons"):
                present.add(row["kind"])
            if conn.execute("SELECT 1 FROM context_sessions LIMIT 1").fetchone():
                present.add("session")
        missing = cm.assert_kinds_covered(present)
        return {
            "schema": SCHEMA_VERSION,
            "required": sorted(cm.CONTEXT_KINDS),
            "present": sorted(present),
            "missing": missing,
            "complete": not missing,
            "matrix": cm.capability_matrix(),
        }

    def graph_for_work(self, work_id: str) -> dict[str, Any]:
        """Full subgraph: sections + all agent-context entries + typed edges."""
        self.ensure_schema()
        wid = (work_id or "").strip()
        with self.connect() as conn:
            work = conn.execute(
                "SELECT * FROM work_items WHERE work_id = ?", (wid,)
            ).fetchone()
            reqs = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM requirements WHERE work_id = ?", (wid,)
                ).fetchall()
            ]
            canvases = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM canvases WHERE work_id = ?", (wid,)
                ).fetchall()
            ]
            lessons = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM lessons WHERE work_id = ? ORDER BY ts DESC, id",
                    (wid,),
                ).fetchall()
            ]
            entries = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM context_entries WHERE work_id = ? "
                    "ORDER BY kind, ts DESC, id",
                    (wid,),
                ).fetchall()
            ]
            sessions = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM context_sessions WHERE work_id = ?", (wid,)
                ).fetchall()
            ]
            areas = [
                dict(r)
                for r in conn.execute(
                    "SELECT a.id, a.name, a.description FROM areas a "
                    "JOIN work_areas wa ON wa.area = a.id WHERE wa.work_id = ? "
                    "ORDER BY a.name",
                    (wid,),
                ).fetchall()
            ]
            node_ids = {wid}
            node_ids.update(r["id"] for r in reqs)
            node_ids.update(c["id"] for c in canvases)
            node_ids.update(l["id"] for l in lessons)
            node_ids.update(e["id"] for e in entries)
            node_ids.update(a["id"] for a in areas)
            edges = [
                dict(r)
                for r in conn.execute(
                    "SELECT src_kind, src_id, rel, dst_kind, dst_id FROM edges"
                ).fetchall()
                if r["src_id"] in node_ids or r["dst_id"] in node_ids
            ]
            return {
                "work_id": wid,
                "work": dict(work) if work else None,
                "requirements": reqs,
                "canvases": canvases,
                "areas": areas,
                "lessons": lessons,
                "context_entries": entries,
                "sessions": sessions,
                "edges": edges,
            }

    def context_linked_to_section(
        self, *, section_kind: str, section_id: str
    ) -> dict[str, Any]:
        """Context parts (areas/lessons) linked to a requirement or REASONS canvas."""
        self.ensure_schema()
        kind = (section_kind or "").strip().lower()
        sid = (section_id or "").strip()
        with self.connect() as conn:
            area_ids = [
                r["dst_id"]
                for r in conn.execute(
                    "SELECT dst_id FROM edges WHERE src_kind = ? AND src_id = ? "
                    "AND rel = ? AND dst_kind = ?",
                    (kind, sid, REL_AREA, NODE_AREA),
                ).fetchall()
            ]
            lesson_ids = [
                r["src_id"]
                for r in conn.execute(
                    "SELECT src_id FROM edges WHERE src_kind = ? AND rel = ? "
                    "AND dst_kind = ? AND dst_id = ?",
                    (NODE_LESSON, REL_ABOUT, kind, sid),
                ).fetchall()
            ]
            areas = []
            if area_ids:
                placeholders = ",".join("?" * len(area_ids))
                areas = [
                    dict(r)
                    for r in conn.execute(
                        f"SELECT * FROM areas WHERE id IN ({placeholders})",
                        area_ids,
                    ).fetchall()
                ]
            lessons = []
            if lesson_ids:
                placeholders = ",".join("?" * len(lesson_ids))
                lessons = [
                    dict(r)
                    for r in conn.execute(
                        f"SELECT * FROM lessons WHERE id IN ({placeholders}) "
                        "ORDER BY ts DESC, id",
                        lesson_ids,
                    ).fetchall()
                ]
            reasons = []
            if kind == NODE_REQUIREMENT:
                reasons = [
                    dict(r)
                    for r in conn.execute(
                        "SELECT c.* FROM canvases c "
                        "JOIN edges e ON e.dst_id = c.id "
                        "WHERE e.src_kind = ? AND e.src_id = ? AND e.rel = ? "
                        "AND e.dst_kind = ?",
                        (NODE_REQUIREMENT, sid, REL_REASONS, NODE_CANVAS),
                    ).fetchall()
                ]
            return {
                "section_kind": kind,
                "section_id": sid,
                "areas": areas,
                "lessons": lessons,
                "reasons_canvases": reasons,
            }

    LOOKUP_COLUMNS = (
        "work_id",
        "title",
        "registry_status",
        "registry_owner",
        "registry_phase",
        "jira_key",
        "canvas_status",
        "final_status",
        "has_canvas",
        "has_requirement",
        "canvas_path",
        "requirement_path",
    )

    def lookup(
        self,
        work_id: str,
        *,
        search: str = "",
        search_limit: int = 5,
        rebuild_if_missing: bool = True,
    ) -> dict[str, Any]:
        """Machine-readable Work ID snapshot for session briefs.

        Returns a dict with db_path, work_item (or null), related (optional search
        hits), and rebuilt flag. Never raises for missing rows.
        """
        rebuilt = False
        if rebuild_if_missing and not self.db_path.is_file():
            self.rebuild()
            rebuilt = True
        elif not self.db_path.is_file():
            return {
                "db_path": str(self.db_path),
                "rebuilt": False,
                "available": False,
                "work_id": work_id,
                "work_item": None,
                "related": [],
                "error": "SQLite index missing",
            }

        cols = ", ".join(self.LOOKUP_COLUMNS)
        rows = self.query_sql(
            f"SELECT {cols} FROM work_items WHERE work_id = ?",
            (work_id,),
        )
        related: list[dict[str, Any]] = []
        if search.strip():
            hits = self.find(search=search.strip(), limit=max(1, min(search_limit, 20)))
            related = [
                {k: h.get(k) for k in self.LOOKUP_COLUMNS if k in h}
                for h in hits
                if h.get("work_id") != work_id
            ][:search_limit]
        return {
            "db_path": str(self.db_path),
            "rebuilt": rebuilt,
            "available": True,
            "work_id": work_id,
            "work_item": rows[0] if rows else None,
            "related": related,
        }

    def lookup_markdown(
        self,
        work_id: str,
        *,
        search: str = "",
        search_limit: int = 5,
    ) -> str:
        """Markdown block for embedding into a session brief."""
        data = self.lookup(work_id, search=search, search_limit=search_limit)
        lines = [
            "## Local SQLite Index (query cache)",
            "",
            f"- Index path: `{data.get('db_path', '')}`",
            f"- Work ID lookup: `{work_id}`",
        ]
        if data.get("rebuilt"):
            lines.append("- Note: index was rebuilt because it was missing.")
        if not data.get("available"):
            lines.append(f"- Status: unavailable ({data.get('error', 'unknown')})")
            lines.append("- Git artifacts remain the source of truth.")
            lines.append("")
            return "\n".join(lines)

        item = data.get("work_item")
        if not item:
            lines.append("- Status: no `work_items` row for this Work ID (run `db rebuild`).")
            lines.append("- Git artifacts remain the source of truth.")
            lines.append("")
            return "\n".join(lines)

        lines.append("- Status: loaded into this brief for progressive disclosure.")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        for key in self.LOOKUP_COLUMNS:
            val = item.get(key, "")
            if val is None or val == "":
                continue
            # Keep table cells single-line (canvas Final Status can be multi-line).
            cell = re.sub(r"\s+", " ", str(val)).strip().replace("|", "\\|")
            if not cell:
                continue
            lines.append(f"| {key} | {cell} |")
        related = data.get("related") or []
        if related:
            lines.append("")
            lines.append("Related search hits:")
            for hit in related:
                wid = hit.get("work_id", "")
                title = hit.get("title") or ""
                lines.append(f"- `{wid}` {title}".rstrip())
        lines.append("")
        lines.append(
            "This is a local regenerable cache. Do not treat it as authoritative; "
            "prefer canvas/requirement/registry files when they disagree."
        )
        lines.append("")
        return "\n".join(lines)

    def query_sql(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        sql = sql.strip().rstrip(";")
        if not _SELECT_RE.match(sql) or _FORBIDDEN_SQL.search(sql):
            raise ValueError("db query only allows a single read-only SELECT statement")
        self.ensure()
        with self.connect() as conn:
            cur = conn.execute(sql, tuple(params))
            cols = [d[0] for d in cur.description or []]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def find(
        self,
        *,
        work_id: str = "",
        status: str = "",
        search: str = "",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        self.ensure()
        limit = max(1, min(limit, 500))
        with self.connect() as conn:
            if search:
                fts = self._meta(conn, "fts")
                if fts == "fts5":
                    rows = conn.execute(
                        "SELECT w.* FROM work_items w "
                        "WHERE w.work_id IN ("
                        "  SELECT work_id FROM work_search WHERE work_search MATCH ?"
                        ") ORDER BY w.work_id LIMIT ?",
                        (search, limit),
                    ).fetchall()
                else:
                    like = f"%{search}%"
                    rows = conn.execute(
                        "SELECT * FROM work_items WHERE "
                        "work_id LIKE ? OR title LIKE ? OR jira_key LIKE ? "
                        "OR github_number LIKE ? OR registry_note LIKE ? "
                        "LIMIT ?",
                        (like, like, like, like, like, limit),
                    ).fetchall()
                return [dict(r) for r in rows]
            clauses: list[str] = []
            params: list[Any] = []
            if work_id:
                clauses.append("work_id = ?")
                params.append(work_id)
            if status:
                clauses.append("(registry_status = ? OR canvas_status = ? OR final_status = ?)")
                params.extend([status, status, status])
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            params.append(limit)
            rows = conn.execute(
                f"SELECT * FROM work_items{where} ORDER BY work_id LIMIT ?",
                params,
            ).fetchall()
            return [dict(r) for r in rows]

    def export_json(self, path: Path | None = None) -> str:
        self.ensure()
        with self.connect() as conn:
            payload = {
                "schema_version": self._meta(conn, "schema_version"),
                "rebuilt_at": self._meta(conn, "rebuilt_at"),
                "source_commit": self._meta(conn, "source_commit"),
                "work_items": [
                    dict(r) for r in conn.execute("SELECT * FROM work_items ORDER BY work_id")
                ],
                "artifacts": [
                    dict(r) for r in conn.execute("SELECT * FROM artifacts ORDER BY work_id, kind")
                ],
                "local_sessions": [
                    dict(r) for r in conn.execute("SELECT * FROM local_sessions ORDER BY session_id")
                ],
            }
        text = json.dumps(payload, indent=2) + "\n"
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return text

    def export_sql(self, path: Path | None = None) -> str:
        self.ensure()
        lines = [
            f"-- SDLC local index dump ({_utc_now()})",
            f"-- source: {self.db_path}",
            "BEGIN;",
        ]
        with self.connect() as conn:
            for line in conn.iterdump():
                lines.append(line)
        lines.append("COMMIT;")
        text = "\n".join(lines) + "\n"
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return text

def format_rows(rows: list[dict[str, Any]], columns: list[str] | None = None) -> str:
    if not rows:
        return "(no rows)\n"
    cols = columns or list(rows[0].keys())
    widths = {c: len(c) for c in cols}
    for row in rows:
        for c in cols:
            widths[c] = max(widths[c], len(str(row.get(c, "") or "")))
    header = "  ".join(c.ljust(widths[c]) for c in cols)
    sep = "  ".join("-" * widths[c] for c in cols)
    lines = [header, sep]
    for row in rows:
        lines.append("  ".join(str(row.get(c, "") or "").ljust(widths[c]) for c in cols))
    return "\n".join(lines) + "\n"
