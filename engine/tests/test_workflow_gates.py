"""Workflow gate_check enforcement tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sdlc_engine.cli import main
from sdlc_engine.lessons_ledger import LessonRecord, LessonsLedger
from sdlc_engine.pointer import PointerStore
from sdlc_engine.project import Project
from sdlc_engine.workflow import WorkflowEngine


def _seed_req(root: Path, wid: str) -> None:
    d = root / "requirements" / "milestones"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{wid}.md").write_text(f"# Requirement: {wid}\n\n## Summary\nTest.\n", encoding="utf-8")


def _seed_analysis(root: Path, wid: str) -> None:
    d = root / "spdd" / "analysis"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{wid}-analysis.md").write_text(f"# Analysis: {wid}\n", encoding="utf-8")


def _seed_canvas(root: Path, wid: str, *, ready: bool = False) -> None:
    d = root / "spdd" / "canvas"
    d.mkdir(parents=True, exist_ok=True)
    status = "Ready For Coding" if ready else "Draft"
    (d / f"{wid}.md").write_text(
        f"# REASONS Canvas: {wid}\n\n## Metadata\n\n- Status: {status}\n",
        encoding="utf-8",
    )


def _seed_review(root: Path, wid: str) -> None:
    d = root / "spdd" / "reviews"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{wid}-review.md").write_text(f"# Review: {wid}\n", encoding="utf-8")


def _stage_record(root: Path, wid: str, kind: str = "session") -> None:
    LessonsLedger(Project(root)).stage(
        LessonRecord(id="", kind=kind, work_id=wid, title="t", body="b")
    )


@pytest.fixture
def proj(tmp_path: Path) -> tuple[Project, WorkflowEngine]:
    p = Project(tmp_path)
    p.ensure_runtime_dirs()
    return p, WorkflowEngine(p)


def test_gate_analysis_requires_requirement(proj: tuple[Project, WorkflowEngine]) -> None:
    _, eng = proj
    wid = "FEAT-001-gates"
    ok, failures = eng.gate_check(wid, "analysis")
    assert not ok
    assert any("requirement missing" in f for f in failures)


def test_gate_plan_requires_analysis_or_skip(proj: tuple[Project, WorkflowEngine]) -> None:
    p, eng = proj
    wid = "FEAT-002-gates"
    _seed_req(p.root, wid)
    ok, _ = eng.gate_check(wid, "plan")
    assert not ok
    _seed_analysis(p.root, wid)
    ok, failures = eng.gate_check(wid, "plan")
    assert ok and not failures


def test_gate_code_requires_ready_canvas(proj: tuple[Project, WorkflowEngine]) -> None:
    p, eng = proj
    wid = "FEAT-003-gates"
    _seed_req(p.root, wid)
    _seed_canvas(p.root, wid, ready=False)
    ok, failures = eng.gate_check(wid, "code")
    assert not ok
    assert any("Ready For Coding" in f for f in failures)
    _seed_canvas(p.root, wid, ready=True)
    ok, failures = eng.gate_check(wid, "code")
    assert ok and not failures


def test_advance_blocked_without_prereqs(proj: tuple[Project, WorkflowEngine]) -> None:
    p, eng = proj
    wid = "FEAT-004-gates"
    PointerStore(p).set(wid)
    eng.ensure_state(wid)
    with pytest.raises(ValueError, match="gate check failed"):
        eng.advance(to="plan")


def test_advance_force_bypasses(proj: tuple[Project, WorkflowEngine]) -> None:
    p, eng = proj
    wid = "FEAT-005-gates"
    PointerStore(p).set(wid)
    eng.ensure_state(wid)
    state = eng.advance(to="plan", force=True)
    assert state.phase == "plan"


def test_skip_bypasses_analysis_for_plan(proj: tuple[Project, WorkflowEngine]) -> None:
    p, eng = proj
    wid = "FEAT-006-gates"
    _seed_req(p.root, wid)
    PointerStore(p).set(wid)
    eng.skip("analysis", "spike")
    ok, failures = eng.gate_check(wid, "plan")
    assert ok and not failures


def test_cli_gate_exit_codes(proj: tuple[Project, WorkflowEngine], capsys) -> None:
    p, _ = proj
    wid = "FEAT-007-gates"
    rc = main(["--root", str(p.root), "gate", "--phase", "analysis", "--work-id", wid])
    assert rc == 1
    _seed_req(p.root, wid)
    rc = main(["--root", str(p.root), "gate", "--phase", "analysis", "--work-id", wid])
    assert rc == 0


def test_gate_sync_requires_retro_lesson(proj: tuple[Project, WorkflowEngine]) -> None:
    p, eng = proj
    wid = "FEAT-008-gates"
    ok, failures = eng.gate_check(wid, "sync")
    assert not ok
    _stage_record(p.root, wid, kind="decision")
    ok, failures = eng.gate_check(wid, "sync")
    assert ok and not failures
