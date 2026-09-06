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


def _seed_canvas(root: Path, wid: str, *, ready: bool = False, extra: str = "") -> None:
    d = root / "spdd" / "canvas"
    d.mkdir(parents=True, exist_ok=True)
    readiness = "Ready For Coding" if ready else "Needs Analysis"
    (d / f"{wid}.md").write_text(
        f"""# REASONS Canvas: {wid}

## Metadata

- Work ID: {wid}
- Readiness: {readiness}

## R - Requirements

Implement the gated operation for {wid}.

## E - Entities

- Example entity

## A - Approach

One operation.

## S - Structure

- src/app.py

## O - Operations

### T01 - Do the thing

- Status: Not Started
- Files: src/app.py

## N - Norms

- One operation per session

## S - Safeguards

- Do not expand scope

## Review Checklist

- [ ] reviewed

## Sync Notes

{extra}

## Final Status

- Status: In Progress
""",
        encoding="utf-8",
    )


def _seed_review(root: Path, wid: str, *, body: str | None = None) -> None:
    d = root / "spdd" / "reviews"
    d.mkdir(parents=True, exist_ok=True)
    text = body or (
        f"# Review: {wid}\n\n"
        f"**Result:** Approved With Notes\n\n"
        f"Safeguards checked: no scope expansion; tests added.\n"
    )
    (d / f"{wid}-review.md").write_text(text, encoding="utf-8")


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


def test_gate_code_rejects_ready_phrase_outside_readiness_field(
    proj: tuple[Project, WorkflowEngine],
) -> None:
    p, eng = proj
    wid = "FEAT-014-false-ready"
    _seed_req(p.root, wid)
    _seed_canvas(
        p.root,
        wid,
        ready=False,
        extra="Remember: Ready For Coding is written here in Sync Notes only.",
    )
    ok, failures = eng.gate_check(wid, "code")
    assert not ok
    assert any("Ready For Coding" in f for f in failures)


def test_gate_code_rejects_empty_operations(proj: tuple[Project, WorkflowEngine]) -> None:
    p, eng = proj
    wid = "FEAT-014-empty-ops"
    _seed_req(p.root, wid)
    canvas = p.root / "spdd" / "canvas"
    canvas.mkdir(parents=True, exist_ok=True)
    (canvas / f"{wid}.md").write_text(
        """# REASONS Canvas: empty-ops

## Metadata
- Readiness: Ready For Coding

## R - Requirements
A real requirement sentence.

## O - Operations

## S - Safeguards
- none
""",
        encoding="utf-8",
    )
    ok, failures = eng.gate_check(wid, "code")
    assert not ok
    assert any("T##" in f or "operation" in f.lower() for f in failures)


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


def test_gate_local_id_exempt(proj: tuple[Project, WorkflowEngine]) -> None:
    _, eng = proj
    wid = "LOCAL-001-quick-lane"
    for phase in ("analysis", "plan", "code", "review", "sync"):
        ok, failures = eng.gate_check(wid, phase)
        assert ok and not failures, f"LOCAL should bypass {phase}: {failures}"


def test_cli_gate_local_exempt(proj: tuple[Project, WorkflowEngine]) -> None:
    p, _ = proj
    wid = "LOCAL-002-quick-lane"
    rc = main(["--root", str(p.root), "gate", "--phase", "code", "--work-id", wid])
    assert rc == 0


def test_gate_sync_requires_retro_lesson(proj: tuple[Project, WorkflowEngine]) -> None:
    p, eng = proj
    wid = "FEAT-008-gates"
    ok, failures = eng.gate_check(wid, "sync")
    assert not ok
    _stage_record(p.root, wid, kind="decision")
    ok, failures = eng.gate_check(wid, "sync")
    assert ok and not failures


def test_gate_retro_rejects_empty_review(proj: tuple[Project, WorkflowEngine]) -> None:
    p, eng = proj
    wid = "FEAT-016-empty-review"
    _seed_review(p.root, wid, body="# Review: empty\n")
    ok, failures = eng.gate_check(wid, "retro")
    assert not ok
    assert any("minima" in f or "Result" in f or "empty" in f.lower() for f in failures)
    _seed_review(p.root, wid)
    ok, failures = eng.gate_check(wid, "retro")
    assert ok and not failures


def test_sync_does_not_pass_safeguards_on_empty_review(
    proj: tuple[Project, WorkflowEngine],
) -> None:
    p, eng = proj
    wid = "FEAT-016-sync-empty"
    _seed_review(p.root, wid, body="# Review: empty\n")
    state = eng.sync(wid)
    assert state.gates.get("safeguards_checked") != "passed"
    _seed_review(p.root, wid)
    state = eng.sync(wid)
    assert state.gates["safeguards_checked"] == "passed"
    assert state.gates["review_completed"] == "passed"


def test_advertised_gates_are_enforced_or_labeled_advisory() -> None:
    from sdlc_engine.phases import ADVISORY_GATES, ENFORCED_GATES, GATE_LABELS

    assert set(GATE_LABELS) == ADVISORY_GATES | ENFORCED_GATES
    for name in ADVISORY_GATES:
        assert "(advisory)" in GATE_LABELS[name].lower(), name
    for name in ENFORCED_GATES:
        assert "(advisory)" not in GATE_LABELS[name].lower(), name
