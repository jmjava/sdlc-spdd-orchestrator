"""Live triple-backend persist (git + sqlite + Guide/Neo4j). Requires Guide stack up.

C-RETRIEVE graph proof: persist one pitfall, then require the same record id
from the ledger, SQLite, and live Guide via ``context parity`` (work_subgraph).
Skip/unreachable is not a pass.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from sdlc_engine.context_store import ContextStore
from sdlc_engine.db import LocalIndex
from sdlc_engine.guide_client import GuideClient, resolve_guide_base_url
from sdlc_engine.persistence import save_config
from sdlc_engine.project import Project

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
        assert guide_block.get("enabled") is True, parity
        assert guide_block.get("via") == "work_subgraph", guide_block
        assert not guide_block.get("skipped"), guide_block
        assert not guide_block.get("unreachable"), guide_block
        assert guide_block.get("ok") is True, guide_block
        assert lesson_id not in (guide_block.get("missing") or []), guide_block
        assert lesson_id in store.guide_lesson_ids(), guide_block
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
