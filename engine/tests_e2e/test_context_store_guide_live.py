"""Live triple-backend persist (git + sqlite + Guide). Requires Guide stack up."""

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
        save_config(fixture, {"backends": ["git-pointers", "sqlite", "guide-dice"]})
        store = ContextStore(Project(fixture))
        result = store.persist_lesson(
            kind="pitfall",
            work_id=wid,
            area="engine",
            body="LIVE-TRIPLE-PERSIST",
            source="live-test",
            accept=True,
            project_guide=True,
        )
        assert result.ok is True
        assert LocalIndex(Project(fixture)).lessons_for_work(wid)
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
