"""SQLite schema v3 — full graph: requirements ↔ REASONS ↔ context parts."""

from __future__ import annotations

from pathlib import Path

from sdlc_engine.db import (
    NODE_AREA,
    NODE_CANVAS,
    NODE_LESSON,
    NODE_REQUIREMENT,
    NODE_WORK,
    REL_ABOUT,
    REL_AREA,
    REL_CANVAS,
    REL_REASONS,
    REL_REQUIREMENT,
    SCHEMA_VERSION,
    LocalIndex,
)
from sdlc_engine.project import Project


def _seed_stay_set(root: Path, work_id: str) -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(
        f"""# Requirement: {work_id}

## Summary

Scope for {work_id}.

## Jira

- Key: ORCH-900
- Summary: Graph schema {work_id}
""",
        encoding="utf-8",
    )
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"""# REASONS Canvas: {work_id} - Graph

## Metadata

- Work ID: {work_id}
- Work Type: Feature
- Status: In Progress
- Source System: Jira
- Source Issue: ORCH-900
""",
        encoding="utf-8",
    )


def test_schema_version_is_v3_after_rebuild(tmp_path: Path) -> None:
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    assert idx.status_dict()["schema"] == SCHEMA_VERSION
    assert SCHEMA_VERSION == "4"


def test_rebuild_links_requirement_to_reasons_canvas(tmp_path: Path) -> None:
    wid = "FEAT-910-full-graph"
    _seed_stay_set(tmp_path, wid)
    idx = LocalIndex(Project(tmp_path))
    stats = idx.rebuild()
    assert stats.requirements >= 1
    assert stats.canvases >= 1
    assert stats.edges >= 3  # work→req, work→canvas, req→reasons→canvas

    reqs = idx.query_sql(
        "SELECT id, work_id, path FROM requirements WHERE work_id = ?", (wid,)
    )
    assert len(reqs) == 1
    assert reqs[0]["id"] == f"{wid}:requirement"
    assert "requirements/milestones" in reqs[0]["path"]

    canvases = idx.query_sql(
        "SELECT id, path FROM canvases WHERE work_id = ?", (wid,)
    )
    assert len(canvases) == 1
    assert canvases[0]["id"] == f"{wid}:canvas"

    edges = {
        (e["src_kind"], e["rel"], e["dst_kind"])
        for e in idx.query_sql(
            "SELECT src_kind, rel, dst_kind FROM edges WHERE src_id LIKE ? OR dst_id LIKE ?",
            (f"{wid}%", f"{wid}%"),
        )
    }
    assert (NODE_WORK, REL_REQUIREMENT, NODE_REQUIREMENT) in edges
    assert (NODE_WORK, REL_CANVAS, NODE_CANVAS) in edges
    assert (NODE_REQUIREMENT, REL_REASONS, NODE_CANVAS) in edges


def test_lesson_links_to_requirement_reasons_and_area(tmp_path: Path) -> None:
    wid = "FEAT-911-context-links"
    area = "com.embabel.guide.spdd"
    _seed_stay_set(tmp_path, wid)
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()

    lid = f"decision:{wid}:{area}:test"
    idx.upsert_lesson(
        lesson_id=lid,
        kind="decision",
        work_id=wid,
        area=area,
        body="Schema must cover requirements, REASONS, and context parts",
        source="test",
    )

    graph = idx.graph_for_work(wid)
    assert graph["work"] is not None
    assert len(graph["requirements"]) == 1
    assert len(graph["canvases"]) == 1
    assert len(graph["areas"]) == 1
    assert graph["areas"][0]["id"] == area
    assert len(graph["lessons"]) == 1

    edge_set = {(e["src_kind"], e["src_id"], e["rel"], e["dst_kind"], e["dst_id"]) for e in graph["edges"]}
    assert (NODE_LESSON, lid, REL_ABOUT, NODE_AREA, area) in edge_set
    assert (
        NODE_LESSON,
        lid,
        REL_ABOUT,
        NODE_REQUIREMENT,
        f"{wid}:requirement",
    ) in edge_set
    assert (NODE_LESSON, lid, REL_ABOUT, NODE_CANVAS, f"{wid}:canvas") in edge_set
    assert (NODE_REQUIREMENT, f"{wid}:requirement", REL_AREA, NODE_AREA, area) in edge_set
    assert (NODE_CANVAS, f"{wid}:canvas", REL_AREA, NODE_AREA, area) in edge_set
    assert (NODE_WORK, wid, REL_AREA, NODE_AREA, area) in edge_set

    ctx_req = idx.context_linked_to_section(
        section_kind=NODE_REQUIREMENT, section_id=f"{wid}:requirement"
    )
    assert {a["id"] for a in ctx_req["areas"]} == {area}
    assert {l["id"] for l in ctx_req["lessons"]} == {lid}
    assert {c["id"] for c in ctx_req["reasons_canvases"]} == {f"{wid}:canvas"}

    ctx_canvas = idx.context_linked_to_section(
        section_kind=NODE_CANVAS, section_id=f"{wid}:canvas"
    )
    assert {a["id"] for a in ctx_canvas["areas"]} == {area}
    assert {l["id"] for l in ctx_canvas["lessons"]} == {lid}


def test_sync_stay_set_upsert_apis(tmp_path: Path) -> None:
    wid = "FEAT-912-sync"
    _seed_stay_set(tmp_path, wid)
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    # Clear section nodes to prove sync re-creates them without full rebuild.
    with idx.connect() as conn:
        conn.execute("DELETE FROM edges")
        conn.execute("DELETE FROM requirements")
        conn.execute("DELETE FROM canvases")
        conn.commit()

    synced = idx.sync_stay_set(wid)
    assert synced["requirement_id"] == f"{wid}:requirement"
    assert synced["canvas_id"] == f"{wid}:canvas"
    reasons = idx.query_sql(
        "SELECT rel FROM edges WHERE src_id = ? AND dst_id = ?",
        (f"{wid}:requirement", f"{wid}:canvas"),
    )
    assert reasons[0]["rel"] == REL_REASONS
