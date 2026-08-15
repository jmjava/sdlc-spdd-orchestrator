"""Unit coverage for the Vue ops console playground seed."""

from __future__ import annotations

from pathlib import Path

import pytest

from sdlc_engine.cli_parser import build_parser
from sdlc_engine.installer.playground import (
    WORKS,
    is_playground,
    materialize_playground,
)


def test_materialize_playground_writes_tabs_data(tmp_path: Path) -> None:
    dest = materialize_playground(tmp_path / "play", orch=tmp_path)
    assert is_playground(dest)
    active = WORKS[0][0]
    assert (dest / ".sdlc" / "pointer").read_text(encoding="utf-8").strip() == active
    assert (dest / "spdd" / "canvas" / f"{active}.md").is_file()
    assert (dest / "requirements" / "milestones" / f"{active}.md").is_file()
    assert (dest / "adf" / f"{active}.adf.json").is_file()
    assert (dest / "spdd" / "memory" / "lessons.jsonl").read_text(encoding="utf-8").count("\n") == 3
    assert (dest / "spdd" / "memory" / "registry.jsonl").is_file()
    assert (dest / ".sdlc" / "staged" / "lessons.jsonl").is_file()
    assert (dest / "PLAYGROUND.md").is_file()
    backups = list((dest / ".sdlc-spdd-upgrade-backups").iterdir())
    assert backups
    assert (dest / ".sdlc" / "persistence-config.json").is_file()
    assert (dest / ".sdlc" / "integrations-config.json").is_file()


def test_materialize_playground_refresh_replaces(tmp_path: Path) -> None:
    dest = materialize_playground(tmp_path / "play")
    junk = dest / "junk.txt"
    junk.write_text("nope", encoding="utf-8")
    materialize_playground(dest, refresh=True)
    assert not junk.exists()
    assert is_playground(dest)


def test_console_parser_playground_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["console", "--playground", "--playground-dir", "/tmp/p", "--no-browser"])
    assert args.playground is True
    assert args.playground_dir == "/tmp/p"
    assert args.no_browser is True


def test_health_reports_playground(tmp_path: Path) -> None:
    pytest.importorskip("flask")
    from sdlc_engine.installer.app import create_app

    dest = materialize_playground(tmp_path / "play")
    app = create_app(dest, vue_dist=False)
    body = app.test_client().get("/api/health").get_json()
    assert body["ok"] is True
    assert body["playground"] is True
    assert body["default_target"] == str(dest)
