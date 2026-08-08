"""SQLite schema v5 — rebuild from ledger, staged flag, capability coverage."""

from __future__ import annotations

from pathlib import Path

from sdlc_engine.context_model import CONTEXT_KINDS
from sdlc_engine.db import SCHEMA_VERSION, LocalIndex
from sdlc_engine.lessons_ledger import LessonRecord, LessonsLedger
from sdlc_engine.project import Project


def _seed_v5_tree(root: Path, work_id: str) -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(f"# Requirement: {work_id}\n\n## Summary\nV5 tree.\n", encoding="utf-8")
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
    (root / "spdd" / "analysis").mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "analysis" / f"{work_id}-analysis.md").write_text("# Analysis\n", encoding="utf-8")
    (root / "spdd" / "reviews").mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "reviews" / f"{work_id}-review.md").write_text("# Review\n", encoding="utf-8")
    (root / "spdd" / "sync").mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "sync" / f"{work_id}-sync.md").write_text("# Sync\n", encoding="utf-8")

    mem = root / "spdd" / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    ledger = LessonsLedger(Project(root))
    for kind, body in (
        ("decision", "Use ledger v3"),
        ("pitfall", "Never PR embabel/guide"),
        ("pattern", "Dual-write projections"),
    ):
        ledger.append_accepted(
            LessonRecord(
                id="",
                kind=kind,
                work_id=work_id,
                area="engine",
                body=body,
                source="test",
            )
        )
    ledger.append_accepted(
        LessonRecord(
            id="",
            kind="session",
            work_id=work_id,
            title="Session note",
            body="Key point from session",
            source="test",
        )
    )
    ledger.append_accepted(
        LessonRecord(
            id="",
            kind="analysis",
            work_id=work_id,
            area="engine",
            body="Analysis record",
            keywords=["sqlite"],
            source="test",
        )
    )
    ledger.stage(
        LessonRecord(
            id="",
            kind="decision",
            work_id=work_id,
            area="engine",
            body="Staged only",
            source="stage-test",
        )
    )

    hot = root / ".sdlc" / "sessions"
    hot.mkdir(parents=True, exist_ok=True)
    (hot / f"20260808T120000Z-{work_id}-code.md").write_text("# Hot session\n", encoding="utf-8")


def test_schema_version_is_v5(tmp_path: Path) -> None:
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    assert SCHEMA_VERSION == "5"
    assert idx.status_dict()["schema"] == "5"


def test_rebuild_from_ledger_and_staged_flag(tmp_path: Path) -> None:
    wid = "FEAT-920-v5-graph"
    _seed_v5_tree(tmp_path, wid)
    idx = LocalIndex(Project(tmp_path))
    stats = idx.rebuild()
    assert stats.lessons >= 5
    assert stats.staged_lessons >= 1
    staged = idx.query_sql("SELECT id, staged FROM lessons WHERE staged = 1")
    assert staged
    accepted = idx.query_sql("SELECT id FROM lessons WHERE staged = 0")
    assert len(accepted) >= 5


def test_capability_coverage_complete_on_seeded_tree(tmp_path: Path) -> None:
    wid = "FEAT-921-v5-coverage"
    _seed_v5_tree(tmp_path, wid)
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    coverage = idx.capability_coverage()
    assert coverage["complete"] is True, coverage["missing"]
    assert set(CONTEXT_KINDS).issubset(set(coverage["present"]))


def test_graph_for_work_includes_lessons_and_edges(tmp_path: Path) -> None:
    wid = "FEAT-922-v5-edges"
    _seed_v5_tree(tmp_path, wid)
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    graph = idx.graph_for_work(wid)
    assert graph["requirements"]
    assert graph["canvases"]
    assert graph["lessons"]
    assert "project_facts" not in graph
    edge_rels = {(e["src_kind"], e["rel"], e["dst_kind"]) for e in graph["edges"]}
    assert ("requirement", "reasons", "canvas") in edge_rels
    assert ("lesson", "recorded_for", "work") in edge_rels
