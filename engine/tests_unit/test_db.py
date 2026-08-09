from pathlib import Path

from sdlc_engine.cli import main
from sdlc_engine.db import LocalIndex
from sdlc_engine.project import Project
from sdlc_engine.registry import TeamRegistry


def _seed(root: Path, work_id: str, *, jira: str = "ORCH-1", status: str = "In Progress") -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

Indexed work for {work_id}.

## Jira

- Key: {jira}
- Summary: Indexed {work_id}

### Description

Body for search.
""",
        encoding="utf-8",
    )
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"""# REASONS Canvas: {work_id} - Indexed demo

## Metadata

- Work ID: {work_id}
- Work Type: Feature
- Status: {status}
- Source System: Jira
- Source Issue: {jira}
- Milestone: milestone-1.md

## Final Status

- Status: {status}
""",
        encoding="utf-8",
    )
    feat = root / "agent-context" / "features" / work_id
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "requirement.md").write_text(f"# {work_id}\n", encoding="utf-8")


def test_rebuild_and_query(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "db-tester")
    a = "FEAT-700-sqlite-a"
    b = "FEAT-701-sqlite-b"
    _seed(tmp_path, a, jira="ORCH-70")
    _seed(tmp_path, b, jira="ORCH-71", status="Draft")
    TeamRegistry(Project(tmp_path)).claim(a)

    idx = LocalIndex(Project(tmp_path))
    stats = idx.rebuild()
    assert stats.work_items >= 2
    assert idx.db_path.is_file()
    assert idx.db_path.parent.name == ".sdlc"

    rows = idx.find(work_id=a)
    assert len(rows) == 1
    assert rows[0]["jira_key"] == "ORCH-70"
    assert rows[0]["registry_status"] == "active"
    assert rows[0]["has_canvas"] == 1

    searched = idx.find(search="Indexed")
    assert {r["work_id"] for r in searched} >= {a, b}

    sql_rows = idx.query_sql(
        "SELECT work_id, jira_key FROM work_items WHERE jira_key = ?",
        ("ORCH-71",),
    )
    assert sql_rows[0]["work_id"] == b


def test_query_rejects_writes(tmp_path: Path) -> None:
    _seed(tmp_path, "FEAT-702-safe")
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    try:
        idx.query_sql("DELETE FROM work_items")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "read-only" in str(exc)


def test_export_json_and_cli(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "db-tester")
    _seed(tmp_path, "FEAT-703-export")
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    out = tmp_path / "export.json"
    text = idx.export_json(out)
    assert '"work_items"' in text
    assert out.is_file()

    assert main(["--root", str(tmp_path), "db", "rebuild"]) == 0
    assert main(["--root", str(tmp_path), "db", "status"]) == 0
    assert main(["--root", str(tmp_path), "db", "query", "--search", "export"]) == 0
    assert (
        main(
            [
                "--root",
                str(tmp_path),
                "db",
                "query",
                "SELECT work_id FROM work_items LIMIT 5",
                "--json",
            ]
        )
        == 0
    )


def test_lookup_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "db-tester")
    wid = "FEAT-704-lookup"
    _seed(tmp_path, wid, jira="ORCH-74")
    TeamRegistry(Project(tmp_path)).claim(wid)
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()

    data = idx.lookup(wid)
    assert data["available"] is True
    assert data["work_item"] is not None
    assert data["work_item"]["work_id"] == wid
    assert data["work_item"]["jira_key"] == "ORCH-74"
    assert data["work_item"]["has_canvas"] == 1
    assert data["work_item"]["registry_status"] == "active"

    md = idx.lookup_markdown(wid)
    assert "## Local SQLite Index (query cache)" in md
    assert wid in md
    assert "has_canvas" in md
    assert "registry_status" in md

    assert main(["--root", str(tmp_path), "db", "lookup", "--work-id", wid, "--json"]) == 0
    assert (
        main(
            [
                "--root",
                str(tmp_path),
                "db",
                "lookup",
                "--work-id",
                wid,
                "--markdown",
            ]
        )
        == 0
    )


def test_lookup_rebuilds_when_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "db-tester")
    wid = "FEAT-705-lookup-rebuild"
    _seed(tmp_path, wid)
    idx = LocalIndex(Project(tmp_path))
    assert not idx.db_path.is_file()
    data = idx.lookup(wid)
    assert data["rebuilt"] is True
    assert data["available"] is True
    assert idx.db_path.is_file()


def test_local_sessions_indexed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "db-tester")
    from sdlc_engine.local_sessions import LocalSessionService

    LocalSessionService(Project(tmp_path)).start(name="db-local", intent="index me")
    idx = LocalIndex(Project(tmp_path))
    stats = idx.rebuild()
    assert stats.local_sessions >= 1
    rows = idx.query_sql("SELECT session_id, status FROM local_sessions")
    assert any(r["session_id"].startswith("LOCAL-") for r in rows)
