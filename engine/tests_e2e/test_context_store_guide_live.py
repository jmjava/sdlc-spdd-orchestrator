"""Live triple-backend persist and context-select. Requires Guide stack up.

Smoke: persist one pitfall, require the same id from ledger, SQLite, and
live Guide via ``work_subgraph``. Skip/unreachable is not a pass.

T04: two Work IDs / three areas — work subgraph must not mix sibling works;
``area_lessons`` is cross-work for one area and must exclude other areas.
"""

from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path

import pytest

from sdlc_engine.context_store import ContextStore, lesson_ids_from_subgraph
from sdlc_engine.db import LocalIndex
from sdlc_engine.guide_client import GuideClient, resolve_guide_base_url
from sdlc_engine.persistence import save_config
from sdlc_engine.project import Project

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tests" / "research"))

from cretrieve_context_select import (  # noqa: E402
    ids_matching,
    load_records,
    persist_records,
    record_id,
    retrieved_ids,
    seed_canvases,
    subgraph_kind_ids,
)

MARKER = "LIVE-TRIPLE-PERSIST"


def _seed_canvas(root: Path, work_id: str) -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(f"# Requirement: {work_id}\n\n## Summary\nProof.\n", encoding="utf-8")
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
    root.joinpath("spdd/memory").mkdir(parents=True, exist_ok=True)


def test_live_persist_enters_all_backends() -> None:
    base = resolve_guide_base_url()
    if not GuideClient(base, timeout=3.0).health_ok():
        pytest.fail(
            f"Guide not running at {base} — run SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh"
        )

    wid = "FEAT-902-live-triple-persist"
    repo_root = Path(__file__).resolve().parents[2]
    fixture = repo_root / ".sdlc" / "test-fixtures" / f"live-triple-{uuid.uuid4().hex[:8]}"
    try:
        fixture.mkdir(parents=True, exist_ok=True)
        _seed_canvas(fixture, wid)
        save_config(
            fixture,
            {
                "backends": ["git-pointers", "sqlite", "guide-dice"],
                "guide_base_url": base,
            },
        )
        store = ContextStore(Project(fixture), guide_base_url=base)
        result = store.persist_lesson(
            kind="pitfall",
            work_id=wid,
            area="engine",
            body=MARKER,
            source="live-test",
            accept=True,
            project_guide=True,
        )
        assert result.ok is True, result.as_dict()
        lesson_id = str(result.git.get("id") or "")
        assert lesson_id, result.as_dict()
        assert result.git.get("ok") is True, result.as_dict()
        assert result.sqlite.get("ok") is True, result.as_dict()
        assert result.guide.get("ok") is True, result.as_dict()
        assert not result.guide.get("skipped"), result.as_dict()
        assert result.guide.get("ingestIndex"), result.as_dict()

        shown = store.show(lesson_id)
        assert shown is not None
        assert MARKER in (shown.get("body") or "")

        assert LocalIndex(Project(fixture)).lessons_for_work(wid)

        parity = store.parity(repair=False)
        sqlite_block = parity.get("sqlite") or {}
        assert sqlite_block.get("enabled") is True, parity
        assert sqlite_block.get("ok") is True, parity
        assert lesson_id not in (sqlite_block.get("missing") or []), parity

        guide_block = parity.get("guide") or {}
        subgraph = GuideClient(base).work_subgraph(wid)
        graph_evidence = {"guide": guide_block, "subgraph": subgraph}
        assert guide_block.get("enabled") is True, parity
        assert guide_block.get("via") == "work_subgraph", graph_evidence
        assert not guide_block.get("skipped"), graph_evidence
        assert not guide_block.get("unreachable"), graph_evidence
        assert guide_block.get("ok") is True, graph_evidence
        assert lesson_id not in (guide_block.get("missing") or []), graph_evidence
        assert lesson_id in store.guide_lesson_ids(), graph_evidence
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_live_context_selects_right_records() -> None:
    """Two works, three areas: work subgraph vs area lessons must not mix.

    Skip/unreachable is not a pass. Extra records from other live tests in
    the same Neo4j may exist; this fixture's sibling ids must still be absent
    from the wrong context.
    """
    base = resolve_guide_base_url()
    client = GuideClient(base, timeout=3.0)
    if not client.health_ok():
        pytest.fail(
            f"Guide not running at {base} — run SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh"
        )

    records = load_records()
    repo_root = Path(__file__).resolve().parents[2]
    fixture = repo_root / ".sdlc" / "test-fixtures" / f"live-ctx-{uuid.uuid4().hex[:8]}"
    try:
        fixture.mkdir(parents=True, exist_ok=True)
        seed_canvases(fixture, records)
        save_config(
            fixture,
            {
                "backends": ["git-pointers", "sqlite", "guide-dice"],
                "guide_base_url": base,
            },
        )
        store = ContextStore(Project(fixture), guide_base_url=base)
        keys = persist_records(store, records, project_guide=True)

        alpha = "FEAT-910-ctx-alpha"
        beta = "FEAT-911-ctx-beta"
        alpha_ids = ids_matching(records, work_id=alpha)
        beta_ids = ids_matching(records, work_id=beta)
        engine_ids = ids_matching(records, area="ctx-engine")

        self_ledger_alpha = retrieved_ids(store, work_id=alpha)
        assert self_ledger_alpha == alpha_ids, self_ledger_alpha
        assert retrieved_ids(store, area="ctx-engine") == engine_ids
        assert retrieved_ids(store, work_id=alpha, kind="pitfall") == {
            keys["alpha_engine_pitfall"]
        }
        assert retrieved_ids(store, work_id=alpha, query="Vue") == {
            keys["alpha_console_decision"]
        }
        assert retrieved_ids(store, work_id=alpha, query="by-label") == set()

        sqlite_work = {
            row["id"]
            for row in LocalIndex(Project(fixture)).lessons_for_work(alpha)
            if not row["staged"]
        }
        sqlite_area = {
            row["id"]
            for row in LocalIndex(Project(fixture)).lessons_for_area("ctx-engine")
            if not row["staged"]
        }
        assert sqlite_work == alpha_ids
        assert sqlite_area == engine_ids

        sg_alpha = client.work_subgraph(alpha)
        sg_beta = client.work_subgraph(beta)
        assert sg_alpha.get("ok") is True, sg_alpha
        assert sg_beta.get("ok") is True, sg_beta
        alpha_data = sg_alpha.get("data") or {}
        beta_data = sg_beta.get("data") or {}
        alpha_graph = lesson_ids_from_subgraph(alpha_data)
        beta_graph = lesson_ids_from_subgraph(beta_data)
        evidence = {"alpha": sg_alpha, "beta": sg_beta}

        assert alpha_ids <= alpha_graph, evidence
        assert beta_ids.isdisjoint(alpha_graph), evidence
        assert beta_ids <= beta_graph, evidence
        assert alpha_ids.isdisjoint(beta_graph), evidence
        assert subgraph_kind_ids(alpha_data, "pitfall") == {
            keys["alpha_engine_pitfall"]
        }, evidence
        assert subgraph_kind_ids(alpha_data, "decision") == {
            keys["alpha_console_decision"]
        }, evidence
        assert keys["alpha_engine_pitfall"] not in subgraph_kind_ids(
            alpha_data, "decision"
        )

        area = client.area_lessons("ctx-engine")
        assert area.get("ok") is True, area
        area_ids = lesson_ids_from_subgraph(area.get("data") or {})
        area_evidence = {"area": area, "engine_ids": sorted(engine_ids)}
        assert engine_ids <= area_ids, area_evidence
        assert keys["alpha_console_decision"] not in area_ids, area_evidence
        assert keys["beta_docs_pattern"] not in area_ids, area_evidence
        assert record_id(records[0]) in area_ids
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
