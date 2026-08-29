"""Tests for the ops console (install, SQLite, rollback, Guide helpers)."""

from __future__ import annotations

from pathlib import Path

import pytest

flask = pytest.importorskip("flask")

from sdlc_engine.db import LocalIndex  # noqa: E402
from sdlc_engine.installer.app import create_app  # noqa: E402
from sdlc_engine.installer.detect import detect_target  # noqa: E402
from sdlc_engine.installer.guide import checklist, load_config, save_config  # noqa: E402
from sdlc_engine.installer.rollback import list_backups, restore_backup  # noqa: E402
from sdlc_engine.installer.runner import orchestrator_root  # noqa: E402
from sdlc_engine.project import Project  # noqa: E402


def test_orchestrator_root_finds_scripts() -> None:
    root = orchestrator_root()
    assert (root / "scripts" / "setup-agent-prompts.sh").is_file()
    assert (root / "scripts" / "upgrade-project.sh").is_file()


def test_detect_fresh_directory(tmp_path: Path) -> None:
    info = detect_target(tmp_path)
    assert info["exists"] is True
    assert info["mode"] == "fresh"
    assert info["recommendation"] == "install"
    assert info["markers"] == []


def test_detect_upgrade_markers(tmp_path: Path) -> None:
    marker = tmp_path / "scripts" / "sdlc-spdd" / "sdlc.sh"
    marker.parent.mkdir(parents=True)
    marker.write_text("#!/bin/bash\n", encoding="utf-8")
    info = detect_target(tmp_path)
    assert info["mode"] == "upgrade"
    assert info["recommendation"] == "upgrade"
    assert "scripts/sdlc-spdd/sdlc.sh" in info["markers"]


def test_detect_missing(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    info = detect_target(missing)
    assert info["exists"] is False
    assert info["recommendation"] == "create"


def test_api_health_and_detect(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()
    health = client.get("/api/health")
    assert health.status_code == 200
    body = health.get_json()
    assert body["ok"] is True
    assert Path(body["orchestrator_root"]).is_dir()

    page = client.get("/")
    assert page.status_code == 200
    assert b"SDLC-SPDD Ops Console" in page.data

    det = client.post("/api/detect", json={"target": str(tmp_path)})
    assert det.status_code == 200
    assert det.get_json()["recommendation"] == "install"


def test_api_run_dry_install(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post(
        "/api/run",
        json={
            "action": "install",
            "target": str(tmp_path),
            "assistants": ["cursor"],
            "dry_run": True,
        },
    )
    data = res.get_json()
    assert data["ok"] is True
    assert data["exit_code"] == 0
    assert "setup-agent-prompts.sh" in " ".join(data["command"])
    assert "--dry-run" in data["command"]
    summary = data["summary"]
    assert summary["dry_run"] is True
    assert summary["would_count"] >= 1
    assert summary["would"]
    assert any("sdlc-spdd-init" in step for step in summary["next_steps"])


def test_api_run_dry_upgrade(tmp_path: Path) -> None:
    marker = tmp_path / "agent-context" / "sdlc-workflow.sh"
    marker.parent.mkdir(parents=True)
    marker.write_text("#!/bin/bash\n", encoding="utf-8")
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post(
        "/api/run",
        json={
            "action": "upgrade",
            "target": str(tmp_path),
            "assistants": ["cursor", "copilot"],
            "dry_run": True,
        },
    )
    data = res.get_json()
    assert data["ok"] is True
    assert "upgrade-project.sh" in " ".join(data["command"])


def test_sqlite_status_and_rebuild(tmp_path: Path) -> None:
    (tmp_path / "spdd" / "canvas").mkdir(parents=True)
    (tmp_path / "spdd" / "memory").mkdir(parents=True)
    (tmp_path / "spdd" / "memory" / "registry.jsonl").write_text("", encoding="utf-8")
    app = create_app(tmp_path)
    client = app.test_client()
    missing = client.post("/api/sqlite/status", json={"target": str(tmp_path)})
    assert missing.status_code == 200
    assert missing.get_json()["exists"] is False

    rebuilt = client.post("/api/sqlite/rebuild", json={"target": str(tmp_path)})
    assert rebuilt.status_code == 200
    body = rebuilt.get_json()
    assert body["ok"] is True
    assert Path(body["stats"]["path"]).is_file()

    status = client.post("/api/sqlite/status", json={"target": str(tmp_path)})
    info = status.get_json()
    assert info["exists"] is True
    assert "work_items" in info

    # status_dict used by LocalIndex directly
    index = LocalIndex(Project.resolve(tmp_path))
    assert index.status_dict()["exists"] is True


def test_rollback_restore(tmp_path: Path) -> None:
    backup = tmp_path / ".sdlc-spdd-upgrade-backups" / "20260101T120000Z"
    rel = Path(".cursor") / "commands" / "sdlc-spdd-init.md"
    src = backup / rel
    src.parent.mkdir(parents=True)
    src.write_text("BACKUP_CONTENT\n", encoding="utf-8")
    dest = tmp_path / rel
    dest.parent.mkdir(parents=True)
    dest.write_text("CURRENT\n", encoding="utf-8")

    listed = list_backups(tmp_path)
    assert len(listed) == 1
    assert listed[0]["id"] == "20260101T120000Z"

    dry = restore_backup(tmp_path, "20260101T120000Z", dry_run=True)
    assert dry["ok"] is True
    assert dest.read_text(encoding="utf-8") == "CURRENT\n"

    live = restore_backup(tmp_path, "20260101T120000Z", dry_run=False, safety_backup=True)
    assert live["ok"] is True
    assert dest.read_text(encoding="utf-8") == "BACKUP_CONTENT\n"
    assert live["safety_backup"]
    safety = Path(live["safety_backup"])
    assert (safety / rel).read_text(encoding="utf-8") == "CURRENT\n"

    app = create_app(tmp_path)
    client = app.test_client()
    api = client.post("/api/backups", json={"target": str(tmp_path)})
    assert api.status_code == 200
    assert len(api.get_json()["backups"]) >= 1


def test_guide_config_roundtrip(tmp_path: Path) -> None:
    cfg = load_config(tmp_path)
    assert "profile" in cfg
    saved = save_config(
        tmp_path,
        {
            "guide_home": str(tmp_path / "guide-repo"),
            "guide_git_url": "https://github.com/jmjava/orch-guide.git",
            "profile": "menke-2",
            "host": "127.0.0.1",
            "port": 21337,
            "neo4j_bolt_port": 17687,
            "neo4j_http_port": 17474,
            "notes": "test",
        },
    )
    assert saved["profile"] == "menke-2"
    assert saved["neo4j_bolt_port"] == 17687
    assert (tmp_path / ".sdlc" / "guide-config.json").is_file()
    items = checklist(saved, {"tcp_open": False}, neo4j={"bolt_open": False})
    assert any(i["id"] == "tcp" and i["ok"] is False for i in items)
    assert any(i["id"] == "neo4j" and i["ok"] is False for i in items)

    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post("/api/guide", json={"target": str(tmp_path)})
    assert res.status_code == 200
    body = res.get_json()
    assert body["config"]["profile"] == "menke-2"
    assert "NEO4J_BOLT_PORT=17687" in body["ingest_command"]
    assert "neo4j" in body


def test_guide_env_custom_ports(monkeypatch) -> None:
    from sdlc_engine.installer import guide_runtime as gr
    from sdlc_engine.installer.guide_runtime import guide_env

    # Keep this unit test independent of whether Bolt is open on the host.
    monkeypatch.setattr(gr, "_tcp_open", lambda *a, **k: False)
    monkeypatch.delenv("SKIP_COMPOSE_NEO4J", raising=False)

    env = guide_env(
        {
            "profile": "sdlc-spdd",
            "port": 21337,
            "neo4j_bolt_port": 17687,
            "neo4j_http_port": 17474,
            "neo4j_https_port": 17473,
            "neo4j_password": "secret",
        }
    )
    assert env["SERVER_PORT"] == "21337"
    assert env["GUIDE_PORT"] == "21337"
    assert env["SPRING_PROFILES_ACTIVE"] == "neo4j,local,sdlc-spdd"
    assert env["NEO4J_BOLT_PORT"] == "17687"
    assert env["NEO4J_URI"] == "bolt://localhost:17687"
    assert env["NEO4J_PASSWORD"] == "secret"
    assert "SKIP_COMPOSE_NEO4J" not in env or env.get("SKIP_COMPOSE_NEO4J") in {"", None}


def test_guide_env_sets_skip_compose_when_bolt_open(monkeypatch) -> None:
    from sdlc_engine.installer import guide_runtime as gr
    from sdlc_engine.installer.guide_runtime import guide_env

    monkeypatch.delenv("SKIP_COMPOSE_NEO4J", raising=False)
    monkeypatch.setattr(gr, "_tcp_open", lambda *a, **k: True)
    env = guide_env({"port": 21337, "neo4j_bolt_port": 7687})
    assert env["SKIP_COMPOSE_NEO4J"] == "1"


def test_guide_env_preserves_explicit_skip_compose(monkeypatch) -> None:
    from sdlc_engine.installer import guide_runtime as gr
    from sdlc_engine.installer.guide_runtime import guide_env

    monkeypatch.setenv("SKIP_COMPOSE_NEO4J", "0")
    monkeypatch.setattr(gr, "_tcp_open", lambda *a, **k: True)
    env = guide_env({"port": 21337, "neo4j_bolt_port": 7687})
    assert env["SKIP_COMPOSE_NEO4J"] == "0"


def test_start_neo4j_errors_without_compose(tmp_path: Path, monkeypatch) -> None:
    from sdlc_engine.installer import guide_runtime as gr

    monkeypatch.setattr(gr, "_tcp_open", lambda *a, **k: False)
    result = gr.start_neo4j({"guide_home": str(tmp_path), "neo4j_bolt_port": 7687})
    assert result["ok"] is False
    assert "compose.yaml" in (result.get("error") or "")


def test_stop_guide_noop_without_runtime(tmp_path: Path) -> None:
    from sdlc_engine.installer.guide_runtime import stop_guide

    result = stop_guide(tmp_path, {"port": 21337})
    assert result["ok"] is True
    assert result["killed"] == []


def test_ensure_guide_repo_requires_home() -> None:
    from sdlc_engine.installer.guide_runtime import ensure_guide_repo

    result = ensure_guide_repo({"guide_home": ""})
    assert result["ok"] is False
    assert "guide_home" in (result.get("error") or "")


def test_load_runtime_tolerates_corrupt_json(tmp_path: Path) -> None:
    from sdlc_engine.installer.guide_runtime import _load_runtime, runtime_path

    path = runtime_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")
    assert _load_runtime(tmp_path) == {}


def test_resolve_guide_home_prefers_valid_env(tmp_path: Path, monkeypatch) -> None:
    from sdlc_engine.installer.guide import resolve_guide_home

    home = tmp_path / "env-guide"
    (home / "scripts").mkdir(parents=True)
    (home / "scripts" / "append-ingest.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    monkeypatch.setenv("GUIDE_HOME", str(home))
    assert resolve_guide_home() == home.resolve()


def test_resolve_guide_home_ignores_bare_env(tmp_path: Path, monkeypatch) -> None:
    from sdlc_engine.installer import guide as guide_mod
    from sdlc_engine.installer.guide import resolve_guide_home

    bare = tmp_path / "not-guide"
    bare.mkdir()
    monkeypatch.setenv("GUIDE_HOME", str(bare))
    monkeypatch.setattr(guide_mod, "_looks_like_guide_home", lambda _p: False)
    assert resolve_guide_home() == Path.home() / "github" / "jmjava" / "orch-guide"


def test_start_neo4j_compose_path(tmp_path: Path, monkeypatch) -> None:
    from sdlc_engine.installer import guide_runtime as gr

    guide = tmp_path / "guide"
    guide.mkdir()
    (guide / "compose.yaml").write_text("services: {}\n", encoding="utf-8")
    calls = {"n": 0}

    def fake_tcp(*_a, **_k):
        calls["n"] += 1
        # First probe (already running?) false; later wait loop true.
        return calls["n"] > 1

    monkeypatch.setattr(gr, "_tcp_open", fake_tcp)
    monkeypatch.setattr(
        gr,
        "_run",
        lambda *a, **k: {"ok": True, "exit_code": 0, "command": [], "log": "up"},
    )
    result = gr.start_neo4j(
        {"guide_home": str(guide), "neo4j_bolt_port": 17687, "neo4j_http_port": 17474}
    )
    assert result["ok"] is True
    assert result["action"] == "started"
    assert result["bolt_ready"] is True


def test_ensure_guide_repo_present_no_pull(tmp_path: Path, monkeypatch) -> None:
    from sdlc_engine.installer import guide_runtime as gr

    guide = tmp_path / "guide"
    (guide / ".git").mkdir(parents=True)

    def fake_run(cmd, **_k):
        joined = " ".join(cmd)
        if "rev-parse" in joined and "--short" in joined:
            return {"ok": True, "exit_code": 0, "command": cmd, "log": "abc1234"}
        if "abbrev-ref" in joined:
            return {"ok": True, "exit_code": 0, "command": cmd, "log": "main"}
        if "remote" in joined:
            return {"ok": True, "exit_code": 0, "command": cmd, "log": "origin"}
        return {"ok": True, "exit_code": 0, "command": cmd, "log": ""}

    monkeypatch.setattr(gr, "_run", fake_run)
    result = gr.ensure_guide_repo({"guide_home": str(guide)}, pull=False)
    assert result["ok"] is True
    assert result["action"] == "present"


def test_embabel_profile_and_named_entity_gate(tmp_path: Path) -> None:
    from sdlc_engine.installer.guide_compliance import (
        embabel_mechanics_checklist,
        ensure_spdd_profile,
        named_entity_module_present,
    )

    fake_guide = tmp_path / "guide"
    domain = fake_guide / "src/main/kotlin/com/embabel/guide/spdd/domain"
    domain.mkdir(parents=True)
    (domain / "SpddDomain.kt").write_text("class WorkId\n", encoding="utf-8")
    dict_path = fake_guide / "src/main/kotlin/com/embabel/guide/spdd/SpddEntityDictionary.kt"
    dict_path.parent.mkdir(parents=True, exist_ok=True)
    dict_path.write_text(
        'fun create() = DataDictionary.fromClasses("sdlc-spdd")\n',
        encoding="utf-8",
    )
    assert named_entity_module_present(fake_guide) is True

    real_guide = Path("/home/ubuntu/github/jmjava/guide")
    if real_guide.is_dir():
        assert named_entity_module_present(real_guide) is True

    written = ensure_spdd_profile(
        fake_guide, orchestrator_root=tmp_path / "orch", profile="sdlc-spdd-test"
    )
    assert written["ok"] is True
    assert Path(written["path"]).is_file()
    assert "spdd-projection" in Path(written["path"]).read_text(encoding="utf-8")

    mechanics = embabel_mechanics_checklist(
        cfg={"host": "127.0.0.1", "port": 21337, "profile": "sdlc-spdd"},
        neo4j={"bolt_open": True},
        guide_probe={"tcp_open": False},
        mcp={"reachable": False},
        projection={"ok": False},
        guide_home_ok=True,
        named_entity_module_ok=True,
        spring_profiles="neo4j,local,sdlc-spdd",
    )
    by_id = {m["id"]: m["ok"] for m in mechanics}
    assert by_id["profiles"] is True
    assert by_id["named_entity"] is True
    assert by_id["neo4j"] is True


def test_api_guide_page_has_runtime_controls(tmp_path: Path) -> None:
    """Vue Guide/ADF tabs own the operator buttons (Flask HTML retired)."""
    from sdlc_engine.installer.runner import orchestrator_root

    guide = (orchestrator_root() / "console-ui" / "src" / "components" / "GuideTab.vue").read_text(
        encoding="utf-8"
    )
    adf = (orchestrator_root() / "console-ui" / "src" / "components" / "AdfTab.vue").read_text(
        encoding="utf-8"
    )
    for needle in (
        "Start Neo4j",
        "Start Guide (+ingest)",
        "Load NamedEntity projection",
        "Incremental ingest",
        "Purge preview",
        "Purge ALL RAG",
        'data-testid="btn-purge"',
        'data-testid="btn-git-reset"',
    ):
        assert needle in guide, needle
    for needle in ("Start viewer", 'data-testid="btn-adf-start"', "Init SPDD"):
        assert needle in adf, needle

    app = create_app(tmp_path, vue_dist=False)
    page = app.test_client().get("/")
    assert page.status_code == 200
    assert b"Vue3 console dist is not built" in page.data


def test_guide_ops_helpers_and_purge_confirm(tmp_path: Path) -> None:
    from sdlc_engine.installer.guide_ops import default_operator_directories

    dirs = default_operator_directories(tmp_path)
    assert any(d.endswith("spdd/memory") for d in dirs)
    assert any(d.endswith("spdd/canvas") for d in dirs)

    app = create_app(tmp_path)
    client = app.test_client()
    denied = client.post("/api/guide/purge", json={"target": str(tmp_path)})
    assert denied.status_code == 400
    assert denied.get_json()["ok"] is False

    denied_all = client.post("/api/guide/purge-all-rag", json={"target": str(tmp_path)})
    assert denied_all.status_code == 400
