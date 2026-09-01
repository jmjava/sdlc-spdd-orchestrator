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


def test_area_only_record_validates_without_work_id(tmp_path) -> None:
    rec = LessonRecord(
        id="",
        kind="pitfall",
        work_id="",
        area="notify",
        body="Retry without an idempotency key double-posts.",
        source="adhoc-prompt",
    )
    rec.validate()
    assert rec.id == "pitfall:(none):notify:adhoc-prompt"
    assert rec.work_id == ""


def test_record_requires_work_id_or_area() -> None:
    rec = LessonRecord(
        id="",
        kind="pitfall",
        work_id="",
        area="",
        body="no scope",
        source="adhoc-prompt",
    )
    try:
        rec.validate()
    except ValueError as exc:
        assert "work_id or area" in str(exc)
    else:
        raise AssertionError("expected validate to require work_id or area")


def test_stage_and_retrieve_area_only(tmp_path) -> None:
    project = Project(tmp_path)
    project.memory_dir.mkdir(parents=True, exist_ok=True)
    ledger = LessonsLedger(project)
    rec = ledger.stage(
        LessonRecord(
            id="",
            kind="pitfall",
            work_id="",
            area="notify",
            body="Retry without an idempotency key double-posts.",
            source="adhoc-prompt",
        )
    )
    assert rec.id == "pitfall:(none):notify:adhoc-prompt"
    by_area = ledger.records(area="notify")
    assert [r.id for r in by_area] == [rec.id]
    by_feat = ledger.records(work_id="FEAT-001")
    assert by_feat == []


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
