"""Prove ContextStore writes enter git pointers, SQLite, and Guide DICE."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sdlc_engine.cli import main
from sdlc_engine.context_store import ContextStore
from sdlc_engine.db import LocalIndex
from sdlc_engine.pointers import PointerLedger
from sdlc_engine.project import Project


def _seed_canvas(root: Path, work_id: str) -> None:
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"""# REASONS Canvas: {work_id} - Persistence proof

## Metadata

- Work ID: {work_id}
- Work Type: Feature
- Status: In Progress
""",
        encoding="utf-8",
    )
    # lean stay-set dirs
    mem = root / "spdd" / "memory" / "lessons"
    mem.mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "memory" / "pointers.jsonl").write_text("", encoding="utf-8")


def test_persist_lesson_enters_git_and_sqlite(tmp_path: Path) -> None:
    wid = "FEAT-900-persist-proof"
    area = "com.embabel.guide.spdd"
    _seed_canvas(tmp_path, wid)
    store = ContextStore(Project(tmp_path), guide_base_url="http://127.0.0.1:9")

    result = store.persist_lesson(
        kind="pitfall",
        work_id=wid,
        area=area,
        body="Never open PRs against embabel/guide",
        source="unit-test",
        project_guide=False,
    )
    assert result.git.get("ok") is True
    assert result.sqlite.get("ok") is True
    assert result.guide.get("skipped") is True

    # --- Path 1: lean git ---
    lesson_file = tmp_path / "spdd" / "memory" / "lessons" / "pitfalls.md"
    assert lesson_file.is_file()
    text = lesson_file.read_text(encoding="utf-8")
    assert "Never open PRs against embabel/guide" in text
    assert f"id: pitfall:{wid}:{area}:unit-test" in text

    index = (tmp_path / "spdd" / "memory" / "context-index.md").read_text(encoding="utf-8")
    assert f"| {area} | pitfall | {wid} |" in index

    ptrs = PointerLedger(Project(tmp_path)).list(work_id=wid, kind="lesson")
    assert len(ptrs) == 1
    assert ptrs[0].links.get("lesson_id") == f"pitfall:{wid}:{area}:unit-test"
    assert area in (ptrs[0].links.get("areas") or [])

    # --- Path 2: SQLite relational ---
    idx = LocalIndex(Project(tmp_path))
    lessons = idx.lessons_for_area(area)
    assert len(lessons) == 1
    assert lessons[0]["work_id"] == wid
    assert lessons[0]["kind"] == "pitfall"
    areas = idx.query_sql(
        "SELECT area FROM work_areas WHERE work_id = ?",
        (wid,),
    )
    assert areas[0]["area"] == area


def test_cli_persist_lesson_no_guide(tmp_path: Path) -> None:
    wid = "FEAT-903-cli"
    _seed_canvas(tmp_path, wid)
    rc = main(
        [
            "--root",
            str(tmp_path),
            "context",
            "persist-lesson",
            "--kind",
            "pattern",
            "--work-id",
            wid,
            "--area",
            "scripts/lib",
            "--body",
            "CLI fan-out writes lean git + sqlite",
            "--no-guide",
        ]
    )
    assert rc == 0
    assert LocalIndex(Project(tmp_path)).lessons_for_work(wid)
    assert PointerLedger(Project(tmp_path)).list(work_id=wid, kind="lesson")


def test_persist_lesson_calls_guide_project(tmp_path: Path) -> None:
    wid = "FEAT-901-guide-mock"
    _seed_canvas(tmp_path, wid)
    store = ContextStore(Project(tmp_path), guide_base_url="http://guide.test")

    fake_body = json.dumps(
        {
            "rootPath": str(tmp_path),
            "workIds": 1,
            "pitfalls": 1,
            "decisions": 0,
            "patterns": 0,
        }
    ).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = fake_body
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False

    with patch("sdlc_engine.context_store.urllib.request.urlopen", return_value=mock_resp) as mocked:
        result = store.persist_lesson(
            kind="pitfall",
            work_id=wid,
            area="area-x",
            body="guide fan-out proof",
            source="mock",
            project_guide=True,
        )

    assert result.git.get("ok") is True
    assert result.sqlite.get("ok") is True
    assert result.guide.get("ok") is True
    assert result.guide.get("pitfalls") == 1
    assert result.ok is True
    assert mocked.called
    req = mocked.call_args.args[0]
    assert req.full_url.endswith("/api/v1/data/spdd-projection/load")


def _guide_live() -> bool:
    import urllib.request

    base = os.environ.get("GUIDE_BASE_URL", "http://localhost:21337").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/actuator/health", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


@pytest.mark.skipif(not _guide_live(), reason="Guide not running on GUIDE_BASE_URL/:21337")
def test_live_persist_enters_all_three_backends() -> None:
    """Live E2E: git stay-set + SQLite rows + Guide Neo4j projection all see the lesson.

    Fixture root must sit under Guide allowed-roots (orchestrator checkout), not /tmp.
    """
    import shutil
    import uuid

    wid = "FEAT-902-live-triple-persist"
    area = "com.embabel.guide.spdd"
    body = "LIVE-TRIPLE-PERSIST: never contribute to embabel/guide"
    # Resolve from this test file → repo root (…/engine/tests/this.py → repo)
    repo_root = Path(__file__).resolve().parents[2]
    fixture = repo_root / ".sdlc" / "test-fixtures" / f"live-triple-{uuid.uuid4().hex[:8]}"
    try:
        fixture.mkdir(parents=True, exist_ok=True)
        _seed_canvas(fixture, wid)

        store = ContextStore(Project(fixture))
        result = store.persist_lesson(
            kind="pitfall",
            work_id=wid,
            area=area,
            body=body,
            source="live-test",
            project_guide=True,
        )
        assert result.git.get("ok") is True, result.as_dict()
        assert result.sqlite.get("ok") is True, result.as_dict()
        assert result.guide.get("ok") is True, result.as_dict()
        assert result.ok is True, result.as_dict()

        # git
        assert body in (fixture / "spdd/memory/lessons/pitfalls.md").read_text(encoding="utf-8")
        assert PointerLedger(Project(fixture)).list(work_id=wid)

        # sqlite
        sqlite_lessons = LocalIndex(Project(fixture)).lessons_for_work(wid)
        assert any(body in (r.get("body") or "") for r in sqlite_lessons)

        # guide retrieve — description/name carries index Entry column; body marker is in Entry path/text
        work = store.guide_work(wid)
        assert work.get("found") is True
        pitfalls = work.get("pitfalls") or []
        assert pitfalls, f"expected Guide pitfalls for {wid}, got {work}"
        blob = json.dumps(pitfalls)
        assert "LIVE-TRIPLE-PERSIST" in blob, blob

        assembled = store.retrieve(work_id=wid, area=area)
        assert assembled["git_pointers"]
        assert assembled["sqlite_lessons"]
        assert assembled["guide"] and assembled["guide"].get("found") is True
    finally:
        shutil.rmtree(fixture, ignore_errors=True)