"""Guide parity uses work_subgraph retrieve, not by-label skip."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from sdlc_engine.context_store import ContextStore, lesson_ids_from_subgraph
from sdlc_engine.persistence import save_config
from sdlc_engine.project import Project


def _seed(root: Path, work_id: str) -> None:
    req = root / "requirements" / "milestones" / f"{work_id}.md"
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text(f"# Requirement {work_id}\n", encoding="utf-8")
    canvas = root / "spdd" / "canvas" / f"{work_id}.md"
    canvas.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_text(
        f"# REASONS Canvas: {work_id}\n\n## Metadata\n\n- Work ID: {work_id}\n",
        encoding="utf-8",
    )
    (root / "spdd" / "memory").mkdir(parents=True, exist_ok=True)


def test_lesson_ids_from_subgraph_collects_record_ids() -> None:
    data = {
        "pitfalls": [{"id": "pitfall:W:engine:t", "body": "x"}],
        "decisions": [{"entityId": "decision:W:engine:t"}],
        "patterns": ["pattern:W:engine:t"],
    }
    assert lesson_ids_from_subgraph(data) == {
        "pitfall:W:engine:t",
        "decision:W:engine:t",
        "pattern:W:engine:t",
    }


def test_parity_skips_guide_only_when_unhealthy(tmp_path: Path) -> None:
    wid = "FEAT-904-guide-down"
    _seed(tmp_path, wid)
    save_config(tmp_path, {"backends": ["git-pointers", "guide-dice"]})
    store = ContextStore(Project(tmp_path), guide_base_url="http://127.0.0.1:9")
    store.persist_lesson(
        kind="pitfall",
        work_id=wid,
        area="engine",
        body="x",
        source="unit",
        accept=True,
        project_guide=False,
    )
    with patch.object(store, "_guide_client") as mock_client:
        mock_client.return_value.health_ok.return_value = False
        parity = store.parity(repair=False)
    guide = parity["guide"]
    assert guide["enabled"] is True
    assert guide["skipped"] is True
    assert guide["unreachable"] is True
    assert "missing" not in guide


def test_parity_reads_guide_via_work_subgraph(tmp_path: Path) -> None:
    wid = "FEAT-905-guide-up"
    _seed(tmp_path, wid)
    save_config(tmp_path, {"backends": ["git-pointers", "guide-dice"]})
    store = ContextStore(Project(tmp_path), guide_base_url="http://guide.test")
    result = store.persist_lesson(
        kind="pitfall",
        work_id=wid,
        area="engine",
        body="GRAPH-ID",
        source="unit",
        accept=True,
        project_guide=False,
    )
    lesson_id = result.git["id"]
    client = MagicMock()
    client.health_ok.return_value = True
    client.work_subgraph.return_value = {
        "ok": True,
        "data": {"pitfalls": [{"id": lesson_id, "body": "GRAPH-ID"}]},
    }
    with patch.object(store, "_guide_client", return_value=client):
        parity = store.parity(repair=False)
    guide = parity["guide"]
    assert guide["via"] == "work_subgraph"
    assert guide.get("skipped") is None
    assert guide.get("unreachable") is None
    assert guide["ok"] is True
    assert guide["missing"] == []
    client.work_subgraph.assert_called_with(wid)


def test_parity_fails_when_live_guide_missing_id(tmp_path: Path) -> None:
    wid = "FEAT-906-guide-miss"
    _seed(tmp_path, wid)
    save_config(tmp_path, {"backends": ["git-pointers", "guide-dice"]})
    store = ContextStore(Project(tmp_path), guide_base_url="http://guide.test")
    result = store.persist_lesson(
        kind="pitfall",
        work_id=wid,
        area="engine",
        body="missing-from-graph",
        source="unit",
        accept=True,
        project_guide=False,
    )
    lesson_id = result.git["id"]
    client = MagicMock()
    client.health_ok.return_value = True
    client.work_subgraph.return_value = {"ok": True, "data": {"pitfalls": []}}
    with patch.object(store, "_guide_client", return_value=client):
        parity = store.parity(repair=False)
    guide = parity["guide"]
    assert guide["ok"] is False
    assert not guide.get("skipped")
    assert lesson_id in guide["missing"]
    assert parity["ok"] is False


def test_parity_fails_not_skip_when_live_subgraph_errors(tmp_path: Path) -> None:
    wid = "FEAT-907-guide-err"
    _seed(tmp_path, wid)
    save_config(tmp_path, {"backends": ["git-pointers", "guide-dice"]})
    store = ContextStore(Project(tmp_path), guide_base_url="http://guide.test")
    store.persist_lesson(
        kind="pitfall",
        work_id=wid,
        area="engine",
        body="x",
        source="unit",
        accept=True,
        project_guide=False,
    )
    client = MagicMock()
    client.health_ok.return_value = True
    client.work_subgraph.return_value = {
        "ok": False,
        "status": 500,
        "error": "boom",
    }
    with patch.object(store, "_guide_client", return_value=client):
        parity = store.parity(repair=False)
    guide = parity["guide"]
    assert guide["ok"] is False
    assert not guide.get("skipped")
    assert not guide.get("unreachable")
    assert "work_subgraph" in (guide.get("error") or "")
    assert parity["ok"] is False
