"""ContextStore persistence — ledger-first v3."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sdlc_engine.cli import main
from sdlc_engine.context_store import ContextStore
from sdlc_engine.db import LocalIndex
from sdlc_engine.persistence import save_config
from sdlc_engine.project import Project


def _seed_canvas(root: Path, work_id: str) -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(f"# Requirement: {work_id}\n\n## Summary\nProof.\n", encoding="utf-8")
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


def test_persist_lesson_stages_git_and_sqlite(tmp_path: Path) -> None:
    wid = "FEAT-900-persist-proof"
    area = "engine"
    _seed_canvas(tmp_path, wid)
    save_config(tmp_path, {"backends": ["git-pointers", "sqlite"]})
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
    assert result.git.get("staged") is True
    assert result.sqlite.get("ok") is True

    staged_path = tmp_path / ".sdlc" / "staged" / "lessons.jsonl"
    assert staged_path.is_file()
    assert "Never open PRs" in staged_path.read_text(encoding="utf-8")

    idx = LocalIndex(Project(tmp_path))
    lessons = idx.lessons_for_area(area)
    assert len(lessons) == 1
    assert lessons[0]["staged"] == 1
    assert result.sqlite.get("schema") == "5"


def test_persist_accept_and_parity(tmp_path: Path) -> None:
    wid = "FEAT-901-accept"
    _seed_canvas(tmp_path, wid)
    save_config(tmp_path, {"backends": ["git-pointers", "sqlite"]})
    store = ContextStore(Project(tmp_path), guide_base_url="http://127.0.0.1:9")
    store.persist_lesson(
        kind="pattern",
        work_id=wid,
        area="scripts",
        body="Accept me",
        source="test",
        project_guide=False,
    )
    store.accept(work_id=wid, project_guide=False)
    ledger_path = tmp_path / "spdd" / "memory" / "lessons.jsonl"
    assert ledger_path.is_file()
    parity = store.parity(repair=False)
    assert parity["sqlite"]["enabled"] is True
    assert parity["sqlite"]["ok"] is True


def test_cli_persist_lesson_no_guide(tmp_path: Path) -> None:
    wid = "FEAT-903-cli"
    _seed_canvas(tmp_path, wid)
    save_config(tmp_path, {"backends": ["git-pointers", "sqlite"]})
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
            "CLI fan-out writes ledger + sqlite",
            "--no-guide",
        ]
    )
    assert rc == 0
    assert LocalIndex(Project(tmp_path)).lessons_for_work(wid)


def test_cli_persist_lesson_area_only_no_work_id(tmp_path: Path) -> None:
    save_config(tmp_path, {"backends": ["git-pointers", "sqlite"]})
    rc = main(
        [
            "--root",
            str(tmp_path),
            "context",
            "persist-lesson",
            "--kind",
            "pitfall",
            "--area",
            "notify",
            "--source",
            "adhoc-prompt",
            "--body",
            "Retry without an idempotency key double-posts.",
            "--no-guide",
        ]
    )
    assert rc == 0
    staged = (tmp_path / ".sdlc" / "staged" / "lessons.jsonl").read_text(encoding="utf-8")
    assert "FEAT-" not in staged
    assert '"work_id": ""' in staged
    assert "pitfall:(none):notify:adhoc-prompt" in staged
    store = ContextStore(Project(tmp_path), guide_base_url="http://127.0.0.1:9")
    found = store.retrieve(area="notify")
    ids = [row["id"] for row in found["ledger"]]
    assert "pitfall:(none):notify:adhoc-prompt" in ids
    assert all(row.get("work_id") == "" for row in found["ledger"])
    lessons = LocalIndex(Project(tmp_path)).lessons_for_area("notify")
    assert lessons


def test_cli_persist_lesson_requires_work_id_or_area(tmp_path: Path) -> None:
    rc = main(
        [
            "--root",
            str(tmp_path),
            "context",
            "persist-lesson",
            "--kind",
            "pitfall",
            "--body",
            "missing both scopes",
            "--no-guide",
        ]
    )
    assert rc == 2


def test_persist_lesson_calls_guide_project(tmp_path: Path) -> None:
    wid = "FEAT-901-guide-mock"
    _seed_canvas(tmp_path, wid)
    store = ContextStore(Project(tmp_path), guide_base_url="http://guide.test")

    fake_body = json.dumps({"rootPath": str(tmp_path), "workIds": 1, "pitfalls": 1}).encode(
        "utf-8"
    )

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
    assert result.guide.get("ok") is True
    assert mocked.called
