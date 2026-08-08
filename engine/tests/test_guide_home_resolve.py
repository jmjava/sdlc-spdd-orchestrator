"""Guide home resolution for dual-repo Cloud Agent layouts."""

from __future__ import annotations

from pathlib import Path

from sdlc_engine.installer import guide as guide_mod
from sdlc_engine.installer import guide_runtime as gr
from sdlc_engine.installer.guide import resolve_guide_home
from sdlc_engine.installer.runner import orchestrator_root


def _seed_guide(path: Path) -> Path:
    (path / "scripts").mkdir(parents=True)
    (path / "scripts" / "append-ingest.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    (path / "compose.yaml").write_text("services: {}\n", encoding="utf-8")
    return path


def test_looks_like_guide_home(tmp_path: Path) -> None:
    assert guide_mod._looks_like_guide_home(tmp_path) is False
    seeded = _seed_guide(tmp_path / "guide")
    assert guide_mod._looks_like_guide_home(seeded) is True


def test_resolve_guide_home_prefers_env(tmp_path: Path, monkeypatch) -> None:
    home = _seed_guide(tmp_path / "env-guide")
    monkeypatch.setenv("GUIDE_HOME", str(home))
    assert resolve_guide_home() == home.resolve()


def test_resolve_guide_home_ignores_env_that_is_not_guide(tmp_path: Path, monkeypatch) -> None:
    bare = tmp_path / "not-guide"
    bare.mkdir()
    monkeypatch.setenv("GUIDE_HOME", str(bare))
    # Force discovery misses so invalid GUIDE_HOME cannot win via sibling/agent paths.
    monkeypatch.setattr(guide_mod, "_looks_like_guide_home", lambda _p: False)
    resolved = resolve_guide_home()
    assert resolved != bare.resolve()
    assert resolved == Path.home() / "github" / "jmjava" / "guide"


def test_default_config_points_at_dual_repo_sibling_when_present(monkeypatch) -> None:
    """Cursor dual-repo env: /agent/repos/guide beside sdlc-spdd-orchestrator."""
    monkeypatch.delenv("GUIDE_HOME", raising=False)
    sibling = orchestrator_root().parent / "guide"
    if not guide_mod._looks_like_guide_home(sibling):
        return
    cfg = guide_mod.default_config()
    assert Path(cfg["guide_home"]).resolve() == sibling.resolve()


def test_start_neo4j_is_idempotent_when_bolt_already_open(monkeypatch) -> None:
    monkeypatch.setattr(gr, "_tcp_open", lambda *a, **k: True)
    result = gr.start_neo4j(
        {
            "guide_home": "/missing",
            "neo4j_bolt_port": 7687,
            "neo4j_http_port": 7474,
        }
    )
    assert result["ok"] is True
    assert result["action"] == "already_running"
    assert result["bolt_ready"] is True
