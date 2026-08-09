from pathlib import Path

from sdlc_engine.lessons_ledger import LessonRecord, LessonsLedger
from sdlc_engine.project import Project
from sdlc_engine.workflow import WorkflowEngine


def _write_requirement(root: Path, work_id: str) -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(f"# Requirement: {work_id}\n\n## Summary\nWorkflow test seed.\n", encoding="utf-8")


def _write_canvas(root: Path, work_id: str, status: str = "Ready For Coding") -> None:
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"# {work_id}\n\n## Operations\n\n### T01 - First\n\n- Status: Not Started\n\n## Final Status\n\n- Status: {status}\n",
        encoding="utf-8",
    )


def test_resume_advance_shelf_next(tmp_path: Path) -> None:
    root = tmp_path
    work_id = "FEAT-010-flow"
    _write_requirement(root, work_id)
    _write_canvas(root, work_id)
    LessonsLedger(Project(root)).stage(
        LessonRecord(id="", kind="session", work_id=work_id, body="T01 complete — workflow test")
    )
    eng = WorkflowEngine(Project(root))
    state = eng.resume(work_id)
    assert eng.pointer.get() == work_id
    assert state.phase in {"architect", "code", "plan", "analysis", "init"}
    eng.advance()
    after = eng.load_state(work_id)
    assert after.phase != state.phase or state.phase == "sync"
    text = eng.next_text()
    assert "Do now" in text
    assert work_id in text
    eng.shelf("pause")
    assert eng.pointer.get() == ""
    shelved = eng.list_shelved()
    assert any(s[0] == work_id for s in shelved)


def test_status_json(tmp_path: Path) -> None:
    work_id = "FEAT-011-json"
    _write_requirement(tmp_path, work_id)
    _write_canvas(tmp_path, work_id)
    eng = WorkflowEngine(Project(tmp_path))
    eng.resume(work_id)
    raw = eng.status_json()
    assert '"phase"' in raw
    assert work_id in raw
