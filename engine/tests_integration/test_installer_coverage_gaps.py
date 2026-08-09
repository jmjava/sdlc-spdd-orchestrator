"""Targeted installer coverage for guide config, stack status, and app error paths."""

from __future__ import annotations

import io
import json
import os
import subprocess
import urllib.error
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

pytest.importorskip("flask")

import sdlc_engine.installer.app as app_module
from sdlc_engine.installer import guide as guide_mod
from sdlc_engine.installer import guide_compliance as gc
from sdlc_engine.installer import guide_ops as go
from sdlc_engine.installer import guide_runtime as gr
from sdlc_engine.installer import runner as rn
from sdlc_engine.installer.app import _gh_auth_status, create_app


def test_guide_config_load_save_and_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GUIDE_HOME", raising=False)
    orch = tmp_path / "orch-guide"
    orch.mkdir()
    monkeypatch.setenv("GUIDE_HOME", str(orch))

    cfg = guide_mod.default_config()
    assert cfg["guide_home"] == str(orch)

    saved = guide_mod.save_config(
        tmp_path,
        {
            "guide_home": str(orch),
            "profile": "sdlc-spdd",
            "port": 21337,
            "notes": "test",
        },
    )
    assert saved["notes"] == "test"
    assert guide_mod.config_path(tmp_path).is_file()

    corrupt = guide_mod.config_path(tmp_path)
    corrupt.write_text("{not-json", encoding="utf-8")
    loaded = guide_mod.load_config(tmp_path)
    assert loaded["config_path"] == str(corrupt)

    monkeypatch.setattr(guide_mod.socket, "create_connection", lambda *a, **k: (_ for _ in ()).throw(OSError("closed")))
    tcp_fail = guide_mod.probe_guide("127.0.0.1", 9)
    assert tcp_fail["tcp_open"] is False

    class _Conn:
        def __enter__(self) -> "_Conn":
            return self

        def __exit__(self, *a: Any) -> None:
            return None

    monkeypatch.setattr(guide_mod.socket, "create_connection", lambda *a, **k: _Conn())

    class _Http:
        status = 200

        def __enter__(self) -> "_Http":
            return self

        def __exit__(self, *a: Any) -> None:
            return None

    monkeypatch.setattr(guide_mod.urllib.request, "urlopen", lambda *a, **k: _Http())
    ok = guide_mod.probe_guide("127.0.0.1", 21337)
    assert ok["tcp_open"] is True
    assert ok["http_ok"] is True

    class _HttpErr(urllib.error.HTTPError):
        def __init__(self) -> None:
            super().__init__("http://x", 503, "err", hdrs=None, fp=io.BytesIO(b""))

    monkeypatch.setattr(
        guide_mod.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(_HttpErr()),
    )
    err_probe = guide_mod.probe_guide("127.0.0.1", 21337)
    assert err_probe["http_ok"] is True

    monkeypatch.setattr(
        guide_mod.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("weird http")),
    )
    generic = guide_mod.probe_guide("127.0.0.1", 21337)
    assert "weird http" in generic["detail"]


def test_guide_default_config_home_resolution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GUIDE_HOME", raising=False)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(guide_mod.Path, "home", staticmethod(lambda: fake_home))
    jm = fake_home / "github" / "jmjava"
    (jm / "guide").mkdir(parents=True)
    legacy_cfg = guide_mod.default_config()
    assert legacy_cfg["guide_home"] == str(jm / "guide")
    (jm / "orch-guide").mkdir()
    orch_cfg = guide_mod.default_config()
    assert orch_cfg["guide_home"] == str(jm / "orch-guide")

    (jm / "guide").rmdir()
    (jm / "orch-guide").rmdir()
    fallback_cfg = guide_mod.default_config()
    assert fallback_cfg["guide_home"] == str(jm / "orch-guide")


def test_guide_ops_http_error_and_purge_params(monkeypatch: pytest.MonkeyPatch) -> None:
    class _HttpErr(urllib.error.HTTPError):
        def __init__(self) -> None:
            super().__init__(
                "http://x",
                502,
                "bad",
                hdrs=None,
                fp=io.BytesIO(b"not-json-error"),
            )

    monkeypatch.setattr(
        go.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(_HttpErr()),
    )
    err = go.guide_stats("127.0.0.1", 21337)
    assert err["ok"] is False
    assert err["data"]["error"] == "not-json-error"

    class _Resp:
        status = 200

        def __enter__(self) -> "_Resp":
            return self

        def __exit__(self, *a: Any) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok":true}'

    monkeypatch.setattr(go.urllib.request, "urlopen", lambda *a, **k: _Resp())
    assert go.purge_preview("127.0.0.1", 21337, uri_prefix="spdd://")["ok"] is True
    assert go.purge_content("127.0.0.1", 21337, uri_prefix="spdd://")["ok"] is True


def test_runner_orchestrator_root_env_and_missing_script(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_root = tmp_path / "orchestrator"
    scripts = fake_root / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "setup-agent-prompts.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setenv("SDLC_ORCHESTRATOR_ROOT", str(fake_root))

    real_is_file = Path.is_file

    def selective_is_file(self: Path) -> bool:
        if self.name == "setup-agent-prompts.sh" and self.parent.name == "scripts":
            env_root = Path(os.environ.get("SDLC_ORCHESTRATOR_ROOT", "")).resolve()
            if env_root / "scripts" / "setup-agent-prompts.sh" == self:
                return True
            return False
        return real_is_file(self)

    monkeypatch.setattr(Path, "is_file", selective_is_file)
    assert rn.orchestrator_root() == fake_root.resolve()

    broken = tmp_path / "broken"
    broken.mkdir()
    monkeypatch.setattr(rn, "orchestrator_root", lambda: broken.resolve())
    missing = rn.run_action(action="install", target=tmp_path / "proj")
    assert missing["ok"] is False
    assert "Script not found" in missing["log"]


def test_stack_status_and_neo4j_compose(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "guide"
    home.mkdir()
    (home / "compose.yaml").write_text("services: {}\n", encoding="utf-8")
    cfg = {
        "guide_home": str(home),
        "host": "127.0.0.1",
        "port": 21337,
        "neo4j_bolt_port": 7687,
        "neo4j_http_port": 7474,
        "neo4j_https_port": 7473,
        "profile": "sdlc-spdd",
    }

    monkeypatch.setattr(gr, "_tcp_open", lambda *a, **k: False)
    monkeypatch.setattr(
        gr,
        "_run",
        lambda *a, **k: {"ok": True, "exit_code": 0, "log": "up", "command": a[0]},
    )
    monkeypatch.setattr(gr.time, "sleep", lambda *_a, **_k: None)

    calls = {"n": 0}

    def tcp_after_compose(host: str, port: int, timeout: float = 1.0) -> bool:
        calls["n"] += 1
        return calls["n"] > 1

    monkeypatch.setattr(gr, "_tcp_open", tcp_after_compose)
    neo = gr.start_neo4j(cfg)
    assert neo["ok"] is True
    assert neo.get("bolt_ready") is True

    monkeypatch.setattr(gr, "probe_neo4j", lambda c: {"bolt_open": True})
    monkeypatch.setattr(gr, "guide_process_status", lambda t, c: {"alive": False})
    monkeypatch.setattr(
        guide_mod,
        "probe_guide",
        lambda host, port, timeout=1.5: {
            "host": host,
            "port": port,
            "tcp_open": False,
            "http_ok": False,
            "detail": "stub",
            "sse_url": "",
        },
    )
    st = gr.stack_status(tmp_path, cfg)
    assert st["neo4j"]["bolt_open"] is True
    assert "guide_probe" in st


def test_guide_compliance_load_projection_edges(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Raw:
        status = 200

        def __enter__(self) -> "_Raw":
            return self

        def __exit__(self, *a: Any) -> None:
            return None

        def read(self) -> bytes:
            return b"not-json-body"

    monkeypatch.setattr(gc.urllib.request, "urlopen", lambda *a, **k: _Raw())
    loaded = gc.load_spdd_projection("127.0.0.1", 21337)
    assert loaded["ok"] is True
    assert loaded["data"]["raw"] == "not-json-body"

    class _HttpErr(urllib.error.HTTPError):
        def __init__(self) -> None:
            super().__init__("http://x", 502, "bad", hdrs=None, fp=io.BytesIO(b"err"))

    monkeypatch.setattr(
        gc.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(_HttpErr()),
    )
    assert gc.load_spdd_projection("127.0.0.1", 1)["ok"] is False

    monkeypatch.setattr(
        gc.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("network down")),
    )
    assert gc.load_spdd_projection("127.0.0.1", 2)["ok"] is False

    class _SseErr(urllib.error.HTTPError):
        def __init__(self) -> None:
            super().__init__("http://x/sse", 401, "auth", hdrs=None, fp=io.BytesIO(b""))

    monkeypatch.setattr(
        gc.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(_SseErr()),
    )
    sse = gc.probe_mcp_sse("127.0.0.1", 21337)
    assert sse["reachable"] is True
    assert "401" in sse["detail"]


def test_gh_auth_status_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_module.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
    missing = _gh_auth_status()
    assert missing["installed"] is False

    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("gh", 3)),
    )
    timed = _gh_auth_status()
    assert timed["installed"] is True
    assert timed["authenticated"] is False

    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("gh broken")),
    )
    broken = _gh_auth_status()
    assert broken["installed"] is False
    assert "gh broken" in broken["detail"]

    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        lambda *a, **k: MagicMock(returncode=0, stdout="", stderr=""),
    )
    assert _gh_auth_status()["authenticated"] is True

    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        lambda *a, **k: MagicMock(returncode=1, stdout="", stderr=""),
    )
    assert _gh_auth_status()["authenticated"] is False


def test_api_error_responses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = create_app(tmp_path)
    client = app.test_client()

    bad = client.post("/api/dashboard/status", json={"target": str(tmp_path / "missing")})
    assert bad.status_code == 400

    monkeypatch.setattr(app_module, "_dashboard_status", lambda target: (_ for _ in ()).throw(RuntimeError("boom")))
    err = client.post("/api/dashboard/status", json={"target": str(tmp_path)})
    assert err.status_code == 500
    assert err.get_json()["ok"] is False

    monkeypatch.setattr(
        app_module.ContextStore,
        "parity",
        lambda self, repair=False: (_ for _ in ()).throw(RuntimeError("parity fail")),
    )
    parity = client.post("/api/persistence/parity", json={"target": str(tmp_path)})
    assert parity.status_code == 500
    assert "parity fail" in parity.get_json()["error"]
