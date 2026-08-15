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
from sdlc_engine.installer.playground_fakes import (
    FAKE_GH_TOKEN,
    FAKE_JIRA_TOKEN,
    fake_guide_action,
    fake_guide_payload,
    fake_issue_sync,
    issue_refs,
    load_runtime,
    seed_fake_guide_tree,
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
    integ = (dest / ".sdlc" / "integrations-config.json").read_text(encoding="utf-8")
    assert FAKE_JIRA_TOKEN in integ
    assert FAKE_GH_TOKEN in integ
    assert (dest / ".sdlc" / "fake-guide" / "compose.yaml").is_file()
    assert (dest / ".sdlc" / "fake-guide" / "scripts" / "append-ingest.sh").is_file()
    assert (dest / ".sdlc" / "playground-runtime.json").is_file()
    jira_key, gh_num = issue_refs(active)
    req = (dest / "requirements" / "milestones" / f"{active}.md").read_text(encoding="utf-8")
    assert jira_key in req
    assert gh_num in req


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


def test_fake_guide_start_stop_and_ingest(tmp_path: Path) -> None:
    dest = materialize_playground(tmp_path / "play")
    cfg = {"guide_home": str(dest / ".sdlc" / "fake-guide"), "host": "127.0.0.1", "port": 21337}
    payload = fake_guide_payload(dest, cfg, orch=tmp_path)
    assert payload["playground"] is True
    assert payload["probe"]["tcp_open"] is True
    assert payload["neo4j"]["bolt_open"] is True
    assert payload["guide_stats"]["data"]["contentElementCount"] == 42
    assert payload["projection"]["data"]["workIdCount"] == 3

    stopped = fake_guide_action(dest, cfg, "stop")
    assert stopped["ok"] is True
    assert load_runtime(dest)["guide_up"] is False
    down = fake_guide_payload(dest, cfg, orch=tmp_path)
    assert down["probe"]["tcp_open"] is False
    ingest_down = fake_guide_action(dest, cfg, "ingest")
    assert ingest_down["ok"] is False

    started = fake_guide_action(dest, cfg, "start", {"no_ingest": True})
    assert started["ok"] is True
    ingested = fake_guide_action(dest, cfg, "ingest")
    assert ingested["ok"] is True
    assert load_runtime(dest)["chunks"] == 49

    purged = fake_guide_action(dest, cfg, "purge_all_rag", {"confirm": True})
    assert purged["ok"] is True
    assert load_runtime(dest)["chunks"] == 0


def test_fake_issue_sync_dry_run_and_apply(tmp_path: Path) -> None:
    dest = materialize_playground(tmp_path / "play")
    work_id = WORKS[0][0]
    preview = fake_issue_sync(
        dest, work_id=work_id, system="jira", direction="pull", apply=False
    )
    assert preview["ok"] is True
    assert preview["playground"] is True
    assert "PLAY-930" in preview["report"]
    assert "--apply" not in preview["cli"]

    applied = fake_issue_sync(
        dest, work_id=work_id, system="github", direction="push", apply=True
    )
    assert applied["ok"] is True
    req = (dest / "requirements" / "milestones" / f"{work_id}.md").read_text(encoding="utf-8")
    assert "Playground github push" in req


def test_fake_guide_remaining_actions(tmp_path: Path) -> None:
    dest = materialize_playground(tmp_path / "play")
    cfg = {"guide_home": str(dest / ".sdlc" / "fake-guide"), "profile": "sdlc-spdd"}
    assert fake_guide_action(dest, cfg, "ensure")["ok"] is True
    assert fake_guide_action(dest, cfg, "neo4j_stop")["ok"] is True
    assert load_runtime(dest)["neo4j_up"] is False
    assert fake_guide_action(dest, cfg, "start", {"skip_neo4j": False})["ok"] is True
    assert load_runtime(dest)["neo4j_up"] is True
    assert fake_guide_action(dest, cfg, "ensure_profile", {"profile": "sdlc-spdd"})["ok"] is True
    loaded = fake_guide_action(dest, cfg, "projection_load")
    assert loaded["ok"] is True
    assert loaded["data"]["workIdCount"] == 3
    preview = fake_guide_action(dest, cfg, "purge_preview", {"uri_prefix": "file://"})
    assert preview["ok"] is True
    assert fake_guide_action(dest, cfg, "purge")["ok"] is True
    assert fake_guide_action(dest, cfg, "git_reset", {"directory": str(dest)})["ok"] is True
    assert fake_guide_action(dest, cfg, "not-a-thing")["ok"] is False


def test_fake_issue_sync_rejects_non_playground(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="playground"):
        fake_issue_sync(tmp_path, work_id="FEAT-1", system="jira", direction="pull", apply=False)


def test_seed_fake_guide_tree_is_idempotent(tmp_path: Path) -> None:
    dest = tmp_path / "play"
    dest.mkdir()
    first = seed_fake_guide_tree(dest)
    second = seed_fake_guide_tree(dest)
    assert first == second
    assert (first / "scripts" / "user-config" / "application-sdlc-spdd.yml").is_file()
