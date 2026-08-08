"""Persistence backend options (#79/#90) — CLI + ContextStore + console API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sdlc_engine.cli import main
from sdlc_engine.context_store import ContextStore
from sdlc_engine.db import LocalIndex
from sdlc_engine.persistence import (
    BACKEND_GIT,
    BACKEND_GUIDE,
    BACKEND_SQLITE,
    load_config,
    save_config,
    status_dict,
)
from sdlc_engine.project import Project
from sdlc_engine.workflow import WorkflowEngine


def test_default_backends_git_and_guide_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("CONTEXT_BACKENDS", raising=False)
    cfg = load_config(tmp_path)
    assert cfg["backends"] == [BACKEND_GIT, BACKEND_GUIDE]


def test_save_and_load_persistence_config(tmp_path: Path) -> None:
    saved = save_config(
        tmp_path,
        {"backends": ["sqlite", "git-pointers"], "notes": "lean only"},
    )
    assert BACKEND_GIT in saved["backends"]
    assert BACKEND_SQLITE in saved["backends"]
    assert BACKEND_GUIDE not in saved["backends"]
    assert (tmp_path / ".sdlc" / "persistence-config.json").is_file()
    status = status_dict(Project(tmp_path))
    assert status["enabled"]["sqlite"] is True
    assert status["enabled"]["guide-dice"] is False
    assert status["notes"] == "lean only"


def test_env_CONTEXT_BACKENDS_overrides_file(tmp_path: Path, monkeypatch) -> None:
    save_config(tmp_path, {"backends": ["git-pointers", "sqlite", "guide-dice"]})
    monkeypatch.setenv("CONTEXT_BACKENDS", "git-pointers,sqlite")
    cfg = load_config(tmp_path)
    assert cfg["backends"] == [BACKEND_GIT, BACKEND_SQLITE]
    assert cfg["source"] == "env:CONTEXT_BACKENDS"


def test_persist_skips_disabled_sqlite_and_guide(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CONTEXT_BACKENDS", "git-pointers")
    project = Project(tmp_path)
    (tmp_path / "spdd" / "canvas").mkdir(parents=True)
    (tmp_path / "spdd" / "canvas" / "FEAT-persist-off.md").write_text(
        "# canvas\n", encoding="utf-8"
    )
    store = ContextStore(project)
    result = store.persist_lesson(
        kind="decision",
        work_id="FEAT-persist-off",
        body="git only",
        project_guide=True,
    )
    assert result.git.get("ok") is True
    assert result.sqlite.get("skipped") is True
    assert result.guide.get("skipped") is True
    assert result.ok is True
    assert result.partial is False
    assert not (tmp_path / ".sdlc" / "index.sqlite").is_file()


def test_cli_context_backends_set(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("CONTEXT_BACKENDS", raising=False)
    rc = main(
        [
            "--root",
            str(tmp_path),
            "context",
            "backends",
            "--set",
            "git-pointers,sqlite",
            "--notes",
            "console-parity",
        ]
    )
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["backends"] == [BACKEND_GIT, BACKEND_SQLITE]
    rc = main(["--root", str(tmp_path), "context", "backends"])
    assert rc == 0
    status = json.loads(capsys.readouterr().out)
    assert status["enabled"]["guide-dice"] is False


def test_ledger_lessons_ingested_on_rebuild(tmp_path: Path) -> None:
    from sdlc_engine.lessons_ledger import LessonRecord, LessonsLedger

    wid = "FEAT-lean-progress-only"
    tmp_path.joinpath("spdd/memory").mkdir(parents=True)
    LessonsLedger(Project(tmp_path)).append_accepted(
        LessonRecord(
            id="",
            kind="decision",
            work_id=wid,
            body="T01 implemented greet helper",
            source="test",
        )
    )
    idx = LocalIndex(Project(tmp_path))
    stats = idx.rebuild()
    assert stats.lessons >= 1
    graph = idx.graph_for_work(wid)
    assert graph["lessons"]


def test_ledger_staged_flag_on_rebuild(tmp_path: Path) -> None:
    from sdlc_engine.lessons_ledger import LessonRecord, LessonsLedger

    wid = "FEAT-capture-progress"
    tmp_path.joinpath("spdd/memory").mkdir(parents=True)
    ledger = LessonsLedger(Project(tmp_path))
    ledger.stage(
        LessonRecord(
            id="",
            kind="decision",
            work_id=wid,
            area="billing",
            phase="code",
            body="T01 implemented greet helper",
            source="capture",
        )
    )
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    rows = idx.query_sql("SELECT staged, phase, area FROM lessons WHERE work_id = ?", (wid,))
    assert rows
    assert rows[0]["staged"] == 1
    assert rows[0]["phase"] == "code"
    assert rows[0]["area"] == "billing"


def test_persist_partial_when_sqlite_fails(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("CONTEXT_BACKENDS", raising=False)
    save_config(tmp_path, {"backends": ["git-pointers", "sqlite"]})
    project = Project(tmp_path)
    (tmp_path / "spdd" / "canvas").mkdir(parents=True)
    (tmp_path / "spdd" / "canvas" / "FEAT-partial.md").write_text(
        "# canvas\n", encoding="utf-8"
    )
    store = ContextStore(project)

    def boom(*_a, **_k):
        raise RuntimeError("sqlite unavailable")

    monkeypatch.setattr(store.index, "upsert_lesson_record", boom)
    result = store.persist_lesson(
        kind="decision",
        work_id="FEAT-partial",
        body="git ok, sqlite fails",
        project_guide=False,
    )
    assert result.git.get("ok") is True
    assert result.ok is True
    assert result.partial is True
    assert result.sqlite.get("ok") is False
    assert any("sqlite:" in e for e in result.errors)
    assert (tmp_path / ".sdlc" / "staged" / "lessons.jsonl").is_file()


def test_retrieve_honors_backend_gating(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CONTEXT_BACKENDS", "git-pointers")
    project = Project(tmp_path)
    (tmp_path / "spdd" / "canvas").mkdir(parents=True)
    (tmp_path / "spdd" / "canvas" / "FEAT-retrieve-off.md").write_text(
        "# canvas\n", encoding="utf-8"
    )
    # Seed sqlite while backends allow it, then gate retrieve off.
    monkeypatch.delenv("CONTEXT_BACKENDS", raising=False)
    store = ContextStore(project)
    store.persist_lesson(
        kind="pitfall",
        work_id="FEAT-retrieve-off",
        body="should not retrieve when sqlite off",
        project_guide=False,
    )
    monkeypatch.setenv("CONTEXT_BACKENDS", "git-pointers")
    gated = ContextStore(project)
    out = gated.retrieve(work_id="FEAT-retrieve-off")
    assert out["ledger"] == [] or isinstance(out["ledger"], list)
    assert out.get("sqlite_graph", {}).get("skipped") is True
    assert out.get("guide", {}).get("skipped") is True
    assert "sqlite" not in out["backends"]
    assert "guide-dice" not in out["backends"]


def test_workflow_next_honors_quiet(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "quiet-dev")
    monkeypatch.setenv("SDLC_QUIET", "ON")
    project = Project(tmp_path)
    wid = "FEAT-quiet-next"
    (tmp_path / "spdd" / "canvas").mkdir(parents=True)
    (tmp_path / "spdd" / "canvas" / f"{wid}.md").write_text(
        f"# REASONS Canvas: {wid}\n\n## O - Operations\n\n### T01 - Do\n- Status: Not Started\n",
        encoding="utf-8",
    )
    engine = WorkflowEngine(project)
    engine.resume(wid, phase="code")
    text = engine.next_text()
    assert "quiet" in text.lower()
    assert "/sdlc-spdd-code" not in text
    assert "Skip recommended" in text or "load resolved context" in text
    payload = json.loads(engine.status_json(wid))
    assert payload["quiet"] is True
    assert "/sdlc-spdd-code" not in payload["recommended_command"]


def test_workflow_infers_code_from_ledger_records(tmp_path: Path, monkeypatch) -> None:
    from sdlc_engine.lessons_ledger import LessonRecord, LessonsLedger

    monkeypatch.setenv("SDLC_USER", "lean-dev")
    project = Project(tmp_path)
    wid = "FEAT-lean-infer"
    other = "FEAT-other-progress"
    (tmp_path / "requirements" / "milestones").mkdir(parents=True)
    (tmp_path / "requirements" / "milestones" / f"{wid}.md").write_text(
        f"# Requirement: {wid}\n", encoding="utf-8"
    )
    (tmp_path / "requirements" / "milestones" / f"{other}.md").write_text(
        f"# Requirement: {other}\n", encoding="utf-8"
    )
    (tmp_path / "spdd" / "canvas").mkdir(parents=True)
    (tmp_path / "spdd" / "canvas" / f"{wid}.md").write_text(
        f"# REASONS Canvas: {wid}\n\n## Metadata\n- Readiness: Needs Analysis\n",
        encoding="utf-8",
    )
    tmp_path.joinpath("spdd/memory").mkdir(parents=True)
    ledger = LessonsLedger(project)
    ledger.stage(
        LessonRecord(
            id="",
            kind="session",
            work_id=other,
            body="T01 complete — implemented greet",
            source="test",
        )
    )
    ledger.stage(
        LessonRecord(
            id="",
            kind="session",
            work_id=wid,
            body="planning notes only",
            source="test",
        )
    )
    engine = WorkflowEngine(project)
    assert engine.infer_phase_from_artifacts(wid) == "architect"
    ledger.stage(
        LessonRecord(
            id="",
            kind="session",
            work_id=wid,
            body="T01 complete — implemented greet",
            source="test2",
        )
    )
    assert engine.infer_phase_from_artifacts(wid) == "code"


def test_cli_rejects_unknown_backends(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("CONTEXT_BACKENDS", raising=False)
    rc = main(
        [
            "--root",
            str(tmp_path),
            "context",
            "backends",
            "--set",
            "git-pointers,sqllite",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "unknown" in err.lower()


def test_save_does_not_roundtrip_default_guide_url(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("CONTEXT_BACKENDS", raising=False)
    monkeypatch.delenv("GUIDE_BASE_URL", raising=False)
    status = status_dict(Project(tmp_path))
    assert status["guide"]["base_url"] == ""
    assert status["guide"]["effective_base_url"].startswith("http://")
    saved = save_config(
        tmp_path,
        {"backends": ["git-pointers", "sqlite"], "guide_base_url": "", "notes": ""},
    )
    assert saved["guide"]["base_url"] == ""
    cfg_file = json.loads(
        (tmp_path / ".sdlc" / "persistence-config.json").read_text(encoding="utf-8")
    )
    assert cfg_file.get("guide_base_url") == ""
