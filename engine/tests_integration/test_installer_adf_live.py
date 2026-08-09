"""Live ADF Viewer process lifecycle via console APIs (real Popen / SIGTERM).

Spawns ``python -m sdlc_engine.viewer`` on an ephemeral port, probes HTTP,
then stops and asserts the process is gone. Always-on; costs a few seconds.
"""

from __future__ import annotations

import json
import socket
import time
from pathlib import Path

import pytest

pytest.importorskip("flask")

from sdlc_engine.installer.app import create_app
from sdlc_engine.installer import viewer_runtime as vr


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_http(host: str, port: int, *, timeout_sec: float = 15.0) -> dict:
    deadline = time.time() + timeout_sec
    last: dict = {}
    while time.time() < deadline:
        last = vr.probe_viewer(host, port, timeout=0.4)
        if last.get("http_ok"):
            return last
        time.sleep(0.15)
    return last


def test_live_adf_start_probe_stop_via_api(tmp_path: Path) -> None:
    adf_dir = tmp_path / "adf"
    adf_dir.mkdir(parents=True)
    (adf_dir / "LIVE-1.adf.json").write_text(
        json.dumps(
            {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "live lifecycle"}],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    host = "127.0.0.1"
    port = _free_port()
    app = create_app(tmp_path)
    client = app.test_client()
    body = {"target": str(tmp_path), "host": host, "port": port}

    try:
        start = client.post("/api/adf/start", json=body)
        assert start.status_code == 200, start.get_json()
        started = start.get_json()
        assert started["ok"] is True
        assert started["result"]["ok"] is True
        pid = started["result"].get("pid") or started["process"].get("pid")
        assert isinstance(pid, int)

        probe = _wait_http(host, port)
        assert probe.get("http_ok") is True, (
            f"viewer never became ready on {host}:{port}: {probe}; "
            f"log={started['result'].get('log_path')}"
        )

        status = client.post("/api/adf", json=body)
        assert status.status_code == 200
        st = status.get_json()
        assert st["process"]["alive"] is True
        assert st["probe"]["http_ok"] is True
        assert str(port) in (st.get("url") or "")

        # Refuse double-start while alive
        again = client.post("/api/adf/start", json=body)
        assert again.status_code == 400
        assert again.get_json()["ok"] is False

        stop = client.post("/api/adf/stop", json=body)
        assert stop.status_code == 200
        assert stop.get_json()["ok"] is True

        # Port / process should clear shortly after stop.
        deadline = time.time() + 8.0
        while time.time() < deadline:
            if not vr._pid_alive(pid) and not vr._tcp_open(host, port):
                break
            time.sleep(0.15)
        assert not vr._pid_alive(pid), f"pid {pid} still alive after stop"
        assert not vr._tcp_open(host, port), f"port {port} still open after stop"
        assert not (tmp_path / ".sdlc" / "adf-viewer-runtime.json").is_file()

        after = client.post("/api/adf", json=body)
        assert after.status_code == 200
        assert after.get_json()["process"]["alive"] is False
    finally:
        # Best-effort cleanup if an assertion failed mid-flight.
        try:
            vr.stop_viewer(tmp_path)
        except Exception:  # noqa: BLE001
            pass
