"""LessonsLedger stage/accept/dedupe/digest."""

from __future__ import annotations

from sdlc_engine.lessons_ledger import LessonRecord, LessonsLedger
from sdlc_engine.project import Project


def test_stage_accept_and_dedupe(tmp_path) -> None:
    project = Project(tmp_path)
    project.memory_dir.mkdir(parents=True, exist_ok=True)
    ledger = LessonsLedger(project)
    rec = ledger.stage(
        LessonRecord(
            id="",
            kind="pitfall",
            work_id="FEAT-001",
            area="engine",
            body="First capture",
            source="test",
        )
    )
    assert rec.id in ledger.staged_ids()
    assert rec.id not in ledger.accepted_ids()
    out = ledger.accept(ids=[rec.id])
    assert rec.id in ledger.accepted_ids()
    assert rec.id not in ledger.staged_ids()
    assert out["accepted_count"] == 1

    ledger.append_accepted(
        LessonRecord(
            id=rec.id,
            kind="pitfall",
            work_id="FEAT-001",
            area="engine",
            body="Updated body",
            source="test",
        )
    )
    got = ledger.get(rec.id)
    assert got is not None
    assert "Updated" in got.body


def test_digest_bounded(tmp_path) -> None:
    project = Project(tmp_path)
    project.memory_dir.mkdir(parents=True, exist_ok=True)
    ledger = LessonsLedger(project)
    for i in range(5):
        ledger.append_accepted(
            LessonRecord(
                id="",
                kind="decision",
                work_id="FEAT-002",
                area="scripts",
                body=f"Decision {i}",
                keywords=["cli"],
                source=f"t{i}",
            )
        )
    d = ledger.digest(areas=["scripts"], keywords=["cli"], limit=3)
    assert d["total"] >= 5
    assert len(d["top"]) <= 3
