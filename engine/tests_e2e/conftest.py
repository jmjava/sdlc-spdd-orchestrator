"""Shared fixtures for suite 3 (E2E integration)."""

from __future__ import annotations

import socket
import threading
import time
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("flask")

from sdlc_engine.installer import app as installer_app
from sdlc_engine.installer import viewer_runtime as vr
from sdlc_engine.installer.app import create_app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture()
def live_console(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Start ops console on a free port (for Guide tab Playwright probe)."""
    from werkzeug.serving import make_server

    state: dict[str, Any] = {"alive": False, "pid": 424242, "host": "127.0.0.1", "port": 5050}

    def _save(target: Path | str, host: str, port: int) -> None:
        root = Path(target).expanduser().resolve()
        (root / ".sdlc").mkdir(parents=True, exist_ok=True)
        vr._save_runtime(
            root,
            {
                "pid": state["pid"],
                "port": int(port),
                "host": host,
                "log_path": f"/tmp/sdlc-adf-viewer-{port}.log",
                "started_at": "2026-01-01T00:00:00Z",
                "target": str(root),
            },
        )
        state["alive"] = True
        state["host"] = host
        state["port"] = int(port)

    def fake_start(target: Path | str, *, host: str = "127.0.0.1", port: int = 5050) -> dict[str, Any]:
        if state["alive"]:
            return {"ok": False, "error": "ADF Viewer already running", "log": ""}
        _save(target, host, port)
        return {"ok": True, "log": "stub start", "pid": state["pid"]}

    def fake_stop(target: Path | str) -> dict[str, Any]:
        root = Path(target).expanduser().resolve()
        vr._clear_runtime(root)
        state["alive"] = False
        return {"ok": True, "log": "stub stop"}

    monkeypatch.setattr(vr, "_pid_alive", lambda pid: bool(state["alive"]))
    monkeypatch.setattr(vr, "_tcp_open", lambda *a, **k: bool(state["alive"]))
    monkeypatch.setattr(
        vr,
        "probe_viewer",
        lambda host="127.0.0.1", port=5050, **k: {
            "host": host,
            "port": int(port),
            "tcp_open": bool(state["alive"]),
            "http_ok": bool(state["alive"]),
            "url": f"http://{host}:{int(port)}/",
            "detail": "HTTP 200" if state["alive"] else "closed",
        },
    )
    for mod in (vr, installer_app):
        monkeypatch.setattr(mod, "start_viewer", fake_start)
        monkeypatch.setattr(mod, "stop_viewer", fake_stop)
        monkeypatch.setattr(mod, "restart_viewer", fake_restart)

    app = create_app(tmp_path)
    port = _free_port()
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
    else:
        server.shutdown()
        raise RuntimeError("ops console failed to start")

    yield {"base": f"http://127.0.0.1:{port}", "target": tmp_path, "state": state}
    server.shutdown()
