"""Project.home is strict storage v3: SDLC_HOME or <root>/sdlc-spdd, never root."""

from __future__ import annotations

from pathlib import Path

from sdlc_engine.project import Project


def test_home_is_root_slash_sdlc_spdd_without_probing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SDLC_HOME", raising=False)
    project = Project(tmp_path)
    assert project.home == tmp_path / "sdlc-spdd"
    assert not project.home.exists()
    assert project.sdlc_dir == tmp_path / "sdlc-spdd" / ".sdlc"
    assert project.harness_dir == tmp_path / "sdlc-spdd" / "harness"
    assert project.ledger_path == tmp_path / "sdlc-spdd" / "spdd" / "memory" / "lessons.jsonl"
    assert project.registry_path == tmp_path / "sdlc-spdd" / "spdd" / "memory" / "registry.jsonl"
    assert project.roadmap_path == tmp_path / "sdlc-spdd" / "ROADMAP.md"


def test_home_ignores_pre_v3_root_layout(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SDLC_HOME", raising=False)
    (tmp_path / "spdd" / "canvas").mkdir(parents=True)
    (tmp_path / "requirements").mkdir()
    (tmp_path / "agent-context" / "harness").mkdir(parents=True)
    project = Project(tmp_path)
    assert project.home == tmp_path / "sdlc-spdd"
    assert project.harness_dir == tmp_path / "sdlc-spdd" / "harness"
    assert not hasattr(project, "is_single_folder")


def test_sdlc_home_env_overrides(tmp_path: Path, monkeypatch) -> None:
    elsewhere = tmp_path / "elsewhere"
    monkeypatch.setenv("SDLC_HOME", str(elsewhere))
    project = Project(tmp_path)
    assert project.home == elsewhere.resolve()
    assert project.root == tmp_path
