"""Local Embabel Guide configuration helpers for the ops dashboard."""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .guide_runtime import DEFAULT_GIT_URL

CONFIG_REL = Path(".sdlc") / "guide-config.json"

DEFAULT_PROFILES = (
    {
        "id": "menke",
        "purpose": "Code half of corpus — local Embabel/DICE fork repos",
    },
    {
        "id": "menke-2",
        "purpose": "Reference reading — SPDD, context engineering, evals URLs",
    },
    {
        "id": "menke-3",
        "purpose": "Framework depth — shell, harness, craft, RAG",
    },
    {
        "id": "menke-4",
        "purpose": "Docgen consumer — documentation-generator + course-builder docs",
    },
    {
        "id": "menke-5",
        "purpose": "Additional menke layer (if present in jmjava/orch-guide)",
    },
)

_CONFIG_KEYS = (
    "guide_home",
    "guide_git_url",
    "guide_git_ref",
    "profile",
    "spring_profiles",
    "host",
    "mcp_server",
    "notes",
    "neo4j_username",
    "neo4j_password",
    "guide_log_path",
)


def config_path(target: Path | str) -> Path:
    return Path(target).expanduser().resolve() / CONFIG_REL


def _looks_like_guide_home(path: Path) -> bool:
    """True when ``path`` is a usable jmjava/guide (or embabel/guide) checkout."""
    return path.is_dir() and (path / "scripts" / "append-ingest.sh").is_file()


def resolve_guide_home() -> Path:
    """Resolve Guide checkout for dual-repo Cloud Agent / local layouts.

    Order:
    1. ``GUIDE_HOME`` when it points at a real guide tree
    2. Sibling ``../guide`` next to the orchestrator (Cursor dual-repo env)
    3. ``~/github/jmjava/orch-guide`` or legacy ``~/github/jmjava/guide`` when present
    4. Otherwise ``~/github/jmjava/orch-guide`` (may not exist yet)
    """
    env = os.environ.get("GUIDE_HOME", "").strip()
    if env:
        env_path = Path(env).expanduser().resolve()
        if _looks_like_guide_home(env_path):
            return env_path

    try:
        from .runner import orchestrator_root

        sibling = (orchestrator_root().parent / "guide").resolve()
        if _looks_like_guide_home(sibling):
            return sibling
    except FileNotFoundError:
        pass

    # Also accept Cursor's multi-repo workspace layout even if orchestrator_root
    # resolution is unavailable in an unusual install.
    for candidate in (
        Path("/agent/repos/guide"),
        Path.home() / "github" / "jmjava" / "orch-guide",
        Path.home() / "github" / "jmjava" / "guide",
    ):
        resolved = candidate.expanduser().resolve()
        if _looks_like_guide_home(resolved):
            return resolved

    # Invalid GUIDE_HOME is ignored (do not prefer a bare directory over the
    # conventional checkout path used by local / Cloud Agent layouts).
    return Path.home() / "github" / "jmjava" / "orch-guide"


def default_config() -> dict[str, Any]:
    home = os.environ.get("GUIDE_HOME", "").strip()
    if not home:
        orch = Path.home() / "github" / "jmjava" / "orch-guide"
        legacy = Path.home() / "github" / "jmjava" / "guide"
        if orch.is_dir():
            home = str(orch)
        elif legacy.is_dir():
            home = str(legacy)
        else:
            home = str(orch)
    return {
        "guide_home": home,
        "guide_git_url": os.environ.get("GUIDE_GIT_URL", DEFAULT_GIT_URL).strip()
        or DEFAULT_GIT_URL,
        # Pin the merged SPDD NamedEntity projection on jmjava/orch-guide (tag on main).
        # Override with GUIDE_GIT_REF=main for floating tip, or a branch/tag of your choice.
        "guide_git_ref": os.environ.get(
            "GUIDE_GIT_REF", "sdlc-spdd-projection-v2"
        ).strip(),
        "profile": os.environ.get("GUIDE_PROFILE", "sdlc-spdd").strip() or "sdlc-spdd",
        "spring_profiles": os.environ.get("SPRING_PROFILES_ACTIVE", "").strip(),
        "host": os.environ.get("GUIDE_HOST", "127.0.0.1").strip() or "127.0.0.1",
        "port": int(os.environ.get("GUIDE_PORT", "21337") or "21337"),
        "neo4j_bolt_port": int(os.environ.get("NEO4J_BOLT_PORT", "7687") or "7687"),
        "neo4j_http_port": int(os.environ.get("NEO4J_HTTP_PORT", "7474") or "7474"),
        "neo4j_https_port": int(os.environ.get("NEO4J_HTTPS_PORT", "7473") or "7473"),
        "neo4j_username": os.environ.get("NEO4J_USERNAME", "neo4j").strip() or "neo4j",
        "neo4j_password": os.environ.get("NEO4J_PASSWORD", "brahmsian").strip()
        or "brahmsian",
        "mcp_server": "embabel-dev",
        "guide_log_path": "",
        "notes": "",
    }


def load_config(target: Path | str) -> dict[str, Any]:
    path = config_path(target)
    cfg = default_config()
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for key in _CONFIG_KEYS:
                    if key in data and data[key] is not None:
                        cfg[key] = data[key]
                for key in ("port", "neo4j_bolt_port", "neo4j_http_port", "neo4j_https_port"):
                    if key in data and data[key] is not None:
                        cfg[key] = int(data[key])
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    cfg["config_path"] = str(path)
    cfg["profiles"] = list(DEFAULT_PROFILES)
    return cfg


def save_config(target: Path | str, updates: dict[str, Any]) -> dict[str, Any]:
    cfg = load_config(target)
    for key in _CONFIG_KEYS:
        if key in updates and updates[key] is not None:
            cfg[key] = str(updates[key]).strip()
    for key in ("port", "neo4j_bolt_port", "neo4j_http_port", "neo4j_https_port"):
        if key in updates and updates[key] is not None:
            cfg[key] = int(updates[key])
    path = config_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {k: cfg[k] for k in _CONFIG_KEYS}
    payload.update(
        {
            "port": cfg["port"],
            "neo4j_bolt_port": cfg["neo4j_bolt_port"],
            "neo4j_http_port": cfg["neo4j_http_port"],
            "neo4j_https_port": cfg["neo4j_https_port"],
        }
    )
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return load_config(target)


def probe_guide(host: str, port: int, *, timeout: float = 1.5) -> dict[str, Any]:
    """Best-effort reachability check for a local Guide instance."""
    result: dict[str, Any] = {
        "host": host,
        "port": port,
        "tcp_open": False,
        "http_ok": False,
        "detail": "",
        "sse_url": f"http://{host}:{port}/sse",
    }
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            result["tcp_open"] = True
    except OSError as exc:
        result["detail"] = f"TCP closed: {exc}"
        return result

    url = f"http://{host}:{port}/"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — local probe
            result["http_ok"] = 200 <= int(resp.status) < 500
            result["detail"] = f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        result["http_ok"] = True
        result["detail"] = f"HTTP {exc.code} (server responding)"
    except Exception as exc:  # noqa: BLE001
        result["detail"] = f"TCP open; HTTP probe: {exc}"
    return result


def ingest_command(cfg: dict[str, Any]) -> str:
    home = cfg.get("guide_home") or "$GUIDE_HOME"
    profile = cfg.get("profile") or "sdlc-spdd"
    profiles = cfg.get("spring_profiles") or f"neo4j,local,{profile}"
    port = cfg.get("port") or 21337
    bolt = cfg.get("neo4j_bolt_port") or 7687
    http = cfg.get("neo4j_http_port") or 7474
    https = cfg.get("neo4j_https_port") or 7473
    return (
        f"cd {home}\n"
        f"GUIDE_PROFILE={profile} SPRING_PROFILES_ACTIVE={profiles} \\\n"
        f"  GUIDE_PORT={port} SERVER_PORT={port} \\\n"
        f"  NEO4J_BOLT_PORT={bolt} NEO4J_HTTP_PORT={http} NEO4J_HTTPS_PORT={https} \\\n"
        f"  NEO4J_PORT={bolt} NEO4J_URI=bolt://localhost:{bolt} \\\n"
        f"  GUIDE_INGEST_LOG=/tmp/{profile}-ingest.log ./scripts/append-ingest.sh"
    )


def checklist(
    cfg: dict[str, Any],
    probe: dict[str, Any] | None = None,
    *,
    neo4j: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    home = Path(cfg["guide_home"]) if cfg.get("guide_home") else None
    probe = probe or {}
    neo4j = neo4j or {}
    items = [
        {
            "id": "guide_home",
            "label": "Guide repo path exists",
            "ok": bool(home and home.is_dir()),
            "hint": f"Clone/pull from {cfg.get('guide_git_url') or DEFAULT_GIT_URL}",
        },
        {
            "id": "compose",
            "label": "compose.yaml present (Neo4j)",
            "ok": bool(home and (home / "compose.yaml").is_file()),
            "hint": "Required for docker compose up neo4j",
        },
        {
            "id": "append_script",
            "label": "append-ingest.sh present",
            "ok": bool(home and (home / "scripts" / "append-ingest.sh").is_file()),
            "hint": "Expected under $GUIDE_HOME/scripts/append-ingest.sh",
        },
        {
            "id": "profile_yml",
            "label": f"Profile application-{cfg.get('profile')}.yml",
            "ok": bool(
                home
                and (
                    (
                        home
                        / "scripts"
                        / "user-config"
                        / f"application-{cfg.get('profile')}.yml"
                    ).is_file()
                    or (home / f"application-{cfg.get('profile')}.yml").is_file()
                )
            ),
            "hint": "Profiles live under guide/scripts/user-config/ (local only).",
        },
        {
            "id": "neo4j",
            "label": f"Neo4j Bolt on :{cfg.get('neo4j_bolt_port')}",
            "ok": bool(neo4j.get("bolt_open")),
            "hint": "Use Start Neo4j (custom NEO4J_*_PORT from config).",
        },
        {
            "id": "tcp",
            "label": f"Guide listening on {cfg.get('host')}:{cfg.get('port')}",
            "ok": bool(probe.get("tcp_open")),
            "hint": "Use Start Guide (+ingest) then connect embabel-dev MCP.",
        },
        {
            "id": "sqlite_bridge",
            "label": "SQLite is the pre-GUIDE local cache (rebuild anytime)",
            "ok": True,
            "hint": "./scripts/sdlc.sh db rebuild — not a Guide replacement.",
        },
        {
            "id": "mcp",
            "label": "Use embabel-dev MCP tools (docs_vectorSearch / docs_textSearch)",
            "ok": True,
            "hint": f"SSE: http://{cfg.get('host')}:{cfg.get('port')}/sse",
        },
    ]
    return items
