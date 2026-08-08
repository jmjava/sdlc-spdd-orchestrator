"""Hard-review compliance tests for remaining cleanup gaps."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from sdlc_engine.agent_context_upgrade import AgentContextUpgrade
from sdlc_engine.cli import main
from sdlc_engine.context_store import ContextStore
from sdlc_engine.db import LocalIndex
from sdlc_engine.pointers import PointerLedger
from sdlc_engine.project import Project
from sdlc_engine.registry import TeamRegistry


REPO = Path(__file__).resolve().parents[2]


def _seed_stay_set(root: Path, work_id: str) -> None:
    (root / "requirements" / "milestones").mkdir(parents=True, exist_ok=True)
    (root / "requirements" / "milestones" / f"{work_id}.md").write_text(
        f"# Requirement: {work_id}\n\n## Summary\nHard review.\n",
        encoding="utf-8",
    )
    (root / "spdd" / "canvas").mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "canvas" / f"{work_id}.md").write_text(
        f"""# REASONS Canvas: {work_id}

## Metadata

- Work ID: {work_id}
- Work Type: Feature
- Status: In Progress
""",
        encoding="utf-8",
    )


def test_capture_reads_hot_session_writes_lean_indexes(tmp_path: Path) -> None:
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
    lean_index = tmp_path / "spdd" / "memory" / "context-index.md"
    assert lean_index.is_file()
    assert "| scripts/lib | session |" in lean_index.read_text(encoding="utf-8")
    progress = tmp_path / "spdd" / "memory" / "entries" / "progress.md"
    assert progress.is_file()
    assert wid in progress.read_text(encoding="utf-8")
    lean_sessions = list((tmp_path / "spdd" / "memory" / "sessions").glob("*.md"))
    assert lean_sessions
    assert not (tmp_path / "agent-context" / "features").exists()


def test_create_feature_does_not_create_feature_mirrors(tmp_path: Path) -> None:
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
    assert (tmp_path / "spdd" / "memory" / "entries" / "progress.md").is_file()


def test_upgrade_memory_only_exports_then_idempotent(tmp_path: Path) -> None:
    mem = tmp_path / "agent-context" / "memory"
    mem.mkdir(parents=True)
    (mem / "context-index.md").write_text("# Context Index\n", encoding="utf-8")
    (mem / "project-memory.md").write_text("# Project Memory\n", encoding="utf-8")
    up = AgentContextUpgrade(Project(tmp_path))
    first = up.run(dry_run=False, rebuild_db=True)
    assert first.ok
    assert "agent-context/memory/context-index.md" in first.copied_memory
    assert (tmp_path / "agent-context" / "UPGRADED.md").is_file()
    export_mem = Path(first.export_dir) / "memory" / "context-index.md"
    assert export_mem.is_file()
    second = up.run(dry_run=False, rebuild_db=False)
    assert second.ok
    assert any("idempotent" in n.lower() for n in second.notes)
    assert not second.moved


def test_upgrade_archives_features_then_second_run_idempotent(tmp_path: Path) -> None:
    wid = "FEAT-941-up"
    feat = tmp_path / "agent-context" / "features" / wid
    feat.mkdir(parents=True)
    (feat / "progress-log.md").write_text("x\n", encoding="utf-8")
    sess = tmp_path / "agent-context" / "sessions"
    sess.mkdir(parents=True)
    (sess / "current-session.md").write_text("legacy\n", encoding="utf-8")
    up = AgentContextUpgrade(Project(tmp_path))
    a = up.run(dry_run=False, rebuild_db=True)
    assert a.ok
    assert a.moved
    assert not (tmp_path / "agent-context" / "features").exists()
    b = up.run(dry_run=False, rebuild_db=False)
    assert b.ok
    assert not b.moved
    assert any("idempotent" in n.lower() for n in b.notes)


def test_cli_context_retrieve_assembles_paths(tmp_path: Path, capsys) -> None:
    wid = "FEAT-942-retrieve"
    area = "scripts/lib"
    _seed_stay_set(tmp_path, wid)
    store = ContextStore(Project(tmp_path), guide_base_url="http://127.0.0.1:9")
    store.persist_lesson(
        kind="decision",
        work_id=wid,
        area=area,
        body="Retrieve assemble proof",
        source="hard-review",
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
    assert data["git_pointers"]
    assert data["sqlite_lessons"]
    assert data["sqlite_graph"] is not None
    assert data["sqlite_graph"]["requirements"]
    assert data["sqlite_graph"]["canvases"]
    assert any(l.get("body", "").startswith("Retrieve assemble") for l in data["sqlite_lessons"])


def test_registry_lean_jsonl_and_sqlite_on_claim(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDLC_USER", "hard-reviewer")
    wid = "FEAT-943-registry"
    _seed_stay_set(tmp_path, wid)
    reg = TeamRegistry(Project(tmp_path))
    row = reg.claim(wid, phase="code", note="lean registry proof")
    assert row.status == "active"
    lean = tmp_path / "spdd" / "memory" / "registry.jsonl"
    assert lean.is_file()
    events = reg.lean_events(work_id=wid)
    assert len(events) >= 1
    assert events[-1]["event"] == "claim"
    assert events[-1]["owner"] == "hard-reviewer"
    # Legacy TSV still updated for transition
    assert (tmp_path / "agent-context" / "work-registry.tsv").is_file()
    assert wid in (tmp_path / "agent-context" / "work-registry.tsv").read_text(
        encoding="utf-8"
    )
    # SQLite claim fan-out
    claims = LocalIndex(Project(tmp_path)).query_sql(
        "SELECT work_id, owner, status FROM claims WHERE work_id = ?",
        (wid,),
    )
    assert claims
    assert claims[0]["owner"] == "hard-reviewer"
    assert claims[0]["status"] == "active"
