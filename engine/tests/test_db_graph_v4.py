"""SQLite schema v4 — every agent-context capability is first-class + linked."""

from __future__ import annotations

from pathlib import Path

from sdlc_engine.context_model import CONTEXT_KINDS
from sdlc_engine.db import SCHEMA_VERSION, LocalIndex
from sdlc_engine.project import Project


def _seed_full_agent_context(root: Path, work_id: str) -> None:
    """Minimal but complete tree covering every CONTEXT_KINDS source."""
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(
        f"# Requirement: {work_id}\n\n## Summary\nFull context model.\n",
        encoding="utf-8",
    )
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
    (root / "spdd" / "analysis" / f"{work_id}-analysis.md").write_text(
        f"# Analysis {work_id}\n", encoding="utf-8"
    )
    (root / "spdd" / "reviews").mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "reviews" / f"{work_id}-review.md").write_text(
        f"# Review {work_id}\n", encoding="utf-8"
    )
    (root / "spdd" / "sync").mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "sync" / f"{work_id}-sync.md").write_text(
        f"# Sync {work_id}\n", encoding="utf-8"
    )

    feat = root / "agent-context" / "features" / work_id
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "analysis-context.md").write_text("# analysis mirror\n", encoding="utf-8")
    (feat / "progress-log.md").write_text("# progress\n", encoding="utf-8")
    (feat / "review.md").write_text("# review mirror\n", encoding="utf-8")
    (feat / "sync-log.md").write_text("# sync mirror\n", encoding="utf-8")
    (feat / "retro.md").write_text("# retro\n", encoding="utf-8")
    (feat / "requirement.md").write_text("# req mirror\n", encoding="utf-8")
    (feat / "reasons-canvas.md").write_text("# canvas mirror\n", encoding="utf-8")

    mem = root / "agent-context" / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "context-index.md").write_text(
        f"""# Context Index

| Area | Kind | Work ID | Phase | Timestamp | Source | Entry |
|------|------|---------|-------|-----------|--------|-------|
| scripts/lib | metric | {work_id} | sync | 2026-08-07T00:00:00Z | test | readiness=ok |
| scripts/lib | decision | {work_id} | sync | 2026-08-07T00:00:00Z | test | Use schema v4 |
| scripts/lib | pitfall | {work_id} | sync | 2026-08-07T00:00:00Z | test | Do not PR embabel/guide |
| scripts/lib | pattern | {work_id} | sync | 2026-08-07T00:00:00Z | test | Dual-write indexes |
| scripts/lib | session | {work_id} | sync | 2026-08-07T00:00:00Z | test | sessions/demo.md |
""",
        encoding="utf-8",
    )
    (mem / "domain-index.md").write_text(
        f"""# Domain Index

| Keyword | Area | Kind | Work ID | Timestamp | Entry |
|---------|------|------|---------|-----------|-------|
| neo4j | scripts/lib | analysis | {work_id} | 2026-08-07T00:00:00Z | spdd/analysis/{work_id}-analysis.md |
""",
        encoding="utf-8",
    )
    (mem / "phase-index.md").write_text(
        """# Phase Index

| Phase | Path | Purpose |
|-------|------|---------|
| plan | `ROADMAP.md` | Current focus |
| analysis | `spdd/analysis/` | Analysis context |
""",
        encoding="utf-8",
    )
    (mem / "code-areas.md").write_text(
        "# Code Areas\n\n- scripts/lib\n- spdd/canvas\n",
        encoding="utf-8",
    )
    (mem / "project-memory.md").write_text(
        f"""# Project Memory

## Recent Learnings

### 2026-08-07T00:00:00Z - {work_id}

- Phase: sync
- Summary: Full context model landed
- Next: Quiet mode
""",
        encoding="utf-8",
    )
    (mem / "prompt-optimization-log.md").write_text(
        "## 2026-08-07 prompt tune\n\n- Changed capture flags\n",
        encoding="utf-8",
    )
    (mem / "architecture-decisions.md").write_text("# decisions\n", encoding="utf-8")
    (mem / "known-pitfalls.md").write_text("# pitfalls\n", encoding="utf-8")
    (mem / "reusable-patterns.md").write_text("# patterns\n", encoding="utf-8")

    sessions = root / "agent-context" / "sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    (sessions / f"20260807T000000Z-{work_id}-sync.md").write_text(
        f"# Session {work_id}\n", encoding="utf-8"
    )

    (root / "agent-context" / "playbooks").mkdir(parents=True, exist_ok=True)
    (root / "agent-context" / "playbooks" / "java-feature-playbook.md").write_text(
        "# playbook\n", encoding="utf-8"
    )
    (root / "agent-context" / "harness").mkdir(parents=True, exist_ok=True)
    (root / "agent-context" / "harness" / "quality-gates.md").write_text(
        "# harness\n", encoding="utf-8"
    )
    (root / "agent-context" / "extensions").mkdir(parents=True, exist_ok=True)
    (root / "agent-context" / "extensions" / "example.md").write_text(
        "# extension\n", encoding="utf-8"
    )


def test_schema_version_is_v4(tmp_path: Path) -> None:
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    assert SCHEMA_VERSION == "4"
    assert idx.status_dict()["schema"] == "4"


def test_full_agent_context_capability_coverage(tmp_path: Path) -> None:
    wid = "FEAT-920-full-context"
    _seed_full_agent_context(tmp_path, wid)
    idx = LocalIndex(Project(tmp_path))
    stats = idx.rebuild()

    assert stats.context_entries >= 10
    assert stats.domain_keywords >= 1
    assert stats.phase_refs >= 1
    assert stats.project_facts >= 1

    coverage = idx.capability_coverage()
    assert coverage["complete"] is True, f"missing kinds: {coverage['missing']}"
    assert set(CONTEXT_KINDS).issubset(set(coverage["present"]))

    graph = idx.graph_for_work(wid)
    assert graph["requirements"]
    assert graph["canvases"]
    kinds = {e["kind"] for e in graph["context_entries"]}
    assert "analysis" in kinds
    assert "progress" in kinds
    assert "retro" in kinds
    assert "metric" in kinds
    assert "session" in kinds
    assert "requirement_mirror" in kinds
    assert "canvas_mirror" in kinds

    # Entries link to requirement + REASONS
    edge_set = {(e["src_kind"], e["rel"], e["dst_kind"]) for e in graph["edges"]}
    assert ("requirement", "reasons", "canvas") in edge_set
    assert ("entry", "about", "requirement") in edge_set
    assert ("entry", "about", "canvas") in edge_set
    assert ("entry", "about", "area") in edge_set or ("lesson", "about", "area") in edge_set


def test_upsert_context_entry_links_sections(tmp_path: Path) -> None:
    wid = "FEAT-921-entry-api"
    _seed_full_agent_context(tmp_path, wid)
    idx = LocalIndex(Project(tmp_path))
    idx.rebuild()
    eid = idx.upsert_context_entry(
        kind="progress",
        work_id=wid,
        area="scripts/lib",
        body="Captured via API",
        source="unit-test",
    )
    assert eid
    rows = idx.query_sql(
        "SELECT body FROM context_entries WHERE id = ?", (eid,)
    )
    assert "Captured via API" in rows[0]["body"]
    about_req = idx.query_sql(
        "SELECT 1 AS ok FROM edges WHERE src_id = ? AND dst_id = ?",
        (eid, f"{wid}:requirement"),
    )
    assert about_req
