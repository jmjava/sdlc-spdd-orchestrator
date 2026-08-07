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

SCHEMA_VERSION = "4"
DEFAULT_DB_NAME = "index.sqlite"

# Typed edge kinds (src/dst) and relationship names — aligned with Guide DICE
# plus requirement↔REASONS and full agent-context part links.
NODE_WORK = "work"
NODE_REQUIREMENT = "requirement"
NODE_CANVAS = "canvas"
NODE_AREA = "area"
NODE_LESSON = "lesson"
NODE_CLAIM = "claim"
NODE_SESSION = "session"
NODE_POINTER = "pointer"
NODE_ENTRY = "entry"
NODE_KEYWORD = "keyword"
NODE_PHASE_REF = "phase_ref"
NODE_FACT = "fact"

REL_CANVAS = "canvas"  # work —has canvas→ REASONS
REL_REQUIREMENT = "requirement"  # work —has requirement→ requirement
REL_REASONS = "reasons"  # requirement —reasons→ canvas
REL_AREA = "area"  # work|requirement|canvas|entry —in area→ area
REL_ABOUT = "about"  # lesson|entry —about→ area|requirement|canvas
REL_RECORDED_FOR = "recorded_for"  # lesson —recorded for→ work
REL_FOR_WORK = "for_work"  # claim|session|pointer|entry —for→ work
REL_PHASE = "phase"  # entry|phase_ref —phase→ phase_ref
REL_KEYWORD = "keyword"  # keyword —about→ area|entry

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
    requirements: int = 0
    canvases: int = 0
    context_entries: int = 0
    domain_keywords: int = 0
    phase_refs: int = 0
    project_facts: int = 0
    edges: int = 0
    path: str = ""
    rebuilt_at: str = ""
    source_commit: str = ""

    def as_text(self) -> str:
        return (
            f"Rebuilt SQLite index: {self.path}\n"
            f"  work_items: {self.work_items}\n"
            f"  requirements: {self.requirements}\n"
            f"  canvases: {self.canvases}\n"
            f"  context_entries: {self.context_entries}\n"
            f"  domain_keywords: {self.domain_keywords}\n"
            f"  phase_refs: {self.phase_refs}\n"
            f"  project_facts: {self.project_facts}\n"
            f"  edges: {self.edges}\n"
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
            DROP TABLE IF EXISTS edges;
            DROP TABLE IF EXISTS artifacts;
            DROP TABLE IF EXISTS local_sessions;
            DROP TABLE IF EXISTS pointers;
            DROP TABLE IF EXISTS context_sessions;
            DROP TABLE IF EXISTS claims;
            DROP TABLE IF EXISTS work_areas;
            DROP TABLE IF EXISTS lessons;
            DROP TABLE IF EXISTS project_facts;
            DROP TABLE IF EXISTS phase_refs;
            DROP TABLE IF EXISTS domain_keywords;
            DROP TABLE IF EXISTS context_entries;
            DROP TABLE IF EXISTS areas;
            DROP TABLE IF EXISTS canvases;
            DROP TABLE IF EXISTS requirements;
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

            -- Stay-set section nodes (schema v3): requirements + REASONS canvases.
            CREATE TABLE requirements (
              id TEXT PRIMARY KEY,
              work_id TEXT NOT NULL,
              path TEXT NOT NULL DEFAULT '',
              title TEXT NOT NULL DEFAULT '',
              summary TEXT NOT NULL DEFAULT '',
              jira_key TEXT NOT NULL DEFAULT '',
              updated TEXT NOT NULL DEFAULT '',
              FOREIGN KEY(work_id) REFERENCES work_items(work_id)
            );

            CREATE TABLE canvases (
              id TEXT PRIMARY KEY,
              work_id TEXT NOT NULL,
              path TEXT NOT NULL DEFAULT '',
              title TEXT NOT NULL DEFAULT '',
              status TEXT NOT NULL DEFAULT '',
              readiness TEXT NOT NULL DEFAULT '',
              final_status TEXT NOT NULL DEFAULT '',
              updated TEXT NOT NULL DEFAULT '',
              FOREIGN KEY(work_id) REFERENCES work_items(work_id)
            );

            CREATE TABLE areas (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              description TEXT NOT NULL DEFAULT ''
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

            -- Context-part nodes + typed edges (Guide DICE + requirement↔REASONS).
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

            -- Schema v4: remaining agent-context capabilities as first-class nodes.
            CREATE TABLE context_entries (
              id TEXT PRIMARY KEY,
              kind TEXT NOT NULL,
              work_id TEXT NOT NULL DEFAULT '',
              area TEXT NOT NULL DEFAULT '',
              phase TEXT NOT NULL DEFAULT '',
              path TEXT NOT NULL DEFAULT '',
              title TEXT NOT NULL DEFAULT '',
              body TEXT NOT NULL DEFAULT '',
              source TEXT NOT NULL DEFAULT '',
              ts TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE domain_keywords (
              id TEXT PRIMARY KEY,
              keyword TEXT NOT NULL
            );

            CREATE TABLE phase_refs (
              id TEXT PRIMARY KEY,
              phase TEXT NOT NULL,
              path TEXT NOT NULL,
              purpose TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE project_facts (
              id TEXT PRIMARY KEY,
              work_id TEXT NOT NULL DEFAULT '',
              phase TEXT NOT NULL DEFAULT '',
              summary TEXT NOT NULL DEFAULT '',
              next_step TEXT NOT NULL DEFAULT '',
              ts TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE edges (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              src_kind TEXT NOT NULL,
              src_id TEXT NOT NULL,
              rel TEXT NOT NULL,
              dst_kind TEXT NOT NULL,
              dst_id TEXT NOT NULL,
              UNIQUE(src_kind, src_id, rel, dst_kind, dst_id)
            );

            CREATE INDEX idx_lessons_area ON lessons(area);
            CREATE INDEX idx_lessons_work ON lessons(work_id);
            CREATE INDEX idx_claims_work ON claims(work_id);
            CREATE INDEX idx_requirements_work ON requirements(work_id);
            CREATE INDEX idx_canvases_work ON canvases(work_id);
            CREATE INDEX idx_entries_kind ON context_entries(kind);
            CREATE INDEX idx_entries_work ON context_entries(work_id);
            CREATE INDEX idx_entries_area ON context_entries(area);
            CREATE INDEX idx_edges_src ON edges(src_kind, src_id, rel);
            CREATE INDEX idx_edges_dst ON edges(dst_kind, dst_id, rel);
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

                # First-class stay-set nodes + linkage edges (requirement ↔ REASONS).
                req_id = ""
                canvas_id = ""
                if req_rel:
                    req_id = f"{wid}:requirement"
                    conn.execute(
                        "INSERT INTO requirements(id, work_id, path, title, summary, jira_key, updated) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (
                            req_id,
                            wid,
                            req_rel,
                            title,
                            req_parsed.get("summary") or req_parsed.get("jira_summary") or "",
                            jira,
                            reg.updated if reg else stats.rebuilt_at,
                        ),
                    )
                    stats.requirements += 1
                    self._insert_edge(
                        conn,
                        NODE_WORK,
                        wid,
                        REL_REQUIREMENT,
                        NODE_REQUIREMENT,
                        req_id,
                    )
                    stats.edges += 1
                if canvas_rel:
                    canvas_id = f"{wid}:canvas"
                    conn.execute(
                        "INSERT INTO canvases("
                        "id, work_id, path, title, status, readiness, final_status, updated) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (
                            canvas_id,
                            wid,
                            canvas_rel,
                            title,
                            meta.get("status") or "",
                            meta.get("readiness") or "",
                            final,
                            reg.updated if reg else stats.rebuilt_at,
                        ),
                    )
                    stats.canvases += 1
                    self._insert_edge(
                        conn, NODE_WORK, wid, REL_CANVAS, NODE_CANVAS, canvas_id
                    )
                    stats.edges += 1
                if req_id and canvas_id:
                    self._insert_edge(
                        conn,
                        NODE_REQUIREMENT,
                        req_id,
                        REL_REASONS,
                        NODE_CANVAS,
                        canvas_id,
                    )
                    stats.edges += 1

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

            # Full agent-context ingest (governance, mirrors, indexes, tooling).
            self._ingest_full_context(conn, stats)

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

    def _ensure_area_row(self, conn: sqlite3.Connection, area: str) -> str:
        name = (area or "").strip()
        if not name:
            return ""
        conn.execute(
            "INSERT INTO areas(id, name, description) VALUES (?,?,?) "
            "ON CONFLICT(id) DO NOTHING",
            (name, name, ""),
        )
        return name

    def _upsert_entry_row(
        self,
        conn: sqlite3.Connection,
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
        from .context_model import NODE_ENTRY as CM_ENTRY
        from .context_model import stable_id

        kind_n = (kind or "").strip().lower()
        wid = (work_id or "").strip()
        if wid:
            conn.execute(
                "INSERT OR IGNORE INTO work_items(work_id, title, updated) VALUES (?,?,?)",
                (wid, wid, _utc_now()),
            )
        eid = entry_id or stable_id(kind_n, wid, area, path, title, source, ts)
        when = ts or _utc_now()
        conn.execute(
            "INSERT INTO context_entries("
            "id, kind, work_id, area, phase, path, title, body, source, ts) "
            "VALUES (?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "kind=excluded.kind, work_id=excluded.work_id, area=excluded.area, "
            "phase=excluded.phase, path=excluded.path, title=excluded.title, "
            "body=excluded.body, source=excluded.source, ts=excluded.ts",
            (
                eid,
                kind_n,
                wid,
                area or "",
                phase or "",
                path or "",
                title or "",
                body or "",
                source or "",
                when,
            ),
        )
        if wid:
            self._insert_edge(conn, CM_ENTRY, eid, REL_FOR_WORK, NODE_WORK, wid)
            req_id = f"{wid}:requirement"
            canvas_id = f"{wid}:canvas"
            if conn.execute(
                "SELECT 1 FROM requirements WHERE id = ?", (req_id,)
            ).fetchone():
                self._insert_edge(
                    conn, CM_ENTRY, eid, REL_ABOUT, NODE_REQUIREMENT, req_id
                )
            if conn.execute(
                "SELECT 1 FROM canvases WHERE id = ?", (canvas_id,)
            ).fetchone():
                self._insert_edge(conn, CM_ENTRY, eid, REL_ABOUT, NODE_CANVAS, canvas_id)
        if area:
            area_id = self._ensure_area_row(conn, area)
            self._insert_edge(conn, CM_ENTRY, eid, REL_ABOUT, NODE_AREA, area_id)
            if wid:
                self._insert_edge(conn, NODE_WORK, wid, REL_AREA, NODE_AREA, area_id)
                conn.execute(
                    "INSERT OR IGNORE INTO work_areas(work_id, area) VALUES (?,?)",
                    (wid, area_id),
                )
                if conn.execute(
                    "SELECT 1 FROM requirements WHERE id = ?", (f"{wid}:requirement",)
                ).fetchone():
                    self._insert_edge(
                        conn,
                        NODE_REQUIREMENT,
                        f"{wid}:requirement",
                        REL_AREA,
                        NODE_AREA,
                        area_id,
                    )
                if conn.execute(
                    "SELECT 1 FROM canvases WHERE id = ?", (f"{wid}:canvas",)
                ).fetchone():
                    self._insert_edge(
                        conn,
                        NODE_CANVAS,
                        f"{wid}:canvas",
                        REL_AREA,
                        NODE_AREA,
                        area_id,
                    )
        return eid

    def _ingest_full_context(
        self, conn: sqlite3.Connection, stats: RebuildStats
    ) -> None:
        """Ingest stay-set governance + legacy agent-context into graph tables."""
        from . import context_model as cm

        root = self.project.root

        # 1) Stay-set governance artifacts
        for rel_dir, kind, pattern in cm.GOVERNANCE_GLOBS:
            d = root / rel_dir
            if not d.is_dir():
                continue
            for path in sorted(d.glob(pattern)):
                if not path.is_file():
                    continue
                wid = cm.work_id_from_name(path.name)
                body = ""
                try:
                    body = path.read_text(encoding="utf-8")[:4000]
                except OSError:
                    pass
                self._upsert_entry_row(
                    conn,
                    kind=kind,
                    work_id=wid,
                    path=self._rel(path),
                    title=path.stem,
                    body=body,
                    source="stay-set",
                )
                stats.context_entries += 1
                stats.edges += 1

        # 2) Legacy feature mirrors
        feat_root = root / "agent-context" / "features"
        if feat_root.is_dir():
            for work_dir in sorted(p for p in feat_root.iterdir() if p.is_dir()):
                wid = work_dir.name
                for fname, kind in cm.FEATURE_MIRROR_KIND.items():
                    path = work_dir / fname
                    if not path.is_file():
                        continue
                    body = ""
                    try:
                        body = path.read_text(encoding="utf-8")[:4000]
                    except OSError:
                        pass
                    self._upsert_entry_row(
                        conn,
                        kind=kind,
                        work_id=wid,
                        path=self._rel(path),
                        title=fname,
                        body=body,
                        source="feature-mirror",
                    )
                    stats.context_entries += 1

        # 3) context-index.md (lean + legacy)
        for index_rel in (
            Path("spdd/memory/context-index.md"),
            Path("agent-context/memory/context-index.md"),
        ):
            index_path = root / index_rel
            if not index_path.is_file():
                continue
            try:
                rows = cm.parse_md_table(index_path.read_text(encoding="utf-8"))
            except OSError:
                continue
            for row in rows:
                kind = (row.get("kind") or "").strip().lower()
                if not kind:
                    continue
                area = (row.get("area") or "").strip()
                wid = (row.get("work id") or row.get("work_id") or "").strip()
                phase = (row.get("phase") or "").strip()
                ts = (row.get("timestamp") or "").strip()
                source = (row.get("source") or "").strip()
                entry = (row.get("entry") or "").strip()
                if kind in {"decision", "pitfall", "pattern"}:
                    # Prefer lessons table for lesson kinds
                    lesson_wid = wid or "_index"
                    lid = f"{kind}:{lesson_wid}:{area or '(none)'}:{source or 'index'}"
                    conn.execute(
                        "INSERT OR IGNORE INTO work_items(work_id, title, updated) "
                        "VALUES (?,?,?)",
                        (lesson_wid, lesson_wid, _utc_now()),
                    )
                    conn.execute(
                        "INSERT INTO lessons(id, kind, work_id, area, body, source, ts) "
                        "VALUES (?,?,?,?,?,?,?) "
                        "ON CONFLICT(id) DO UPDATE SET body=excluded.body, ts=excluded.ts",
                        (lid, kind, lesson_wid, area, entry, source or "index", ts),
                    )
                    self._insert_edge(
                        conn, NODE_LESSON, lid, REL_RECORDED_FOR, NODE_WORK, lesson_wid
                    )
                    if area:
                        self._ensure_area_row(conn, area)
                        self._insert_edge(
                            conn, NODE_LESSON, lid, REL_ABOUT, NODE_AREA, area
                        )
                    continue
                self._upsert_entry_row(
                    conn,
                    kind=kind if kind in cm.CONTEXT_KINDS else "metric",
                    work_id=wid,
                    area=area,
                    phase=phase,
                    path=str(index_rel),
                    title=entry[:200],
                    body=entry,
                    source=source or str(index_rel),
                    ts=ts,
                )
                stats.context_entries += 1

        # 4) domain-index.md
        for domain_rel in (
            Path("agent-context/memory/domain-index.md"),
            Path("spdd/memory/domain-index.md"),
        ):
            domain_path = root / domain_rel
            if not domain_path.is_file():
                continue
            try:
                rows = cm.parse_md_table(domain_path.read_text(encoding="utf-8"))
            except OSError:
                continue
            for row in rows:
                keyword = (row.get("keyword") or "").strip().lower()
                if not keyword:
                    continue
                kid = cm.stable_id("keyword", keyword)
                conn.execute(
                    "INSERT INTO domain_keywords(id, keyword) VALUES (?,?) "
                    "ON CONFLICT(id) DO UPDATE SET keyword=excluded.keyword",
                    (kid, keyword),
                )
                stats.domain_keywords += 1
                area = (row.get("area") or "").strip()
                if area:
                    self._ensure_area_row(conn, area)
                    self._insert_edge(
                        conn, cm.NODE_KEYWORD, kid, REL_ABOUT, NODE_AREA, area
                    )
                    stats.edges += 1
                wid = (row.get("work id") or row.get("work_id") or "").strip()
                entry_path = (row.get("entry") or "").strip()
                kind = (row.get("kind") or "analysis").strip().lower()
                if entry_path or wid:
                    eid = self._upsert_entry_row(
                        conn,
                        kind=kind if kind in cm.CONTEXT_KINDS else "analysis",
                        work_id=wid,
                        area=area,
                        path=entry_path,
                        title=entry_path or keyword,
                        source="domain-index",
                        ts=(row.get("timestamp") or "").strip(),
                    )
                    self._insert_edge(
                        conn, cm.NODE_KEYWORD, kid, REL_ABOUT, cm.NODE_ENTRY, eid
                    )
                    stats.context_entries += 1

        # 5) phase-index.md
        for phase_rel in (
            Path("agent-context/memory/phase-index.md"),
            Path("spdd/memory/phase-index.md"),
        ):
            phase_path = root / phase_rel
            if not phase_path.is_file():
                continue
            try:
                rows = cm.parse_md_table(phase_path.read_text(encoding="utf-8"))
            except OSError:
                continue
            for row in rows:
                phase = (row.get("phase") or "").strip()
                path = (row.get("path") or "").strip().strip("`")
                purpose = (row.get("purpose") or "").strip()
                if not phase or not path:
                    continue
                pid = cm.stable_id("phase", phase, path)
                conn.execute(
                    "INSERT INTO phase_refs(id, phase, path, purpose) VALUES (?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET purpose=excluded.purpose",
                    (pid, phase, path, purpose),
                )
                stats.phase_refs += 1
                # Also as context_entry kind=phase_ref for capability coverage
                self._upsert_entry_row(
                    conn,
                    kind="phase_ref",
                    phase=phase,
                    path=path,
                    title=purpose or path,
                    body=purpose,
                    source="phase-index",
                    entry_id=pid,
                )
                stats.context_entries += 1

        # 6) code-areas.md → areas
        for areas_rel in (
            Path("agent-context/memory/code-areas.md"),
            Path("spdd/memory/code-areas.md"),
        ):
            areas_path = root / areas_rel
            if not areas_path.is_file():
                continue
            try:
                text = areas_path.read_text(encoding="utf-8")
            except OSError:
                continue
            for area in cm.iter_code_areas(text):
                self._ensure_area_row(conn, area)

        # 7) project-memory facts
        for mem_rel in (
            Path("agent-context/memory/project-memory.md"),
            Path("spdd/memory/project-memory.md"),
        ):
            mem_path = root / mem_rel
            if not mem_path.is_file():
                continue
            try:
                facts = cm.extract_memory_facts(mem_path.read_text(encoding="utf-8"))
            except OSError:
                continue
            for fact in facts:
                fid = cm.stable_id(
                    "fact", fact.get("work_id", ""), fact.get("ts", ""), fact.get("summary", "")
                )
                conn.execute(
                    "INSERT INTO project_facts(id, work_id, phase, summary, next_step, ts) "
                    "VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET summary=excluded.summary",
                    (
                        fid,
                        fact.get("work_id") or "",
                        fact.get("phase") or "",
                        fact.get("summary") or "",
                        fact.get("next_step") or "",
                        fact.get("ts") or "",
                    ),
                )
                stats.project_facts += 1
                self._upsert_entry_row(
                    conn,
                    kind="memory",
                    work_id=fact.get("work_id") or "",
                    phase=fact.get("phase") or "",
                    path=str(mem_rel),
                    title=(fact.get("summary") or "")[:200],
                    body=fact.get("summary") or "",
                    source="project-memory",
                    ts=fact.get("ts") or "",
                    entry_id=fid,
                )
                stats.context_entries += 1

        # 8) prompt-optimization-log
        for prompt_rel in (
            Path("agent-context/memory/prompt-optimization-log.md"),
            Path("spdd/memory/prompt-optimization-log.md"),
        ):
            prompt_path = root / prompt_rel
            if not prompt_path.is_file():
                continue
            try:
                entries = cm.extract_prompt_entries(
                    prompt_path.read_text(encoding="utf-8")
                )
            except OSError:
                continue
            for ent in entries:
                self._upsert_entry_row(
                    conn,
                    kind="prompt",
                    path=str(prompt_rel),
                    title=ent.get("title") or "",
                    body=ent.get("body") or "",
                    source="prompt-optimization-log",
                )
                stats.context_entries += 1

        # 9) Sessions (hot + legacy)
        session_dirs = [
            self.project.sdlc_dir / "sessions",
            root / "agent-context" / "sessions",
            root / "agent-context" / "memory" / "sessions",
        ]
        for sdir in session_dirs:
            if not sdir.is_dir():
                continue
            for path in sorted(sdir.glob("*.md")):
                wid = cm.work_id_from_name(path.name)
                body = ""
                try:
                    body = path.read_text(encoding="utf-8")[:4000]
                except OSError:
                    pass
                sid = path.stem
                conn.execute(
                    "INSERT INTO context_sessions(id, work_id, phase, path, summary, ts) "
                    "VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET "
                    "work_id=excluded.work_id, path=excluded.path, summary=excluded.summary",
                    (sid, wid, "", self._rel(path), body[:500], _utc_now()),
                )
                if wid:
                    self._insert_edge(
                        conn, NODE_SESSION, sid, REL_FOR_WORK, NODE_WORK, wid
                    )
                self._upsert_entry_row(
                    conn,
                    kind="session",
                    work_id=wid,
                    path=self._rel(path),
                    title=sid,
                    body=body,
                    source="session",
                    entry_id=f"session:{sid}",
                )
                stats.context_entries += 1

        # 10) Playbooks / harness / extensions (tooling context)
        tooling = (
            ("agent-context/playbooks", "playbook"),
            ("agent-context/harness", "harness"),
            ("agent-context/extensions", "extension"),
        )
        for rel, kind in tooling:
            d = root / rel
            if not d.is_dir():
                continue
            for path in sorted(d.rglob("*.md")):
                if path.name.startswith("."):
                    continue
                body = ""
                try:
                    body = path.read_text(encoding="utf-8")[:2000]
                except OSError:
                    pass
                self._upsert_entry_row(
                    conn,
                    kind=kind,
                    path=self._rel(path),
                    title=path.stem,
                    body=body,
                    source=rel,
                )
                stats.context_entries += 1

        # 11) Seed lesson files if present without index rows
        for kind, rel in (
            ("decision", Path("agent-context/memory/architecture-decisions.md")),
            ("pitfall", Path("agent-context/memory/known-pitfalls.md")),
            ("pattern", Path("agent-context/memory/reusable-patterns.md")),
            ("decision", Path("spdd/memory/lessons/decisions.md")),
            ("pitfall", Path("spdd/memory/lessons/pitfalls.md")),
            ("pattern", Path("spdd/memory/lessons/patterns.md")),
        ):
            path = root / rel
            if not path.is_file():
                continue
            # Ensure at least one lesson row exists so kind is covered
            lid = f"{kind}:_file:{rel.as_posix()}"
            try:
                body = path.read_text(encoding="utf-8")[:500]
            except OSError:
                body = ""
            conn.execute(
                "INSERT OR IGNORE INTO work_items(work_id, title, updated) VALUES (?,?,?)",
                ("_memory", "memory", _utc_now()),
            )
            conn.execute(
                "INSERT INTO lessons(id, kind, work_id, area, body, source, ts) "
                "VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING",
                (lid, kind, "_memory", "", body, str(rel), _utc_now()),
            )

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
            "context_entries": 0,
            "domain_keywords": 0,
            "phase_refs": 0,
            "project_facts": 0,
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
                    ("phase_refs", "phase_refs"),
                    ("project_facts", "project_facts"),
                    ("edges", "edges"),
                ):
                    try:
                        base[key] = conn.execute(
                            f"SELECT COUNT(*) AS n FROM {table}"
                        ).fetchone()["n"]
                    except sqlite3.Error:
                        base[key] = 0
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
            f"  context_entries: {info.get('context_entries', 0)}\n"
            f"  domain_keywords: {info.get('domain_keywords', 0)}\n"
            f"  phase_refs: {info.get('phase_refs', 0)}\n"
            f"  project_facts: {info.get('project_facts', 0)}\n"
            f"  edges: {info.get('edges', 0)}\n"
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
        """Persist a lesson and link it to work, area, requirement, and REASONS canvas."""
        self.ensure_work_item(work_id)
        kind_n = (kind or "").strip().lower()
        if kind_n not in {"decision", "pitfall", "pattern"}:
            raise ValueError("kind must be decision|pitfall|pattern")
        lid = (lesson_id or "").strip()
        if not lid:
            raise ValueError("lesson_id is required")
        when = ts or _utc_now()
        # Best-effort stay-set sync so lesson can attach to requirement/REASONS.
        try:
            self.sync_stay_set(work_id)
        except Exception:  # noqa: BLE001 - stubs still allow lesson rows
            pass
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO lessons(id, kind, work_id, area, body, source, ts) "
                "VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "kind=excluded.kind, work_id=excluded.work_id, area=excluded.area, "
                "body=excluded.body, source=excluded.source, ts=excluded.ts",
                (lid, kind_n, work_id, area or "", body or "", source or "", when),
            )
            self._insert_edge(
                conn, NODE_LESSON, lid, REL_RECORDED_FOR, NODE_WORK, work_id
            )
            req_id = f"{work_id}:requirement"
            canvas_id = f"{work_id}:canvas"
            if conn.execute(
                "SELECT 1 FROM requirements WHERE id = ?", (req_id,)
            ).fetchone():
                self._insert_edge(
                    conn, NODE_LESSON, lid, REL_ABOUT, NODE_REQUIREMENT, req_id
                )
            if conn.execute(
                "SELECT 1 FROM canvases WHERE id = ?", (canvas_id,)
            ).fetchone():
                self._insert_edge(
                    conn, NODE_LESSON, lid, REL_ABOUT, NODE_CANVAS, canvas_id
                )
            if area:
                conn.execute(
                    "INSERT INTO areas(id, name, description) VALUES (?,?,?) "
                    "ON CONFLICT(id) DO NOTHING",
                    (area, area, ""),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO work_areas(work_id, area) VALUES (?,?)",
                    (work_id, area),
                )
                self._insert_edge(conn, NODE_WORK, work_id, REL_AREA, NODE_AREA, area)
                self._insert_edge(conn, NODE_LESSON, lid, REL_ABOUT, NODE_AREA, area)
                if conn.execute(
                    "SELECT 1 FROM requirements WHERE id = ?", (req_id,)
                ).fetchone():
                    self._insert_edge(
                        conn, NODE_REQUIREMENT, req_id, REL_AREA, NODE_AREA, area
                    )
                if conn.execute(
                    "SELECT 1 FROM canvases WHERE id = ?", (canvas_id,)
                ).fetchone():
                    self._insert_edge(
                        conn, NODE_CANVAS, canvas_id, REL_AREA, NODE_AREA, area
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
            if work_id:
                self._insert_edge(
                    conn, NODE_POINTER, pid, REL_FOR_WORK, NODE_WORK, work_id
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
            if conn.execute("SELECT 1 FROM domain_keywords LIMIT 1").fetchone():
                present.add("domain")
            if conn.execute("SELECT 1 FROM phase_refs LIMIT 1").fetchone():
                present.add("phase_ref")
            if conn.execute("SELECT 1 FROM project_facts LIMIT 1").fetchone():
                present.add("memory")
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
            facts = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM project_facts WHERE work_id = ? ORDER BY ts DESC",
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
                "project_facts": facts,
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
