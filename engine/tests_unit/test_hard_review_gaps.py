"""Hard-review compliance tests for remaining cleanup gaps."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from sdlc_engine.agent_context_upgrade import AgentContextUpgrade
from sdlc_engine.cli import main
from sdlc_engine.context_store import ContextStore
from sdlc_engine.db import LocalIndex
from sdlc_engine.persistence import save_config
from sdlc_engine.project import Project
from sdlc_engine.registry import TeamRegistry


REPO = Path(__file__).resolve().parents[2]


def _seed_stay_set(root: Path, work_id: str, *, ready_for_coding: bool = False) -> None:
    (root / "requirements" / "milestones").mkdir(parents=True, exist_ok=True)
    (root / "requirements" / "milestones" / f"{work_id}.md").write_text(
        f"# Requirement: {work_id}\n\n## Summary\nHard review.\n",
        encoding="utf-8",
    )
    status = "Ready For Coding" if ready_for_coding else "In Progress"
    (root / "spdd" / "canvas").mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "canvas" / f"{work_id}.md").write_text(
        f"""# REASONS Canvas: {work_id}

## Metadata

- Work ID: {work_id}
- Work Type: Feature
- Status: {status}
""",
        encoding="utf-8",
    )


def _staged_records(root: Path) -> list[dict]:
    staged = root / ".sdlc" / "staged" / "lessons.jsonl"
    if not staged.is_file():
        return []
    return [
        json.loads(line)
        for line in staged.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_capture_stages_session_record_only(tmp_path: Path) -> None:
    wid = "FEAT-940-capture-lean"
    _seed_stay_set(tmp_path, wid)
    hot = tmp_path / ".sdlc" / "sessions"
    hot.mkdir(parents=True)
    (hot / "current-session.md").write_text(
        "# Hot brief\nTouching scripts/lib for capture.\n",
        encoding="utf-8",
    )
    script = REPO / "scripts" / "capture-session-memory.sh"
    proc = subprocess.run(
        [
            "bash",
            str(script),
            "--target",
            str(tmp_path),
            "--work-id",
            wid,
            "--phase",
            "sync",
            "--summary",
            "Captured from hot session under scripts/lib",
            "--areas",
            "scripts/lib",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    records = _staged_records(tmp_path)
    assert records, "capture should stage at least one JSONL record"
    sessions = [r for r in records if r["kind"] == "session" and r["work_id"] == wid]
    assert sessions
    assert sessions[-1]["area"] == "scripts/lib"
    # Committed ledger untouched; no legacy index/mirror trees created.
    assert not (tmp_path / "spdd" / "memory" / "lessons.jsonl").exists()
    assert not (tmp_path / "spdd" / "memory" / "context-index.md").exists()
    assert not (tmp_path / "spdd" / "memory" / "entries").exists()
    assert not (tmp_path / "agent-context" / "features").exists()


def test_create_feature_stages_record_no_mirrors(tmp_path: Path) -> None:
    script = REPO / "scripts" / "create-feature.sh"
    proc = subprocess.run(
        [
            "bash",
            str(script),
            "--target",
            str(tmp_path),
            "--type",
            "feature",
            "--name",
            "Hard Review Create",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    canvases = list((tmp_path / "spdd" / "canvas").glob("FEAT-*.md"))
    assert len(canvases) == 1
    wid = canvases[0].stem
    assert (tmp_path / "requirements" / "milestones" / f"{wid}.md").is_file()
    assert not (tmp_path / "agent-context" / "features").exists()
    assert not (tmp_path / "spdd" / "memory" / "entries").exists()
    records = _staged_records(tmp_path)
    assert any(r["kind"] == "session" and r["work_id"] == wid for r in records)


def test_upgrade_memory_only_exports_then_idempotent(tmp_path: Path) -> None:
    mem = tmp_path / "agent-context" / "memory"
    mem.mkdir(parents=True)
    (mem / "context-index.md").write_text(
        """# Context Index

| Area | Kind | Work ID | Phase | Timestamp | Source | Entry |
|------|------|---------|-------|-----------|--------|-------|
| engine | pitfall | FEAT-X | sync | 2026-08-08T00:00:00Z | t | export me |
""",
        encoding="utf-8",
    )
    up = AgentContextUpgrade(Project(tmp_path))
    first = up.run(dry_run=False, rebuild_db=False)
    assert first.ok
    assert first.moved
    assert (tmp_path / ".sdlc" / "storage-v3-migrated").is_file()
    second = up.run(dry_run=False, rebuild_db=False)
    assert second.ok
    assert any("delegated" in n.lower() or "idempotent" in n.lower() for n in second.notes)


def test_upgrade_archives_features_then_second_run_idempotent(tmp_path: Path) -> None:
    wid = "FEAT-941-up"
    feat = tmp_path / "agent-context" / "features" / wid
    feat.mkdir(parents=True)
    (feat / "progress-log.md").write_text("x\n", encoding="utf-8")
    sess = tmp_path / "agent-context" / "sessions"
    sess.mkdir(parents=True)
    (sess / "current-session.md").write_text("legacy\n", encoding="utf-8")
    up = AgentContextUpgrade(Project(tmp_path))
    a = up.run(dry_run=False, rebuild_db=False)
    assert a.ok
    assert a.moved
    assert not (tmp_path / "agent-context" / "features").exists()
    b = up.run(dry_run=False, rebuild_db=False)
    assert b.ok


def test_cli_context_retrieve_assembles_paths(tmp_path: Path, capsys) -> None:
    wid = "FEAT-942-retrieve"
    area = "scripts/lib"
    _seed_stay_set(tmp_path, wid)
    save_config(tmp_path, {"backends": ["git-pointers", "sqlite"]})
    store = ContextStore(Project(tmp_path), guide_base_url="http://127.0.0.1:9")
    store.persist_lesson(
        kind="decision",
        work_id=wid,
        area=area,
        body="Retrieve assemble proof",
        source="hard-review",
        accept=True,
        project_guide=False,
    )
    rc = main(
        [
            "--root",
            str(tmp_path),
            "context",
            "retrieve",
            "--work-id",
            wid,
            "--area",
            area,
        ]
    )
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["work_id"] == wid
    assert data["area"] == area
    assert data["ledger"]
    assert data["sqlite_graph"] is not None
    assert data["sqlite_graph"]["requirements"]
    assert data["sqlite_graph"]["canvases"]
    assert any(
        "Retrieve assemble" in (l.get("body") or "")
        for l in data["sqlite_graph"]["lessons"]
    )


def test_registry_lean_jsonl_and_sqlite_on_claim(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "hard-reviewer")
    wid = "FEAT-943-registry"
    _seed_stay_set(tmp_path, wid, ready_for_coding=True)
    save_config(tmp_path, {"backends": ["git-pointers", "sqlite"]})
    reg = TeamRegistry(Project(tmp_path))
    row = reg.claim(wid, phase="code", note="lean registry proof")
    assert row.status == "active"
    lean = tmp_path / "spdd" / "memory" / "registry.jsonl"
    assert lean.is_file()
    events = reg.lean_events(work_id=wid)
    assert len(events) >= 1
    assert events[-1]["event"] == "claim"
    assert events[-1]["owner"] == "hard-reviewer"
    claims = LocalIndex(Project(tmp_path)).query_sql(
        "SELECT work_id, owner, status FROM claims WHERE work_id = ?",
        (wid,),
    )
    assert claims
    assert claims[0]["owner"] == "hard-reviewer"
    assert claims[0]["status"] == "active"
