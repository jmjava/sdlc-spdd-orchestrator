"""SQLite schema v2 — prove relational graph entry (lessons/areas/claims/pointers)."""

from __future__ import annotations

from pathlib import Path

from sdlc_engine.db import SCHEMA_VERSION, LocalIndex
from sdlc_engine.project import Project


def test_schema_version_is_current_after_rebuild(tmp_path: Path) -> None:
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    assert idx.status_dict()["schema"] == SCHEMA_VERSION
    assert SCHEMA_VERSION == "3"


def test_upsert_lesson_creates_relational_links(tmp_path: Path) -> None:
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    wid = "FEAT-800-graph-lesson"
    area = "com.embabel.guide.spdd"
    lid = f"pitfall:{wid}:{area}:test"

    idx.upsert_lesson(
        lesson_id=lid,
        kind="pitfall",
        work_id=wid,
        area=area,
        body="Never open PRs against embabel/guide",
        source="test",
    )

    by_work = idx.lessons_for_work(wid)
    assert len(by_work) == 1
    assert by_work[0]["id"] == lid
    assert by_work[0]["body"].startswith("Never open")

    by_area = idx.lessons_for_area(area)
    assert {r["id"] for r in by_area} == {lid}

    # work↔area join exists
    rows = idx.query_sql(
        "SELECT work_id, area FROM work_areas WHERE work_id = ? AND area = ?",
        (wid, area),
    )
    assert len(rows) == 1

    # FK parent work_items stub present
    works = idx.query_sql("SELECT work_id FROM work_items WHERE work_id = ?", (wid,))
    assert len(works) == 1


def test_upsert_claim_and_pointer_and_session(tmp_path: Path) -> None:
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    wid = "FEAT-801-claim"

    claim_id = idx.upsert_claim(
        work_id=wid,
        owner="tester",
        status="active",
        phase="code",
        note="claimed for graph test",
    )
    assert claim_id >= 1

    claims = idx.query_sql(
        "SELECT work_id, owner, status FROM claims WHERE work_id = ?",
        (wid,),
    )
    assert claims[0]["owner"] == "tester"
    assert claims[0]["status"] == "active"

    work = idx.find(work_id=wid)[0]
    assert work["registry_status"] == "active"
    assert work["registry_owner"] == "tester"

    idx.upsert_pointer_row(
        pointer_id="ptr_test_1",
        kind="claim",
        work_id=wid,
        intent="claim",
        payload={"claim_id": claim_id},
    )
    ptrs = idx.query_sql("SELECT id, kind FROM pointers WHERE id = ?", ("ptr_test_1",))
    assert ptrs[0]["kind"] == "claim"

    idx.upsert_context_session(
        session_id="sess-1",
        work_id=wid,
        phase="code",
        path=".sdlc/sessions/sess-1.md",
        summary="hot session",
    )
    sessions = idx.query_sql(
        "SELECT id, work_id FROM context_sessions WHERE id = ?",
        ("sess-1",),
    )
    assert sessions[0]["work_id"] == wid


def test_lesson_upsert_is_idempotent(tmp_path: Path) -> None:
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    lid = "decision:W:area:src"
    idx.upsert_lesson(
        lesson_id=lid, kind="decision", work_id="W", area="area", body="v1"
    )
    idx.upsert_lesson(
        lesson_id=lid, kind="decision", work_id="W", area="area", body="v2"
    )
    rows = idx.lessons_for_work("W")
    assert len(rows) == 1
    assert rows[0]["body"] == "v2"
