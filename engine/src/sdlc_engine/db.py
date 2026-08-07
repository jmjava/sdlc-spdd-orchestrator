"""Local regenerable SQLite index — lightweight store before GUIDE/Neo4j.

The binary DB lives under gitignored `.sdlc/index.sqlite`. Multi-user sync stays
git (markdown + work-registry.tsv). Rebuild anytime from on-disk artifacts.
Optional JSON/SQL export is for inspection or hand-off — not a shared live DB.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import canvas as canvas_mod
from .links import collect_links, note_token, parse_canvas_metadata, parse_milestone_requirement
from .project import Project
from .registry import TeamRegistry

SCHEMA_VERSION = "2"
DEFAULT_DB_NAME = "index.sqlite"

# Safe read-only query surface for `db query` convenience filters.
_SELECT_RE = re.compile(r"^\s*select\b", re.IGNORECASE | re.DOTALL)
_FORBIDDEN_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|attach|detach|pragma|create|replace)\b",
    re.IGNORECASE,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class RebuildStats:
    work_items: int = 0
    artifacts: int = 0
    local_sessions: int = 0
    path: str = ""
    rebuilt_at: str = ""
    source_commit: str = ""

    def as_text(self) -> str:
        return (
            f"Rebuilt SQLite index: {self.path}\n"
            f"  work_items: {self.work_items}\n"
            f"  artifacts: {self.artifacts}\n"
            f"  local_sessions: {self.local_sessions}\n"
            f"  source_commit: {self.source_commit or '(unknown)'}\n"
            f"  rebuilt_at: {self.rebuilt_at}\n"
        )


class LocalIndex:
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
        conn.executescript(
            """
            DROP TABLE IF EXISTS work_search;
            DROP TABLE IF EXISTS artifacts;
            DROP TABLE IF EXISTS local_sessions;
            DROP TABLE IF EXISTS pointers;
            DROP TABLE IF EXISTS context_sessions;
            DROP TABLE IF EXISTS claims;
            DROP TABLE IF EXISTS work_areas;
            DROP TABLE IF EXISTS lessons;
            DROP TABLE IF EXISTS work_items;
            DROP TABLE IF EXISTS meta;

            CREATE TABLE meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );

            CREATE TABLE work_items (
              work_id TEXT PRIMARY KEY,
              title TEXT,
              work_type TEXT,
              canvas_status TEXT,
              final_status TEXT,
              milestone TEXT,
              source_system TEXT,
              source_issue TEXT,
              source_url TEXT,
              canvas_path TEXT,
              requirement_path TEXT,
              feature_path TEXT,
              registry_status TEXT,
              registry_owner TEXT,
              registry_phase TEXT,
              registry_note TEXT,
              jira_key TEXT,
              github_number TEXT,
              has_canvas INTEGER NOT NULL DEFAULT 0,
              has_requirement INTEGER NOT NULL DEFAULT 0,
              has_feature INTEGER NOT NULL DEFAULT 0,
              updated TEXT
            );

            CREATE TABLE artifacts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              work_id TEXT,
              kind TEXT NOT NULL,
              path TEXT NOT NULL,
              title TEXT,
              mtime TEXT,
              UNIQUE(kind, path)
            );

            CREATE TABLE local_sessions (
              session_id TEXT PRIMARY KEY,
              title TEXT,
              status TEXT,
              intent TEXT,
              owner TEXT,
              promoted_to TEXT,
              updated TEXT,
              path TEXT
            );

            -- Relational graph tables (schema v2 / SPIKE-088): same link model as Guide DICE.
            CREATE TABLE lessons (
              id TEXT PRIMARY KEY,
              kind TEXT NOT NULL,
              work_id TEXT NOT NULL,
              area TEXT NOT NULL DEFAULT '',
              body TEXT NOT NULL DEFAULT '',
              source TEXT NOT NULL DEFAULT '',
              ts TEXT NOT NULL DEFAULT '',
              FOREIGN KEY(work_id) REFERENCES work_items(work_id)
            );

            CREATE TABLE work_areas (
              work_id TEXT NOT NULL,
              area TEXT NOT NULL,
              PRIMARY KEY (work_id, area),
              FOREIGN KEY(work_id) REFERENCES work_items(work_id)
            );

            CREATE TABLE claims (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              work_id TEXT NOT NULL,
              owner TEXT NOT NULL DEFAULT '',
              status TEXT NOT NULL DEFAULT '',
              phase TEXT NOT NULL DEFAULT '',
              note TEXT NOT NULL DEFAULT '',
              ts TEXT NOT NULL DEFAULT '',
              FOREIGN KEY(work_id) REFERENCES work_items(work_id)
            );

            CREATE TABLE context_sessions (
              id TEXT PRIMARY KEY,
              work_id TEXT NOT NULL DEFAULT '',
              phase TEXT NOT NULL DEFAULT '',
              path TEXT NOT NULL DEFAULT '',
              summary TEXT NOT NULL DEFAULT '',
              ts TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE pointers (
              id TEXT PRIMARY KEY,
              kind TEXT NOT NULL DEFAULT '',
              work_id TEXT NOT NULL DEFAULT '',
              commit_sha TEXT NOT NULL DEFAULT '',
              intent TEXT NOT NULL DEFAULT '',
              payload_json TEXT NOT NULL DEFAULT '{}',
              ts TEXT NOT NULL DEFAULT ''
            );

            CREATE INDEX idx_lessons_area ON lessons(area);
            CREATE INDEX idx_lessons_work ON lessons(work_id);
            CREATE INDEX idx_claims_work ON claims(work_id);
            """
        )
        # FTS5 when available; otherwise search falls back to LIKE.
        try:
            conn.execute(
                "CREATE VIRTUAL TABLE work_search USING fts5("
                "work_id, title, work_type, canvas_status, jira_key, github_number, "
                "registry_note, body, tokenize='porter')"
            )
            conn.execute(
                "INSERT INTO meta(key, value) VALUES ('fts', 'fts5')"
            )
        except sqlite3.OperationalError:
            conn.execute(
                "INSERT INTO meta(key, value) VALUES ('fts', 'like')"
            )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES ('schema_version', ?)",
            (SCHEMA_VERSION,),
        )

    def rebuild(self) -> RebuildStats:
        stats = RebuildStats(path=str(self.db_path), rebuilt_at=_utc_now(), source_commit=self._git_head())
        with self.connect() as conn:
            self._init_schema(conn)
            registry = TeamRegistry(self.project)
            rows = {r.work_id: r for r in registry.rows()}
            work_ids = registry.discover_work_ids()
            fts = self._meta(conn, "fts") == "fts5"

            for wid in work_ids:
                reg = rows.get(wid)
                links = collect_links(self.project, wid, reg)
                meta: dict[str, str] = {}
                if links.canvas and links.canvas.is_file():
                    meta = parse_canvas_metadata(links.canvas)
                req_parsed: dict[str, str] = {}
                if links.milestone_req and links.milestone_req.is_file():
                    req_parsed = parse_milestone_requirement(links.milestone_req)
                final = ""
                if links.canvas and links.canvas.is_file():
                    kind = canvas_mod.final_kind(links.canvas)
                    final = kind or ""
                    # Prefer explicit Final Status text when present
                    text = links.canvas.read_text(encoding="utf-8")
                    m = re.search(
                        r"## Final Status.*?^\s*-\s*Status:\s*(.+)$",
                        text,
                        re.IGNORECASE | re.MULTILINE | re.DOTALL,
                    )
                    if m:
                        final = m.group(1).strip()

                title = meta.get("title") or req_parsed.get("jira_summary") or wid
                jira = links.jira_key or (note_token(reg.note, "jira") if reg else "")
                gh = links.github_number or ""
                if reg and not gh:
                    tok = note_token(reg.note, "github")
                    gh = tok.lstrip("#") if tok else ""

                canvas_rel = self._rel(links.canvas) if links.canvas and links.canvas.is_file() else ""
                req_rel = (
                    self._rel(links.milestone_req)
                    if links.milestone_req and links.milestone_req.is_file()
                    else ""
                )
                feat = self.project.feature_dir(wid)
                feat_rel = self._rel(feat) if feat.is_dir() else ""

                conn.execute(
                    """
                    INSERT INTO work_items(
                      work_id, title, work_type, canvas_status, final_status, milestone,
                      source_system, source_issue, source_url,
                      canvas_path, requirement_path, feature_path,
                      registry_status, registry_owner, registry_phase, registry_note,
                      jira_key, github_number,
                      has_canvas, has_requirement, has_feature, updated
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        wid,
                        title,
                        meta.get("work_type") or "",
                        meta.get("status") or "",
                        final,
                        meta.get("milestone") or "",
                        meta.get("source_system") or links.canvas_source_system or "",
                        meta.get("source_issue") or links.canvas_source_issue or "",
                        meta.get("source_url") or links.canvas_source_url or "",
                        canvas_rel,
                        req_rel,
                        feat_rel,
                        reg.status if reg else "available",
                        reg.owner if reg else "",
                        reg.phase if reg else "",
                        reg.note if reg else "",
                        jira,
                        gh,
                        1 if canvas_rel else 0,
                        1 if req_rel else 0,
                        1 if feat_rel else 0,
                        reg.updated if reg else stats.rebuilt_at,
                    ),
                )
                stats.work_items += 1

                body_bits = [title, meta.get("status") or "", jira, gh, reg.note if reg else ""]
                if links.milestone_req and links.milestone_req.is_file():
                    body_bits.append(req_parsed.get("summary") or "")
                    body_bits.append(req_parsed.get("jira_description") or "")

                for kind, path in self._artifact_paths(wid, links, feat):
                    if not path.is_file() and not (kind == "feature" and path.is_dir()):
                        continue
                    mtime = ""
                    try:
                        mtime = datetime.fromtimestamp(
                            path.stat().st_mtime, tz=timezone.utc
                        ).strftime("%Y-%m-%dT%H:%M:%SZ")
                    except OSError:
                        pass
                    conn.execute(
                        "INSERT OR REPLACE INTO artifacts(work_id, kind, path, title, mtime) "
                        "VALUES (?,?,?,?,?)",
                        (wid, kind, self._rel(path), title if kind == "canvas" else "", mtime),
                    )
                    stats.artifacts += 1

                if fts:
                    conn.execute(
                        "INSERT INTO work_search(work_id, title, work_type, canvas_status, "
                        "jira_key, github_number, registry_note, body) VALUES (?,?,?,?,?,?,?,?)",
                        (
                            wid,
                            title,
                            meta.get("work_type") or "",
                            meta.get("status") or "",
                            jira,
                            gh,
                            reg.note if reg else "",
                            "\n".join(x for x in body_bits if x),
                        ),
                    )

            # Local sessions (machine-private)
            local_root = self.project.sdlc_dir / "local-sessions"
            if local_root.is_dir():
                for meta_path in sorted(local_root.glob("*/session.json")):
                    try:
                        data = json.loads(meta_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        continue
                    sid = data.get("id") or meta_path.parent.name
                    conn.execute(
                        "INSERT OR REPLACE INTO local_sessions("
                        "session_id, title, status, intent, owner, promoted_to, updated, path) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (
                            sid,
                            data.get("title") or "",
                            data.get("status") or "",
                            data.get("intent") or "",
                            data.get("owner") or "",
                            data.get("promoted_to") or "",
                            data.get("updated") or "",
                            self._rel(meta_path.parent),
                        ),
                    )
                    stats.local_sessions += 1

            conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES ('rebuilt_at', ?)",
                (stats.rebuilt_at,),
            )
            conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES ('source_commit', ?)",
                (stats.source_commit,),
            )
            conn.commit()
        return stats

    def _rel(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.project.root.resolve()))
        except ValueError:
            return str(path)

    def _artifact_paths(self, wid: str, links, feat: Path) -> list[tuple[str, Path]]:
        out: list[tuple[str, Path]] = []
        if links.canvas:
            out.append(("canvas", links.canvas))
        if links.milestone_req:
            out.append(("requirement", links.milestone_req))
        if feat.is_dir():
            out.append(("feature", feat))
        analysis = self.project.analysis_path(wid)
        if analysis.is_file():
            out.append(("analysis", analysis))
        review = self.project.review_path(wid)
        if review.is_file():
            out.append(("review", review))
        sync = self.project.sync_path(wid)
        if sync.is_file():
            out.append(("sync", sync))
        return out

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
            f"  artifacts: {info['artifacts']}\n"
            f"  local_sessions: {info['local_sessions']}\n"
            "\n"
            "Multi-user sync: git (markdown + work-registry.tsv), not this file.\n"
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

    def upsert_lesson(
        self,
        *,
        lesson_id: str,
        kind: str,
        work_id: str,
        area: str = "",
        body: str = "",
        source: str = "",
        ts: str = "",
    ) -> None:
        """Persist a lesson row and work↔area link (relational graph)."""
        self.ensure_work_item(work_id)
        kind_n = (kind or "").strip().lower()
        if kind_n not in {"decision", "pitfall", "pattern"}:
            raise ValueError("kind must be decision|pitfall|pattern")
        lid = (lesson_id or "").strip()
        if not lid:
            raise ValueError("lesson_id is required")
        when = ts or _utc_now()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO lessons(id, kind, work_id, area, body, source, ts) "
                "VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "kind=excluded.kind, work_id=excluded.work_id, area=excluded.area, "
                "body=excluded.body, source=excluded.source, ts=excluded.ts",
                (lid, kind_n, work_id, area or "", body or "", source or "", when),
            )
            if area:
                conn.execute(
                    "INSERT OR IGNORE INTO work_areas(work_id, area) VALUES (?,?)",
                    (work_id, area),
                )
            conn.commit()

    def lessons_for_area(self, area: str) -> list[dict[str, Any]]:
        self.ensure_schema()
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, kind, work_id, area, body, source, ts FROM lessons "
                "WHERE area = ? ORDER BY ts DESC, id",
                (area,),
            ).fetchall()
            return [dict(r) for r in rows]

    def lessons_for_work(self, work_id: str) -> list[dict[str, Any]]:
        self.ensure_schema()
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, kind, work_id, area, body, source, ts FROM lessons "
                "WHERE work_id = ? ORDER BY ts DESC, id",
                (work_id,),
            ).fetchall()
            return [dict(r) for r in rows]

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
            conn.execute(
                "UPDATE work_items SET registry_status=?, registry_owner=?, "
                "registry_phase=?, registry_note=?, updated=? WHERE work_id=?",
                (status, owner, phase, note, when, work_id),
            )
            conn.commit()
            return int(cur.lastrowid)

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
            conn.commit()

    def upsert_pointer_row(
        self,
        *,
        pointer_id: str,
        kind: str,
        work_id: str = "",
        commit_sha: str = "",
        intent: str = "",
        payload: dict[str, Any] | None = None,
        ts: str = "",
    ) -> None:
        self.ensure_schema()
        pid = (pointer_id or "").strip()
        if not pid:
            raise ValueError("pointer_id is required")
        when = ts or _utc_now()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO pointers(id, kind, work_id, commit_sha, intent, payload_json, ts) "
                "VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "kind=excluded.kind, work_id=excluded.work_id, commit_sha=excluded.commit_sha, "
                "intent=excluded.intent, payload_json=excluded.payload_json, ts=excluded.ts",
                (
                    pid,
                    kind,
                    work_id,
                    commit_sha,
                    intent,
                    json.dumps(payload or {}, ensure_ascii=False),
                    when,
                ),
            )
            conn.commit()

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
        "has_feature",
        "canvas_path",
        "requirement_path",
        "feature_path",
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
