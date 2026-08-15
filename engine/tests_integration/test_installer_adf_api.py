"""ADF Viewer lifecycle APIs on the ops console (mocked process)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

pytest.importorskip("flask")

from sdlc_engine.installer.app import create_app
from sdlc_engine.installer import viewer_runtime as vr


class _FakeProc:
    def __init__(self, pid: int = 4242) -> None:
        self.pid = pid


def test_viewer_url_and_probe_tcp_closed() -> None:
    assert vr.viewer_url("127.0.0.1", 5050) == "http://127.0.0.1:5050/"
    probe = vr.probe_viewer("127.0.0.1", 1, timeout=0.05)  # port 1 unlikely open
    assert probe["tcp_open"] is False
    assert probe["http_ok"] is False


def test_api_adf_status_default(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post("/api/adf", json={"target": str(tmp_path)})
    assert res.status_code == 200
    body = res.get_json()
    assert body["ok"] is True
    assert "5050" in body["url"]
    assert body["process"]["alive"] is False
    assert "sdlc_engine.viewer" in body["cli"]


def test_api_adf_start_stop_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    fake_pid = {"n": 9001}

    def fake_popen(cmd: list[str], **kwargs: Any) -> _FakeProc:
        calls.append(list(cmd))
        fake_pid["n"] += 1
        return _FakeProc(fake_pid["n"])

    monkeypatch.setattr(vr.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(vr, "_tcp_open", lambda *a, **k: False)
    monkeypatch.setattr(vr, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(vr, "probe_viewer", lambda host="127.0.0.1", port=5050, **k: {
        "host": host,
        "port": port,
        "tcp_open": True,
        "http_ok": True,
        "url": f"http://{host}:{port}/",
        "detail": "HTTP 200",
    })
    monkeypatch.setattr(vr, "_run", lambda *a, **k: {"ok": True, "log": "", "exit_code": 0})

    killed: list[int] = []

    def fake_kill(pid: int, sig: int = 0) -> None:
        if sig != 0:
            killed.append(pid)

    def fake_killpg(pid: int, sig: int) -> None:
        killed.append(pid)

    monkeypatch.setattr(vr.os, "kill", fake_kill)
    monkeypatch.setattr(vr.os, "killpg", fake_killpg)
    monkeypatch.setattr(vr.time, "sleep", lambda *_a, **_k: None)

    app = create_app(tmp_path)
    client = app.test_client()

    start = client.post(
        "/api/adf/start",
        json={"target": str(tmp_path), "host": "127.0.0.1", "port": 5050},
    )
    assert start.status_code == 200
    body = start.get_json()
    assert body["ok"] is True
    assert body["result"]["ok"] is True
    assert calls and "sdlc_engine.viewer" in calls[0]
    assert (tmp_path / ".sdlc" / "adf-viewer-runtime.json").is_file()

    # Already running → 400
    again = client.post(
        "/api/adf/start",
        json={"target": str(tmp_path), "host": "127.0.0.1", "port": 5050},
    )
    assert again.status_code == 400
    assert again.get_json()["ok"] is False

    stop = client.post("/api/adf/stop", json={"target": str(tmp_path)})
    assert stop.status_code == 200
    assert stop.get_json()["ok"] is True
    assert not (tmp_path / ".sdlc" / "adf-viewer-runtime.json").is_file()

    # Restart after stop
    monkeypatch.setattr(vr, "_pid_alive", lambda pid: False)
    restart = client.post(
        "/api/adf/restart",
        json={"target": str(tmp_path), "port": 5055},
    )
    assert restart.status_code == 200
    assert restart.get_json()["ok"] is True
    assert any("5055" in c for c in calls[-1])


def test_api_adf_browse_missing_dir(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post(
        "/api/adf/browse",
        json={"target": str(tmp_path), "path": str(tmp_path / "nope")},
    )
    assert res.status_code == 400
    assert res.get_json()["ok"] is False


def test_api_adf_browse_marks_invalid_files(tmp_path: Path) -> None:
    adf_dir = tmp_path / "adf"
    adf_dir.mkdir()
    (adf_dir / "good.adf.json").write_text(
        json.dumps({"type": "doc", "version": 1, "content": []}),
        encoding="utf-8",
    )
    (adf_dir / "bad.adf.json").write_text("{nope", encoding="utf-8")
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post(
        "/api/adf/browse",
        json={"target": str(tmp_path), "path": str(adf_dir)},
    )
    assert res.status_code == 200
    files = {f["name"]: f for f in res.get_json()["files"]}
    assert files["good.adf.json"]["valid"] is True
    assert files["bad.adf.json"]["valid"] is False


def test_api_adf_init_work_with_claim(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SDLC_USER", "console-claim")
    adf = tmp_path / "adf" / "ORCH-11.adf.json"
    adf.parent.mkdir(parents=True)
    adf.write_text(
        json.dumps(
            {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "heading",
                        "attrs": {"level": 1},
                        "content": [{"type": "text", "text": "Claimed via API"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post(
        "/api/adf/init-work",
        json={
            "target": str(tmp_path),
            "path": str(adf),
            "work_id": "FEAT-013-api-claim",
            # claim defaults to True
        },
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["ok"] is True
    assert body["work_id"] == "FEAT-013-api-claim"
    reg = (tmp_path / "spdd" / "memory" / "registry.jsonl").read_text(encoding="utf-8")
    assert "console-claim" in reg
    assert (tmp_path / ".sdlc" / "pointer").read_text(encoding="utf-8").strip() == (
        "FEAT-013-api-claim"
    )


def test_api_adf_init_work_claim_conflict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SDLC_USER", "bob")
    wid = "FEAT-013-api-conflict"
    (tmp_path / "spdd" / "memory").mkdir(parents=True, exist_ok=True)
    (tmp_path / "spdd" / "memory" / "registry.jsonl").write_text(
        json.dumps(
            {
                "event": "claim",
                "work_id": wid,
                "status": "active",
                "phase": "analysis",
                "owner": "alice",
                "note": "seed",
                "ts": "2026-01-01T00:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    adf = tmp_path / "c.adf.json"
    adf.write_text(json.dumps({"type": "doc", "version": 1, "content": []}), encoding="utf-8")
    app = create_app(tmp_path)
    client = app.test_client()
    res = client.post(
        "/api/adf/init-work",
        json={"target": str(tmp_path), "path": str(adf), "work_id": wid},
    )
    assert res.status_code == 400
    assert "alice" in res.get_json()["error"]
    assert not (tmp_path / "spdd" / "canvas" / f"{wid}.md").exists()


def test_api_adf_init_work_validation(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    client = app.test_client()

    missing_path = client.post(
        "/api/adf/init-work",
        json={"target": str(tmp_path)},
    )
    assert missing_path.status_code == 400
    assert missing_path.get_json()["ok"] is False

    bad = tmp_path / "broken.json"
    bad.write_text('{"type":"doc","version":9}', encoding="utf-8")
    bad_init = client.post(
        "/api/adf/init-work",
        json={"target": str(tmp_path), "path": str(bad), "claim": False},
    )
    assert bad_init.status_code == 400
    assert bad_init.get_json()["ok"] is False

    dry = client.post(
        "/api/adf/init-work",
        json={
            "target": str(tmp_path),
            "path": str(tmp_path / "missing.adf.json"),
            "dry_run": True,
            "claim": False,
        },
    )
    assert dry.status_code == 400


def test_api_adf_browse_and_init_work(tmp_path: Path) -> None:
    adf_dir = tmp_path / "adf"
    adf_dir.mkdir()
    adf = adf_dir / "ORCH-7.adf.json"
    adf.write_text(
        json.dumps(
            {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "heading",
                        "attrs": {"level": 1},
                        "content": [{"type": "text", "text": "Console init"}],
                    },
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "From ops console"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    app = create_app(tmp_path)
    client = app.test_client()

    browse = client.post(
        "/api/adf/browse",
        json={"target": str(tmp_path), "path": str(adf_dir)},
    )
    assert browse.status_code == 200
    listing = browse.get_json()
    assert listing["ok"] is True
    assert any(f["name"] == "ORCH-7.adf.json" and f["valid"] for f in listing["files"])

    init = client.post(
        "/api/adf/init-work",
        json={
            "target": str(tmp_path),
            "path": str(adf),
            "claim": False,
            "work_id": "FEAT-013-console-adf-init",
        },
    )
    assert init.status_code == 200
    body = init.get_json()
    assert body["ok"] is True
    assert body["work_id"] == "FEAT-013-console-adf-init"
    assert body["source_issue"] == "ORCH-7"
    assert (tmp_path / "spdd" / "canvas" / "FEAT-013-console-adf-init.md").is_file()
    assert "sdlc-spdd-analysis" in body["next_command"]
    assert "work init-from-adf" in body["cli"]

    dry = client.post(
        "/api/adf/init-work",
        json={
            "target": str(tmp_path),
            "path": str(adf),
            "claim": False,
            "work_id": "FEAT-014-dry-only",
            "dry_run": True,
        },
    )
    assert dry.status_code == 200
    dry_body = dry.get_json()
    assert dry_body["ok"] is True
    assert dry_body["dry_run"] is True
    assert not (tmp_path / "spdd" / "canvas" / "FEAT-014-dry-only.md").exists()


def test_console_page_includes_adf_init_ui(tmp_path: Path) -> None:
    from sdlc_engine.installer.runner import orchestrator_root

    adf = (orchestrator_root() / "console-ui" / "src" / "components" / "AdfTab.vue").read_text(
        encoding="utf-8"
    )
    assert "Init SPDD work" in adf or "btn-adf-init" in adf
    assert "/api/adf/browse" in adf or "adf/browse" in adf
    assert "/api/adf/init-work" in adf or "adf/init-work" in adf
    assert "btn-adf-init" in adf


def test_start_viewer_missing_target(tmp_path: Path) -> None:
    missing = tmp_path / "gone"
    result = vr.start_viewer(missing)
    assert result["ok"] is False
    assert "not found" in result["error"]


def test_start_viewer_port_in_use(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(vr, "_pid_alive", lambda pid: False)
    monkeypatch.setattr(vr, "_tcp_open", lambda *a, **k: True)
    result = vr.start_viewer(tmp_path, port=5050)
    assert result["ok"] is False
    assert "already in use" in result["error"]
