"""Proof tests for #80 upgrade, #85 sessions, #86 mirrors, #91 quiet."""

from __future__ import annotations

import json
import os
from pathlib import Path

from sdlc_engine.agent_context_upgrade import AgentContextUpgrade
from sdlc_engine.cli import main
from sdlc_engine.context_store import ContextStore
from sdlc_engine.project import Project
from sdlc_engine.quiet import is_quiet, quiet_resume_blurb


def _seed_noise(root: Path, work_id: str) -> None:
    (root / "requirements" / "milestones").mkdir(parents=True, exist_ok=True)
    (root / "requirements" / "milestones" / f"{work_id}.md").write_text(
        f"# {work_id}\n", encoding="utf-8"
    )
    (root / "spdd" / "canvas").mkdir(parents=True, exist_ok=True)
    (root / "spdd" / "canvas" / f"{work_id}.md").write_text(
        f"# REASONS\n\n## Metadata\n\n- Work ID: {work_id}\n",
        encoding="utf-8",
    )
    feat = root / "agent-context" / "features" / work_id
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "progress-log.md").write_text("# progress mirror\n", encoding="utf-8")
    (feat / "reasons-canvas.md").write_text("# canvas mirror\n", encoding="utf-8")
    sess = root / "agent-context" / "sessions"
    sess.mkdir(parents=True, exist_ok=True)
    (sess / "current-session.md").write_text("# legacy session\n", encoding="utf-8")
    mem = root / "agent-context" / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "context-index.md").write_text(
        """# Context Index

| Area | Kind | Work ID | Phase | Timestamp | Source | Entry |
|------|------|---------|-------|-----------|--------|-------|
| scripts/lib | decision | W | sync | 2026-08-07T00:00:00Z | t | keep |
""",
        encoding="utf-8",
    )
    (root / "agent-context" / "harness").mkdir(parents=True, exist_ok=True)
    (root / "agent-context" / "harness" / "skills").mkdir(parents=True, exist_ok=True)


def test_quiet_mode_env_and_harness(tmp_path: Path, monkeypatch) -> None:
    project = Project(tmp_path)
    monkeypatch.delenv("SDLC_QUIET", raising=False)
    assert is_quiet(project) is False
    monkeypatch.setenv("SDLC_QUIET", "1")
    assert is_quiet(project) is True
    monkeypatch.delenv("SDLC_QUIET", raising=False)
    harness = tmp_path / "agent-context" / "harness" / "quiet-mode.md"
    harness.parent.mkdir(parents=True, exist_ok=True)
    harness.write_text("# quiet\n", encoding="utf-8")
    assert is_quiet(project) is True
    assert is_quiet(project, quiet_flag=True) is True
    assert "Quiet" in quiet_resume_blurb()


def test_hot_session_paths_prefer_sdlc(tmp_path: Path) -> None:
    project = Project(tmp_path)
    hot = project.hot_session_dir()
    assert hot == tmp_path / ".sdlc" / "sessions"
    project.ensure_runtime_dirs()
    assert hot.is_dir()
    assert project.current_session_path() == hot / "current-session.md"
    (hot / "current-session.md").write_text("hot\n", encoding="utf-8")
    assert project.current_session_path().read_text(encoding="utf-8") == "hot\n"


def test_persist_entry_does_not_write_feature_mirrors(tmp_path: Path) -> None:
    wid = "FEAT-930-no-mirror"
    _seed_noise(tmp_path, wid)
    store = ContextStore(Project(tmp_path), guide_base_url="http://127.0.0.1:9")
    result = store.persist_lesson(
        kind="decision",
        work_id=wid,
        body="Lean progress only",
        area="scripts/lib",
        project_guide=False,
    )
    assert result.git.get("ok") is True
    staged = tmp_path / ".sdlc" / "staged" / "lessons.jsonl"
    assert staged.is_file()
    assert "Lean progress only" in staged.read_text(encoding="utf-8")
    mirror = tmp_path / "agent-context" / "features" / wid / "progress-log.md"
    assert "Lean progress only" not in mirror.read_text(encoding="utf-8")


def test_upgrade_archives_sessions_and_features(tmp_path: Path) -> None:
    wid = "FEAT-931-upgrade"
    _seed_noise(tmp_path, wid)
    up = AgentContextUpgrade(Project(tmp_path))
    detect = up.detect()
    assert detect["needs_upgrade"] is True
    assert "agent-context/features" in detect["noise"]
    assert "agent-context/sessions" in detect["noise"]

    dry = up.run(dry_run=True)
    assert dry.ok
    assert dry.dry_run
    assert (tmp_path / "agent-context" / "features").is_dir()

    result = up.run(dry_run=False, rebuild_db=False)
    assert result.ok
    assert not (tmp_path / "agent-context" / "features").exists()
    assert not (tmp_path / "agent-context" / "sessions").exists()
    assert (tmp_path / ".sdlc" / "sessions").is_dir()
    export = Path(result.export_dir)
    assert export.is_dir()
    assert (export / "agent-context" / "memory" / "context-index.md").is_file()
    # Stay-set still present
    assert (tmp_path / "spdd" / "canvas" / f"{wid}.md").is_file()
    assert (tmp_path / "requirements" / "milestones" / f"{wid}.md").is_file()


def test_cli_agent_context_upgrade_and_quiet(tmp_path: Path, monkeypatch, capsys) -> None:
    wid = "FEAT-932-cli"
    _seed_noise(tmp_path, wid)
    monkeypatch.setenv("SDLC_QUIET", "1")
    rc = main(["--root", str(tmp_path), "agent-context", "quiet-status"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["quiet"] is True

    rc = main(["--root", str(tmp_path), "agent-context", "detect"])
    assert rc == 0
    detect = json.loads(capsys.readouterr().out)
    assert detect["needs_upgrade"] is True

    rc = main(["--root", str(tmp_path), "agent-context", "upgrade"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["moved"]


def test_start_agent_session_writes_hot_path_and_honors_quiet(tmp_path: Path) -> None:
    wid = "FEAT-933-session-script"
    _seed_noise(tmp_path, wid)
    script = Path(__file__).resolve().parents[2] / "scripts" / "start-agent-session.sh"
    assert script.is_file()
    env = os.environ.copy()
    env["SDLC_QUIET"] = "1"
    import subprocess

    proc = subprocess.run(
        [
            "bash",
            str(script),
            "--target",
            str(tmp_path),
            "--work-id",
            wid,
            "--phase",
            "code",
            "--quiet",
        ],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    hot = tmp_path / ".sdlc" / "sessions" / "current-session.md"
    assert hot.is_file()
    text = hot.read_text(encoding="utf-8")
    assert "Quiet/product-test mode" in text or "Quiet mode" in text
    assert "operation <T##>" not in text
    # Must not write new current-session under legacy path
    legacy_current = tmp_path / "agent-context" / "sessions" / "current-session.md"
    # legacy may still exist from seed, but must not be replaced with new quiet brief
    assert "Quiet/product-test mode" not in legacy_current.read_text(encoding="utf-8")
