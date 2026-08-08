"""Start/stop Neo4j + Guide from a local jmjava/orch-guide clone."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_GIT_URL = "https://github.com/jmjava/orch-guide.git"
RUNTIME_REL = Path(".sdlc") / "guide-runtime.json"


def runtime_path(target: Path | str) -> Path:
    return Path(target).expanduser().resolve() / RUNTIME_REL


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_runtime(target: Path | str) -> dict[str, Any]:
    path = runtime_path(target)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_runtime(target: Path | str, data: dict[str, Any]) -> None:
    path = runtime_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _clear_runtime(target: Path | str) -> None:
    path = runtime_path(target)
    if path.is_file():
        path.unlink()


def _tcp_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 600,
) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    log = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "command": cmd,
        "log": log.strip(),
    }


def guide_env(cfg: dict[str, Any]) -> dict[str, str]:
    """Environment for compose + append-ingest / spring-boot."""
    env = os.environ.copy()
    port = int(cfg.get("port") or 21337)
    bolt = int(cfg.get("neo4j_bolt_port") or 7687)
    http = int(cfg.get("neo4j_http_port") or 7474)
    https = int(cfg.get("neo4j_https_port") or 7473)
    profile = str(cfg.get("profile") or "sdlc-spdd")
    env["GUIDE_PROFILE"] = profile
    # Explicit Embabel Neo4j dialect + local personal profile (append-ingest honors override).
    env["SPRING_PROFILES_ACTIVE"] = str(
        cfg.get("spring_profiles") or f"neo4j,local,{profile}"
    )
    env["GUIDE_PORT"] = str(port)
    env["SERVER_PORT"] = str(port)
    env["NEO4J_BOLT_PORT"] = str(bolt)
    env["NEO4J_HTTP_PORT"] = str(http)
    env["NEO4J_HTTPS_PORT"] = str(https)
    env["NEO4J_PORT"] = str(bolt)
    env["NEO4J_URI"] = f"bolt://localhost:{bolt}"
    env["NEO4J_HOST"] = "localhost"
    env["NEO4J_USERNAME"] = str(cfg.get("neo4j_username") or "neo4j")
    if cfg.get("neo4j_password"):
        env["NEO4J_PASSWORD"] = str(cfg["neo4j_password"])
    # Avoid spring-boot dying when Anthropic autoconfigure is present but unused.
    if not env.get("ANTHROPIC_API_KEY"):
        env["ANTHROPIC_API_KEY"] = env.get(
            "ANTHROPIC_API_KEY_INGEST_PLACEHOLDER", "dummy-key"
        )
    return env


def ensure_guide_repo(
    cfg: dict[str, Any],
    *,
    pull: bool = True,
) -> dict[str, Any]:
    """Clone jmjava/orch-guide if missing; optionally fast-forward pull."""
    home = Path(str(cfg.get("guide_home") or "")).expanduser()
    url = str(cfg.get("guide_git_url") or DEFAULT_GIT_URL).strip() or DEFAULT_GIT_URL
    if not str(home):
        return {"ok": False, "error": "guide_home is required", "log": ""}

    if not home.exists():
        home.parent.mkdir(parents=True, exist_ok=True)
        result = _run(["git", "clone", url, str(home)], timeout=900)
        result["action"] = "clone"
        result["guide_home"] = str(home)
        result["git_url"] = url
        return result

    if not (home / ".git").is_dir():
        return {
            "ok": False,
            "error": f"{home} exists but is not a git clone",
            "action": "validate",
            "guide_home": str(home),
            "log": "",
        }

    logs: list[str] = []
    remote = _run(["git", "-C", str(home), "remote", "-v"])
    logs.append(remote.get("log") or "")
    ref = str(cfg.get("guide_git_ref") or "").strip()

    if pull or ref:
        # Include tags so guide_git_ref can pin release tags (e.g. sdlc-spdd-projection-v1).
        fetch = _run(
            ["git", "-C", str(home), "fetch", "origin", "--tags", "--force"],
            timeout=300,
        )
        logs.append(fetch.get("log") or "")

    if ref:
        # Checkout branch or tag when configured (creates local tracking branch if needed).
        cur = _run(["git", "-C", str(home), "rev-parse", "--abbrev-ref", "HEAD"])
        current = (cur.get("log") or "").strip().splitlines()[-1]
        # Detached HEAD at a tag reports HEAD; also compare the resolved object.
        resolved = _run(["git", "-C", str(home), "rev-parse", "HEAD"])
        want = _run(["git", "-C", str(home), "rev-parse", f"{ref}^{{commit}}"])
        already = (
            want.get("ok")
            and resolved.get("ok")
            and (resolved.get("log") or "").strip() == (want.get("log") or "").strip()
        )
        if not already and current != ref:
            co = _run(
                ["git", "-C", str(home), "checkout", "-B", ref, f"origin/{ref}"],
                timeout=120,
            )
            if not co["ok"]:
                # Annotated / lightweight tag, or local branch name.
                co = _run(["git", "-C", str(home), "checkout", "--detach", ref], timeout=120)
            if not co["ok"]:
                co = _run(["git", "-C", str(home), "checkout", ref], timeout=120)
            logs.append(co.get("log") or "")
            if not co["ok"]:
                return {
                    "ok": False,
                    "action": "checkout",
                    "guide_home": str(home),
                    "git_url": url,
                    "git_ref": ref,
                    "exit_code": co.get("exit_code", 1),
                    "log": "\n".join(x for x in logs if x).strip(),
                    "error": f"could not checkout guide_git_ref={ref}",
                }

    if pull:
        branch = _run(["git", "-C", str(home), "rev-parse", "--abbrev-ref", "HEAD"])
        br = (branch.get("log") or "main").strip().splitlines()[-1]
        # Detached checkouts (release tags) are already at the pin after checkout above.
        if br == "HEAD" and ref:
            head = _run(["git", "-C", str(home), "rev-parse", "--short", "HEAD"])
            logs.append(
                f"HEAD {(head.get('log') or '').strip()} detached at {ref} (tag/pin; skip pull)"
            )
            return {
                "ok": True,
                "action": "checkout",
                "guide_home": str(home),
                "git_url": url,
                "git_ref": ref,
                "exit_code": 0,
                "log": "\n".join(x for x in logs if x).strip(),
                "error": None,
            }
        pull_res = _run(
            ["git", "-C", str(home), "pull", "--ff-only", "origin", br],
            timeout=300,
        )
        logs.append(pull_res.get("log") or "")
        head = _run(["git", "-C", str(home), "rev-parse", "--short", "HEAD"])
        logs.append(f"HEAD {(head.get('log') or '').strip()} on {br}")
        return {
            "ok": pull_res["ok"],
            "action": "pull",
            "guide_home": str(home),
            "git_url": url,
            "git_ref": ref or br,
            "exit_code": pull_res.get("exit_code", 1),
            "log": "\n".join(x for x in logs if x).strip(),
            "error": None if pull_res["ok"] else "git pull --ff-only failed (dirty tree?)",
        }

    head = _run(["git", "-C", str(home), "rev-parse", "--short", "HEAD"])
    branch = _run(["git", "-C", str(home), "rev-parse", "--abbrev-ref", "HEAD"])
    return {
        "ok": True,
        "action": "present",
        "guide_home": str(home),
        "git_url": url,
        "git_ref": ref or (branch.get("log") or "").strip(),
        "log": (head.get("log") or "").strip(),
    }


def start_neo4j(cfg: dict[str, Any]) -> dict[str, Any]:
    home = Path(str(cfg.get("guide_home") or "")).expanduser()
    if not home.is_dir() or not (home / "compose.yaml").is_file():
        return {
            "ok": False,
            "error": "guide_home missing compose.yaml — ensure/pull jmjava/orch-guide first",
            "log": "",
        }
    env = guide_env(cfg)
    # Explicit service name enables the neo4j profile service.
    result = _run(
        ["docker", "compose", "up", "neo4j", "-d"],
        cwd=home,
        env=env,
        timeout=300,
    )
    if result["ok"]:
        # Wait briefly for Bolt.
        host = "127.0.0.1"
        bolt = int(cfg.get("neo4j_bolt_port") or 7687)
        ready = False
        for _ in range(20):
            if _tcp_open(host, bolt, timeout=0.8):
                ready = True
                break
            time.sleep(1.5)
        result["bolt_ready"] = ready
        result["bolt_url"] = f"bolt://localhost:{bolt}"
        result["browser_url"] = (
            f"http://localhost:{int(cfg.get('neo4j_http_port') or 7474)}"
        )
    return result


def stop_neo4j(cfg: dict[str, Any]) -> dict[str, Any]:
    home = Path(str(cfg.get("guide_home") or "")).expanduser()
    if not home.is_dir():
        return {"ok": False, "error": "guide_home missing", "log": ""}
    env = guide_env(cfg)
    return _run(
        ["docker", "compose", "stop", "neo4j"],
        cwd=home,
        env=env,
        timeout=120,
    )


def probe_neo4j(cfg: dict[str, Any]) -> dict[str, Any]:
    bolt = int(cfg.get("neo4j_bolt_port") or 7687)
    http = int(cfg.get("neo4j_http_port") or 7474)
    return {
        "bolt_port": bolt,
        "http_port": http,
        "bolt_open": _tcp_open("127.0.0.1", bolt),
        "http_open": _tcp_open("127.0.0.1", http),
        "bolt_url": f"bolt://localhost:{bolt}",
        "browser_url": f"http://localhost:{http}",
        "container": "embabel-neo4j",
    }


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def guide_process_status(target: Path | str, cfg: dict[str, Any]) -> dict[str, Any]:
    rt = _load_runtime(target)
    pid = rt.get("pid")
    alive = bool(isinstance(pid, int) and _pid_alive(pid))
    port = int(cfg.get("port") or 21337)
    host = str(cfg.get("host") or "127.0.0.1")
    return {
        "pid": pid if alive else None,
        "alive": alive,
        "log_path": rt.get("log_path"),
        "started_at": rt.get("started_at"),
        "mode": rt.get("mode"),
        "port_open": _tcp_open(host, port),
        "runtime_path": str(runtime_path(target)),
    }


def start_guide(
    target: Path | str,
    cfg: dict[str, Any],
    *,
    ingest: bool = True,
    ensure_neo4j: bool = True,
) -> dict[str, Any]:
    """Start Guide (append-ingest or spring-boot) in the background."""
    home = Path(str(cfg.get("guide_home") or "")).expanduser()
    script = home / "scripts" / "append-ingest.sh"
    if not script.is_file():
        return {
            "ok": False,
            "error": f"missing {script} — ensure/pull jmjava/orch-guide first",
            "log": "",
        }

    status = guide_process_status(target, cfg)
    if status.get("alive"):
        return {
            "ok": False,
            "error": f"Guide already running (pid {status['pid']})",
            "status": status,
            "log": "",
        }

    if ensure_neo4j:
        neo = start_neo4j(cfg)
        if not neo.get("ok"):
            return {
                "ok": False,
                "error": "Neo4j failed to start",
                "neo4j": neo,
                "log": neo.get("log") or "",
            }

    env = guide_env(cfg)
    # append-ingest.sh honors FORCE_STARTUP_INGEST (0 = skip reload-on-startup ingest).
    env["FORCE_STARTUP_INGEST"] = "1" if ingest else "0"
    port = int(cfg.get("port") or 21337)
    profile = str(cfg.get("profile") or "user")
    log_path = Path(cfg.get("guide_log_path") or f"/tmp/sdlc-guide-{profile}-{port}.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env["GUIDE_INGEST_LOG"] = str(log_path)
    mode = "append-ingest" if ingest else "append-ingest-no-startup-ingest"
    cmd = ["bash", str(script)]

    log_f = open(log_path, "a", encoding="utf-8")  # noqa: SIM115 — kept by child
    log_f.write(f"\n===== start {_utc_now()} mode={mode} port={port} =====\n")
    log_f.flush()
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(home),
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
        "mode": mode,
        "port": port,
        "profile": cfg.get("profile"),
        "command": cmd,
    }
    _save_runtime(target, rt)
    return {
        "ok": True,
        "status": guide_process_status(target, cfg),
        "log_path": str(log_path),
        "pid": proc.pid,
        "mode": mode,
        "sse_url": f"http://{cfg.get('host') or '127.0.0.1'}:{port}/sse",
        "log": f"Started pid={proc.pid}; logging to {log_path}",
    }


def stop_guide(target: Path | str, cfg: dict[str, Any]) -> dict[str, Any]:
    rt = _load_runtime(target)
    pid = rt.get("pid")
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
        time.sleep(1.5)
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

    # Also clear whatever still holds GUIDE_PORT (matches append-ingest behavior).
    port = int(cfg.get("port") or 21337)
    lsof = _run(["bash", "-lc", f"lsof -ti :{port} || true"])
    pids = [
        int(x)
        for x in (lsof.get("log") or "").split()
        if x.strip().isdigit()
    ]
    for p in pids:
        try:
            os.kill(p, signal.SIGTERM)
            killed.append(f"SIGTERM port-holder {p}")
        except ProcessLookupError:
            pass

    _clear_runtime(target)
    return {
        "ok": True,
        "killed": killed,
        "port": port,
        "log": "; ".join(killed) if killed else "No running Guide process recorded",
    }


def stack_status(target: Path | str, cfg: dict[str, Any]) -> dict[str, Any]:
    from .guide import probe_guide

    return {
        "guide_home": cfg.get("guide_home"),
        "guide_git_url": cfg.get("guide_git_url") or DEFAULT_GIT_URL,
        "neo4j": probe_neo4j(cfg),
        "guide_process": guide_process_status(target, cfg),
        "guide_probe": probe_guide(str(cfg.get("host") or "127.0.0.1"), int(cfg.get("port") or 21337)),
    }
