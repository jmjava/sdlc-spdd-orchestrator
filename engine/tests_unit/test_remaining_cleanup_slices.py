"""Proof tests for #85 sessions, #86 mirrors, #91 quiet (storage v3 only)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from sdlc_engine.cli import main
from sdlc_engine.context_store import ContextStore
from sdlc_engine.project import Project
from sdlc_engine.quiet import is_quiet, quiet_resume_blurb


def _seed_stay_set(root: Path, work_id: str) -> None:
    (root / "sdlc-spdd" / "requirements" / "milestones").mkdir(parents=True, exist_ok=True)
    (root / "sdlc-spdd" / "requirements" / "milestones" / f"{work_id}.md").write_text(
        f"# {work_id}\n", encoding="utf-8"
    )
    (root / "sdlc-spdd" / "spdd" / "canvas").mkdir(parents=True, exist_ok=True)
    (root / "sdlc-spdd" / "spdd" / "canvas" / f"{work_id}.md").write_text(
        f"# REASONS\n\n## Metadata\n\n- Work ID: {work_id}\n",
        encoding="utf-8",
    )
    (root / "sdlc-spdd" / "harness" / "skills").mkdir(parents=True, exist_ok=True)


def test_quiet_mode_env_and_harness(tmp_path: Path, monkeypatch) -> None:
    project = Project(tmp_path)
    monkeypatch.delenv("SDLC_QUIET", raising=False)
    assert is_quiet(project) is False
    monkeypatch.setenv("SDLC_QUIET", "1")
    assert is_quiet(project) is True
    monkeypatch.delenv("SDLC_QUIET", raising=False)
    harness = project.harness_dir / "quiet-mode.md"
    harness.parent.mkdir(parents=True, exist_ok=True)
    harness.write_text("# quiet\n", encoding="utf-8")
    assert is_quiet(project) is True
    assert is_quiet(project, quiet_flag=True) is True
    assert "Quiet" in quiet_resume_blurb()


def test_hot_session_paths_prefer_sdlc(tmp_path: Path) -> None:
    project = Project(tmp_path)
    hot = project.hot_session_dir()
    assert hot == tmp_path / "sdlc-spdd" / ".sdlc" / "sessions"
    project.ensure_runtime_dirs()
    assert hot.is_dir()
    assert project.current_session_path() == hot / "current-session.md"
    (hot / "current-session.md").write_text("hot\n", encoding="utf-8")
    assert project.current_session_path().read_text(encoding="utf-8") == "hot\n"


def test_persist_entry_does_not_write_feature_mirrors(tmp_path: Path) -> None:
    wid = "FEAT-930-no-mirror"
    _seed_stay_set(tmp_path, wid)
    store = ContextStore(Project(tmp_path), guide_base_url="http://127.0.0.1:9")
    result = store.persist_lesson(
        kind="decision",
        work_id=wid,
        body="Lean progress only",
        area="scripts/lib",
        project_guide=False,
    )
    assert result.git.get("ok") is True
    staged = tmp_path / "sdlc-spdd" / ".sdlc" / "staged" / "lessons.jsonl"
    assert staged.is_file()
    assert "Lean progress only" in staged.read_text(encoding="utf-8")
    # Only the staged ledger receives the record; no committed mirror is written.
    assert not (tmp_path / "sdlc-spdd" / "spdd" / "memory" / "lessons.jsonl").exists()
    progress = tmp_path / "sdlc-spdd" / "spdd" / "memory" / "entries" / "progress.md"
    assert not progress.exists() or "Lean progress only" not in progress.read_text(encoding="utf-8")


def test_cli_quiet_status_is_top_level(tmp_path: Path, monkeypatch, capsys) -> None:
    wid = "FEAT-932-cli"
    _seed_stay_set(tmp_path, wid)
    monkeypatch.setenv("SDLC_QUIET", "1")
    rc = main(["--root", str(tmp_path), "quiet-status"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["quiet"] is True
    assert out["hot_session_dir"].endswith(str(Path(".sdlc") / "sessions"))


def test_cli_legacy_migration_verbs_are_gone(tmp_path: Path, capsys) -> None:
    for argv in (["storage", "status"], ["storage", "migrate"], ["agent-context", "detect"]):
        with pytest.raises(SystemExit) as exc:
            main(["--root", str(tmp_path), *argv])
        assert exc.value.code == 2
        capsys.readouterr()


def test_start_agent_session_writes_hot_path_and_honors_quiet(tmp_path: Path) -> None:
    wid = "FEAT-933-session-script"
    _seed_stay_set(tmp_path, wid)
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
    hot = tmp_path / "sdlc-spdd" / ".sdlc" / "sessions" / "current-session.md"
    assert hot.is_file()
    text = hot.read_text(encoding="utf-8")
    assert "Quiet/product-test mode" in text or "Quiet mode" in text
    assert "operation <T##>" not in text
