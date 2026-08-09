"""Live Guide projection round-trip: ledger → Guide → read back (+ MCP parity).

Requires Guide + Neo4j. Run via ``./tests/test-guide-stack-live.sh`` or ``./scripts/run-test-suites.sh e2e --guide``.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path

import pytest

from sdlc_engine.context_store import ContextStore
from sdlc_engine.guide_client import GuideClient, resolve_guide_base_url
from sdlc_engine.persistence import save_config
from sdlc_engine.project import Project

MARKER = "GUIDE-ROUNDTRIP-MARKER"
WORK_PREFIX = "FEAT-RT-GUIDE"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _require_guide() -> GuideClient:
    base = resolve_guide_base_url()
    client = GuideClient(base, timeout=3.0)
    if not client.health_ok():
        pytest.fail(
            f"Guide not reachable at {base} — run SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh"
        )
    return client


@pytest.fixture()
def seeded_project() -> tuple[Path, str, str, str]:
    """Seed under repo .sdlc/test-fixtures (Guide allowed-roots rejects /tmp)."""
    root = _repo_root() / ".sdlc" / "test-fixtures" / f"guide-rt-{uuid.uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=True)
    work_id = f"{WORK_PREFIX}-{uuid.uuid4().hex[:8]}"
    area = "engine-tests"
    body = f"{MARKER}-{uuid.uuid4().hex[:8]}"
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(f"# Requirement: {work_id}\n\n## Summary\nRoundtrip seed.\n", encoding="utf-8")
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"""# REASONS Canvas: {work_id}

## Metadata

- Work ID: {work_id}
- Work Type: Feature
- Status: In Progress

## Requirements

Roundtrip canvas body for Guide projection.
""",
        encoding="utf-8",
    )
    (root / "spdd" / "memory").mkdir(parents=True, exist_ok=True)
    save_config(
        root,
        {
            "backends": ["git-pointers", "sqlite", "guide-dice"],
            "guide_base_url": resolve_guide_base_url(),
        },
    )
    store = ContextStore(Project(root))
    store.persist_lesson(
        kind="pitfall",
        work_id=work_id,
        area=area,
        body=body,
        source="roundtrip-test",
        accept=True,
        project_guide=False,
    )
    lesson_id = f"pitfall:{work_id}:{area}:roundtrip-test"
    index_path = root / "spdd" / "memory" / "context-index.md"
    if not index_path.is_file():
        index_path.write_text(
            "# Context Index\n\n"
            "| Area | Kind | Work ID | Phase | Timestamp | Source | Entry |\n"
            "|------|------|---------|-------|-----------|--------|-------|\n",
            encoding="utf-8",
        )
    with index_path.open("a", encoding="utf-8") as fh:
        fh.write(
            f"| {area} | pitfall | {work_id} | test | 2026-08-08T00:00:00Z | roundtrip-test | {body} |\n"
        )
    yield root, work_id, lesson_id, body
    shutil.rmtree(root, ignore_errors=True)


def test_guide_load_read_subgraph_and_lesson(seeded_project) -> None:
    _require_guide()
    root, work_id, lesson_id, body = seeded_project
    client = GuideClient(resolve_guide_base_url())

    loaded = client.project_load(str(root))
    assert loaded["ok"] is True, loaded

    subgraph = client.work_subgraph(work_id)
    assert subgraph["ok"] is True, subgraph
    data = subgraph["data"]
    assert data.get("found") is True or data.get("work") or data.get("canvases")

    pitfalls = data.get("pitfalls") or []
    pitfall_text = json.dumps(pitfalls)
    assert body in pitfall_text or MARKER in pitfall_text, pitfall_text

    lesson = client.get_lesson(lesson_id)
    if lesson.get("ok"):
        lesson_body = (lesson["data"].get("body") or "").strip()
        assert body in lesson_body or MARKER in lesson_body
    else:
        assert lesson.get("status") == 403

    mcp = client.call_mcp_tool("spdd_workSubgraph", {"workId": work_id})
    assert mcp["ok"] is True, mcp
    assert mcp["tool"] == "spdd_workSubgraph"


def test_guide_parity_ledger_ids_in_graph(seeded_project) -> None:
    _require_guide()
    root, work_id, lesson_id, _body = seeded_project
    client = GuideClient(resolve_guide_base_url())
    assert client.project_load(str(root))["ok"] is True

    store = ContextStore(Project(root))
    parity = store.parity(repair=False)
    assert parity.get("guide", {}).get("enabled") is True
    guide_block = parity.get("guide") or {}
    if guide_block.get("ok") is False and guide_block.get("error"):
        sg = client.work_subgraph(work_id)
        assert sg["ok"] is True, sg
        pitfall_ids = [
            p.get("id") or p.get("entityId") or ""
            for p in (sg.get("data") or {}).get("pitfalls") or []
        ]
        assert lesson_id in pitfall_ids, pitfall_ids
    else:
        missing = guide_block.get("missing") or []
        assert lesson_id not in missing, json.dumps(parity, indent=2)
        assert parity.get("ok") is True, json.dumps(parity, indent=2)


def test_cli_guide_query_work_subgraph(seeded_project, capsys) -> None:
    _require_guide()
    from sdlc_engine.cli import main

    root, work_id, _lesson_id, _body = seeded_project
    client = GuideClient(resolve_guide_base_url())
    assert client.project_load(str(root))["ok"] is True

    os.environ["GUIDE_BASE_URL"] = resolve_guide_base_url()
    rc = main(
        [
            "--root",
            str(root),
            "context",
            "guide-query",
            "--work-id",
            work_id,
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0, out
    payload = json.loads(out)
    assert payload.get("ok") is True
    assert payload.get("resolved_tool") == "spdd_workSubgraph"
