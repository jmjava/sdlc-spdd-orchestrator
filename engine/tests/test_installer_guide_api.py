"""Flask API coverage for Guide / rollback / verify console routes (mocked I/O)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

pytest.importorskip("flask")

from sdlc_engine.installer import app as installer_app
from sdlc_engine.installer.app import create_app


def test_api_run_verify(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post(
        "/api/run",
        json={
            "action": "verify",
            "target": str(tmp_path),
            "assistants": ["cursor"],
            "dry_run": True,
        },
    )
    # verify script may fail on bare tmp_path; still must be a valid API response
    assert res.status_code in {200, 400}
    body = res.get_json()
    assert "ok" in body
    assert "log" in body or "error" in body


def test_api_rollback_endpoint(tmp_path: Path) -> None:
    from sdlc_engine.installer.rollback import backups_root

    root = backups_root(tmp_path)
    backup = root / "20260101T000000Z"
    backup.mkdir(parents=True)
    (backup / "manifest.json").write_text(
        '{"files": ["agent-context/memory/context-index.md"]}\n', encoding="utf-8"
    )
    (backup / "agent-context" / "memory").mkdir(parents=True)
    (backup / "agent-context" / "memory" / "context-index.md").write_text(
        "from-backup\n", encoding="utf-8"
    )

    app = create_app(tmp_path)
    client = app.test_client()
    dry = client.post(
        "/api/rollback",
        json={
            "target": str(tmp_path),
            "backup_id": "20260101T000000Z",
            "dry_run": True,
        },
    )
    assert dry.status_code == 200
    assert dry.get_json()["ok"] is True

    missing = client.post(
        "/api/rollback",
        json={"target": str(tmp_path), "backup_id": ""},
    )
    assert missing.status_code == 400


def test_api_guide_save_and_mocked_lifecycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        installer_app,
        "ensure_guide_repo",
        lambda cfg, pull=True: {"ok": True, "action": "present", "log": "ok"},
    )
    monkeypatch.setattr(
        installer_app,
        "start_neo4j",
        lambda cfg: {"ok": True, "log": "neo up"},
    )
    monkeypatch.setattr(
        installer_app,
        "stop_neo4j",
        lambda cfg: {"ok": True, "log": "neo down"},
    )
    monkeypatch.setattr(
        installer_app,
        "start_guide",
        lambda target, cfg, ingest=True, ensure_neo4j=True: {
            "ok": True,
            "pid": 111,
            "log": "started",
            "log_path": "/tmp/x.log",
        },
    )
    monkeypatch.setattr(
        installer_app,
        "stop_guide",
        lambda target, cfg: {"ok": True, "killed": ["111"], "log": "stopped"},
    )
    monkeypatch.setattr(
        installer_app,
        "ensure_spdd_profile",
        lambda *a, **k: {"ok": True, "path": str(tmp_path / "p.yml"), "written": True},
    )
    monkeypatch.setattr(
        installer_app,
        "load_spdd_projection",
        lambda *a, **k: {"ok": True, "status": 200, "data": {"workIdCount": 2}},
    )
    monkeypatch.setattr(
        installer_app,
        "projection_stats",
        lambda *a, **k: {"ok": True, "data": {"workIdCount": 2}},
    )
    monkeypatch.setattr(
        installer_app,
        "guide_stats",
        lambda *a, **k: {"ok": True, "status": 200, "data": {"chunkCount": 9}},
    )
    monkeypatch.setattr(
        installer_app,
        "load_references",
        lambda *a, **k: {"ok": True, "status": 200, "data": {"elapsed": "PT1S"}},
    )
    monkeypatch.setattr(
        installer_app,
        "purge_preview",
        lambda *a, **k: {"ok": True, "data": {"matchCount": 0}},
    )
    monkeypatch.setattr(
        installer_app,
        "purge_content",
        lambda *a, **k: {"ok": True, "data": {"deleted": 0}},
    )
    monkeypatch.setattr(
        installer_app,
        "reset_git_revision",
        lambda *a, **k: {"ok": True, "data": {"removed": False}},
    )
    monkeypatch.setattr(
        installer_app,
        "purge_all_content_elements_docker",
        lambda **k: {"ok": True, "log": "deleted"},
    )
    monkeypatch.setattr(
        installer_app,
        "probe_guide",
        lambda host, port: {
            "host": host,
            "port": port,
            "tcp_open": True,
            "http_ok": True,
            "detail": "HTTP 200",
            "sse_url": f"http://{host}:{port}/sse",
        },
    )
    monkeypatch.setattr(
        installer_app,
        "probe_mcp_sse",
        lambda host, port: {"reachable": True, "detail": "HTTP 200", "sse_url": "x"},
    )
    monkeypatch.setattr(
        installer_app,
        "stack_status",
        lambda target, cfg: {
            "guide_home": cfg.get("guide_home"),
            "guide_git_url": "https://github.com/jmjava/orch-guide.git",
            "neo4j": {"bolt_open": True, "http_open": True, "bolt_port": 7687, "http_port": 7474},
            "guide_process": {"alive": True, "pid": 111, "port_open": True},
            "guide_probe": {
                "tcp_open": True,
                "http_ok": True,
                "detail": "ok",
                "host": "127.0.0.1",
                "port": 21337,
                "sse_url": "http://127.0.0.1:21337/sse",
            },
        },
    )
    monkeypatch.setattr(installer_app, "named_entity_module_present", lambda home: True)

    guide_home = tmp_path / "guide"
    (guide_home / "scripts").mkdir(parents=True)
    (guide_home / "compose.yaml").write_text("services: {}\n", encoding="utf-8")
    (guide_home / "scripts" / "append-ingest.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    app = create_app(tmp_path)
    client = app.test_client()
    t = str(tmp_path)

    save = client.post(
        "/api/guide/save",
        json={
            "target": t,
            "guide_home": str(guide_home),
            "guide_git_ref": "sdlc-spdd-projection-v2",
            "port": 21337,
        },
    )
    assert save.status_code == 200
    assert save.get_json()["ok"] is True

    for path, extra in [
        ("/api/guide/ensure", {"save_first": True, "no_pull": True}),
        ("/api/guide/neo4j/start", {}),
        ("/api/guide/neo4j/stop", {}),
        ("/api/guide/start", {"no_ingest": True, "skip_neo4j": True}),
        ("/api/guide/stop", {}),
        ("/api/guide/ensure-profile", {}),
        ("/api/guide/projection/load", {}),
        ("/api/guide/stats", {}),
        ("/api/guide/ingest", {}),
        ("/api/guide/purge/preview", {}),
        ("/api/guide/purge", {"confirm": True}),
        ("/api/guide/git-revision/reset", {"directory": t}),
        ("/api/guide/purge-all-rag", {"confirm": True}),
    ]:
        res = client.post(path, json={"target": t, **extra})
        assert res.status_code in {200, 400}, path
        body = res.get_json()
        assert body is not None, path
        assert "ok" in body or "config" in body, path


def test_api_detect_requires_target(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post("/api/detect", json={})
    assert res.status_code == 400
