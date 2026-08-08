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


def test_default_backends_include_all_three(tmp_path: Path) -> None:
    cfg = load_config(tmp_path)
    assert cfg["backends"] == [BACKEND_GIT, BACKEND_SQLITE, BACKEND_GUIDE]


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


def test_lean_only_progress_ingested_on_rebuild(tmp_path: Path) -> None:
    wid = "FEAT-lean-progress-only"
    progress = tmp_path / "spdd" / "memory" / "entries" / "progress.md"
    progress.parent.mkdir(parents=True)
    progress.write_text(
        f"# Progress Entries\n\n## {wid}\n\n- T01 implemented greet helper\n",
        encoding="utf-8",
    )
    idx = LocalIndex(Project(tmp_path))
    stats = idx.rebuild()
    assert stats.context_entries >= 1
    cov = idx.capability_coverage()
    assert "progress" in cov["present"]
    graph = idx.graph_for_work(wid)
    assert any(e.get("kind") == "progress" for e in graph.get("context_entries") or [])


def test_workflow_next_honors_quiet(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "quiet-dev")
    monkeypatch.setenv("SDLC_QUIET", "1")
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
    payload = json.loads(engine.status_json(wid))
    assert payload["quiet"] is True
    assert "/sdlc-spdd-code" not in payload["recommended_command"]


def test_workflow_infers_code_from_lean_progress(tmp_path: Path, monkeypatch) -> None:
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
    progress = tmp_path / "spdd" / "memory" / "entries" / "progress.md"
    progress.parent.mkdir(parents=True)
    progress.write_text(
        f"## {other}\n\n- T01 complete — implemented greet\n\n"
        f"## {wid}\n\n- planning notes only\n",
        encoding="utf-8",
    )
    engine = WorkflowEngine(project)
    # Other work's progress must not force this work into code.
    assert engine.infer_phase_from_artifacts(wid) == "architect"
    progress.write_text(
        f"## {other}\n\n- T01 complete\n\n"
        f"## {wid}\n\n- T01 complete — implemented greet\n",
        encoding="utf-8",
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
