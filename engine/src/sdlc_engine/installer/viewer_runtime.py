"""Start/stop the ADF Viewer process from the ops console (link-out lifecycle)."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from ..io_util import clear_file, load_json_dict, save_json_dict
from ..timeutil import utc_now as _utc_now
from .process_util import pid_alive as _pid_alive
from .process_util import run_cmd
from .process_util import tcp_open as _tcp_open

RUNTIME_REL = Path(".sdlc") / "adf-viewer-runtime.json"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5050


def runtime_path(target: Path | str) -> Path:
    return Path(target).expanduser().resolve() / RUNTIME_REL


def _load_runtime(target: Path | str) -> dict[str, Any]:
    return load_json_dict(runtime_path(target))


def _save_runtime(target: Path | str, data: dict[str, Any]) -> None:
    save_json_dict(runtime_path(target), data)


def _clear_runtime(target: Path | str) -> None:
    clear_file(runtime_path(target))


def _run(cmd: list[str], *, timeout: int = 30) -> dict[str, Any]:
    return run_cmd(cmd, timeout=timeout)


def viewer_url(host: str, port: int) -> str:
    return f"http://{host}:{int(port)}/"


def probe_viewer(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, *, timeout: float = 1.5) -> dict[str, Any]:
    """TCP + HTTP probe of the ADF Viewer."""
    tcp = _tcp_open(host, port, timeout=min(timeout, 1.0))
    url = viewer_url(host, port)
    http_ok = False
    detail = "TCP closed"
    if tcp:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
                http_ok = 200 <= int(resp.status) < 500
                detail = f"HTTP {resp.status}"
        except urllib.error.HTTPError as exc:
            http_ok = True  # server responded
            detail = f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            detail = f"TCP open; HTTP error: {exc}"
    return {
        "host": host,
        "port": int(port),
        "tcp_open": tcp,
        "http_ok": http_ok,
        "url": url,
        "detail": detail,
    }


def viewer_process_status(
    target: Path | str,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> dict[str, Any]:
    rt = _load_runtime(target)
    pid = rt.get("pid")
    alive = bool(isinstance(pid, int) and _pid_alive(pid))
    host = str(rt.get("host") or host or DEFAULT_HOST)
    port = int(rt.get("port") or port or DEFAULT_PORT)
    return {
        "pid": pid if alive else None,
        "alive": alive,
        "log_path": rt.get("log_path"),
        "started_at": rt.get("started_at"),
        "host": host,
        "port": port,
        "port_open": _tcp_open(host, port),
        "url": viewer_url(host, port),
        "runtime_path": str(runtime_path(target)),
        "target": rt.get("target"),
    }


def viewer_payload(
    target: Path | str,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> dict[str, Any]:
    status = viewer_process_status(target, host=host, port=port)
    probe = probe_viewer(str(status.get("host") or host), int(status.get("port") or port))
    return {
        "ok": True,
        "process": status,
        "probe": probe,
        "url": probe.get("url") or status.get("url"),
        "cli": (
            f"python3 -m sdlc_engine.viewer --root {Path(target).expanduser().resolve()} "
            f"--host {status.get('host') or host} --port {status.get('port') or port}"
        ),
        "notes": (
            "Editing and Jira sync live in the ADF Viewer. "
            "This console tab only starts/stops the process and opens the URL."
        ),
    }


def start_viewer(
    target: Path | str,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> dict[str, Any]:
    """Start ADF Viewer in the background for *target*."""
    root = Path(target).expanduser().resolve()
    if not root.is_dir():
        return {"ok": False, "error": f"target not found: {root}", "log": ""}

    host = str(host or DEFAULT_HOST).strip() or DEFAULT_HOST
    port = int(port or DEFAULT_PORT)
    status = viewer_process_status(root, host=host, port=port)
    if status.get("alive"):
        return {
            "ok": False,
            "error": f"ADF Viewer already running (pid {status['pid']})",
            "status": status,
            "log": "",
        }
    if status.get("port_open") or _tcp_open(host, port):
        return {
            "ok": False,
            "error": f"port {port} already in use — Stop/Restart or choose another port",
            "status": status,
            "log": "",
        }

    log_path = Path(f"/tmp/sdlc-adf-viewer-{port}.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "sdlc_engine.viewer",
        "--root",
        str(root),
        "--host",
        host,
        "--port",
        str(port),
    ]
    log_f = open(log_path, "a", encoding="utf-8")  # noqa: SIM115 — kept by child
    log_f.write(f"\n===== start {_utc_now()} port={port} root={root} =====\n")
    log_f.flush()
    env = os.environ.copy()
    # Ensure engine package is importable when launched from console.
    src = Path(__file__).resolve().parents[2]
    py_path = str(src)
    env["PYTHONPATH"] = py_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(root),
            env=env,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except OSError as exc:
        log_f.close()
        return {"ok": False, "error": str(exc), "log": ""}

    rt = {
        "pid": proc.pid,
        "log_path": str(log_path),
        "started_at": _utc_now(),
        "host": host,
        "port": port,
        "target": str(root),
        "command": cmd,
    }
    _save_runtime(root, rt)
    return {
        "ok": True,
        "status": viewer_process_status(root, host=host, port=port),
        "log_path": str(log_path),
        "pid": proc.pid,
        "url": viewer_url(host, port),
        "log": f"Started pid={proc.pid}; logging to {log_path}",
    }


def stop_viewer(target: Path | str) -> dict[str, Any]:
    root = Path(target).expanduser().resolve()
    rt = _load_runtime(root)
    pid = rt.get("pid")
    port = int(rt.get("port") or DEFAULT_PORT)
    killed: list[str] = []

    if isinstance(pid, int) and _pid_alive(pid):
        try:
            os.killpg(pid, signal.SIGTERM)
            killed.append(f"SIGTERM pgid/pid {pid}")
        except ProcessLookupError:
            try:
                os.kill(pid, signal.SIGTERM)
                killed.append(f"SIGTERM pid {pid}")
            except ProcessLookupError:
                pass
        time.sleep(1.0)
        if _pid_alive(pid):
            try:
                os.killpg(pid, signal.SIGKILL)
                killed.append(f"SIGKILL pgid/pid {pid}")
            except ProcessLookupError:
                try:
                    os.kill(pid, signal.SIGKILL)
                    killed.append(f"SIGKILL pid {pid}")
                except ProcessLookupError:
                    pass

    lsof = _run(["bash", "-lc", f"lsof -ti :{port} || true"])
    pids = [int(x) for x in (lsof.get("log") or "").split() if x.strip().isdigit()]
    for p in pids:
        try:
            os.kill(p, signal.SIGTERM)
            killed.append(f"SIGTERM port-holder {p}")
        except ProcessLookupError:
            pass

    _clear_runtime(root)
    return {
        "ok": True,
        "killed": killed,
        "port": port,
        "log": "; ".join(killed) if killed else "No running ADF Viewer process recorded",
    }


def restart_viewer(
    target: Path | str,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> dict[str, Any]:
    stop = stop_viewer(target)
    # Allow the port to free.
    time.sleep(0.4)
    start = start_viewer(target, host=host, port=port)
    return {
        "ok": bool(start.get("ok")),
        "stop": stop,
        "start": start,
        "log": f"stop: {stop.get('log')}; start: {start.get('log') or start.get('error')}",
        "error": start.get("error"),
        "url": start.get("url"),
        "pid": start.get("pid"),
    }
