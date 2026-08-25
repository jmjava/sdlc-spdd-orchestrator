"""In-place upgrade of old SQLite caches before v5 persist writes.

A leftover schema v4 ``index.sqlite`` (no ``title`` / ``phase`` / ``keywords`` /
``staged`` on ``lessons``) cannot accept the current persist INSERT. Persist
must upgrade that file in place first — this is the check that the upgrade
is required, then that it happens automatically.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from sdlc_engine.context_store import ContextStore
from sdlc_engine.db import SCHEMA_VERSION, LocalIndex
from sdlc_engine.persistence import save_config
from sdlc_engine.project import Project


def _seed_stay_set(root: Path, work_id: str) -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(f"# Requirement: {work_id}\n\n## Summary\nOld cache.\n", encoding="utf-8")
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"""# REASONS Canvas: {work_id}

## Metadata

- Work ID: {work_id}
- Work Type: Feature
- Status: In Progress
""",
        encoding="utf-8",
    )
    root.joinpath("spdd/memory").mkdir(parents=True, exist_ok=True)


def _write_v4_sqlite(db_path: Path, *, work_id: str = "FEAT-OLD-V4") -> None:
    """Write a schema-v4 cache: lessons rows have no staged/title/phase/keywords."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE meta (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        CREATE TABLE work_items (
          work_id TEXT PRIMARY KEY,
          title TEXT,
          updated TEXT
        );
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
        """
    )
    conn.execute("INSERT INTO meta(key, value) VALUES ('schema_version', '4')")
    conn.execute(
        "INSERT INTO work_items(work_id, title, updated) VALUES (?,?,?)",
        (work_id, work_id, "2026-01-01T00:00:00Z"),
    )
    conn.execute(
        "INSERT INTO lessons(id, kind, work_id, area, body, source, ts) VALUES (?,?,?,?,?,?,?)",
        (
            f"decision:{work_id}:engine:test",
            "decision",
            work_id,
            "engine",
            "legacy v4 body",
            "test",
            "2026-01-01T00:00:00Z",
        ),
    )
    conn.commit()
    conn.close()


def _write_unreadable_legacy_sqlite(db_path: Path) -> None:
    """Old file with no meta table — _meta() would throw without a guard."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE leftover (id INTEGER PRIMARY KEY, note TEXT)")
    conn.execute("INSERT INTO leftover(note) VALUES ('pre-meta cache')")
    conn.commit()
    conn.close()


def _v5_persist_insert(conn: sqlite3.Connection) -> None:
    """The column list persist uses today (schema v5)."""
    conn.execute(
        "INSERT INTO lessons("
        "id, kind, work_id, area, title, body, source, phase, keywords, ts, staged) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "pitfall:FEAT-OLD-V4:engine:probe",
            "pitfall",
            "FEAT-OLD-V4",
            "engine",
            "probe",
            "needs staged column",
            "probe",
            "code",
            "[]",
            "2026-08-25T00:00:00Z",
            1,
        ),
    )


def test_v5_persist_row_fails_on_old_schema_without_upgrade(tmp_path: Path) -> None:
    """Confirm: the persistence write cannot land until the old format is upgraded."""
    db_path = tmp_path / ".sdlc" / "index.sqlite"
    _write_v4_sqlite(db_path)
    conn = sqlite3.connect(str(db_path))
    with pytest.raises(sqlite3.OperationalError, match="staged|title|phase|keywords"):
        _v5_persist_insert(conn)
    ver = conn.execute(
        "SELECT value FROM meta WHERE key = 'schema_version'"
    ).fetchone()[0]
    assert ver == "4"
    cols = {row[1] for row in conn.execute("PRAGMA table_info(lessons)").fetchall()}
    assert "staged" not in cols
    conn.close()


def test_persist_upgrades_v4_sqlite_in_place_then_succeeds(tmp_path: Path) -> None:
    wid = "FEAT-OLD-V4"
    _seed_stay_set(tmp_path, wid)
    save_config(tmp_path, {"backends": ["git-pointers", "sqlite"]})
    db_path = tmp_path / ".sdlc" / "index.sqlite"
    _write_v4_sqlite(db_path, work_id=wid)

    store = ContextStore(Project(tmp_path), guide_base_url="http://127.0.0.1:9")
    result = store.persist_lesson(
        kind="pitfall",
        work_id=wid,
        area="engine",
        body="upgrade first, then persist",
        source="upgrade-check",
        project_guide=False,
    )
    assert result.git.get("ok") is True
    assert result.sqlite.get("ok") is True, result.sqlite
    assert result.sqlite.get("schema") == SCHEMA_VERSION

    idx = LocalIndex(Project(tmp_path))
    status = idx.status_dict()
    assert status["schema"] == SCHEMA_VERSION
    with idx.connect() as conn:
        col_names = {row[1] for row in conn.execute("PRAGMA table_info(lessons)").fetchall()}
    assert {"title", "phase", "keywords", "staged"} <= col_names
    rows = idx.lessons_for_work(wid)
    assert any("upgrade first, then persist" in (r.get("body") or "") for r in rows)
    staged = idx.query_sql("SELECT staged FROM lessons WHERE body LIKE ?", ("%upgrade first%",))
    assert staged and staged[0]["staged"] == 1


def test_ensure_schema_rebuilds_unreadable_legacy_db(tmp_path: Path) -> None:
    _seed_stay_set(tmp_path, "FEAT-NO-META")
    db_path = tmp_path / ".sdlc" / "index.sqlite"
    _write_unreadable_legacy_sqlite(db_path)
    idx = LocalIndex(Project(tmp_path))
    idx.ensure_schema()
    assert idx.status_dict()["schema"] == SCHEMA_VERSION
    assert idx.status_dict().get("error") is None
