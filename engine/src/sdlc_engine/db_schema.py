"""SQLite schema and typed graph constants for the local index."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

SCHEMA_VERSION = "5"
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
NODE_ENTRY = "entry"
NODE_KEYWORD = "keyword"

REL_CANVAS = "canvas"  # work —has canvas→ REASONS
REL_REQUIREMENT = "requirement"  # work —has requirement→ requirement
REL_REASONS = "reasons"  # requirement —reasons→ canvas
REL_AREA = "area"  # work|requirement|canvas|entry —in area→ area
REL_ABOUT = "about"  # lesson|entry —about→ area|requirement|canvas
REL_RECORDED_FOR = "recorded_for"  # lesson —recorded for→ work
REL_FOR_WORK = "for_work"  # claim|session|entry —for→ work
REL_KEYWORD = "keyword"  # keyword —about→ area|lesson


@dataclass
class RebuildStats:
    work_items: int = 0
    artifacts: int = 0
    local_sessions: int = 0
    requirements: int = 0
    canvases: int = 0
    lessons: int = 0
    staged_lessons: int = 0
    context_entries: int = 0
    domain_keywords: int = 0
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
            f"  lessons: {self.lessons}\n"
            f"  staged_lessons: {self.staged_lessons}\n"
            f"  context_entries: {self.context_entries}\n"
            f"  domain_keywords: {self.domain_keywords}\n"
            f"  edges: {self.edges}\n"
            f"  artifacts: {self.artifacts}\n"
            f"  local_sessions: {self.local_sessions}\n"
            f"  source_commit: {self.source_commit or '(unknown)'}\n"
            f"  rebuilt_at: {self.rebuilt_at}\n"
        )


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS work_search;
        DROP TABLE IF EXISTS edges;
        DROP TABLE IF EXISTS artifacts;
        DROP TABLE IF EXISTS local_sessions;
        DROP TABLE IF EXISTS context_sessions;
        DROP TABLE IF EXISTS claims;
        DROP TABLE IF EXISTS work_areas;
        DROP TABLE IF EXISTS lessons;
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
          registry_status TEXT,
          registry_owner TEXT,
          registry_phase TEXT,
          registry_note TEXT,
          jira_key TEXT,
          github_number TEXT,
          has_canvas INTEGER NOT NULL DEFAULT 0,
          has_requirement INTEGER NOT NULL DEFAULT 0,
          updated TEXT
        );

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

        CREATE TABLE lessons (
          id TEXT PRIMARY KEY,
          kind TEXT NOT NULL,
          work_id TEXT NOT NULL,
          area TEXT NOT NULL DEFAULT '',
          title TEXT NOT NULL DEFAULT '',
          body TEXT NOT NULL DEFAULT '',
          source TEXT NOT NULL DEFAULT '',
          phase TEXT NOT NULL DEFAULT '',
          keywords TEXT NOT NULL DEFAULT '[]',
          ts TEXT NOT NULL DEFAULT '',
          staged INTEGER NOT NULL DEFAULT 0,
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
        CREATE INDEX idx_lessons_staged ON lessons(staged);
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

