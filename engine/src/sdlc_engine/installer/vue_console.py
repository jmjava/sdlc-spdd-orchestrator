"""Resolve and optionally build the Vue3 ops console dist."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Mapping
from pathlib import Path

from .runner import orchestrator_root

STUB_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>SDLC-SPDD Ops Console</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 42rem; margin: 2rem auto; padding: 0 1rem; }
    pre { background: #f4f4f4; padding: 0.75rem 1rem; overflow: auto; }
    code { font-size: 0.95em; }
  </style>
</head>
<body>
  <h1>SDLC-SPDD Ops Console</h1>
  <p>Vue3 console dist is not built. JSON API is still at <code>/api/health</code>.</p>
  <p>From the orchestrator repo:</p>
  <pre>cd console-ui && npm ci && npm run build
python -m sdlc_engine console --target .</pre>
  <p><code>sdlc.sh console</code> builds <code>console-ui/dist</code> automatically when npm is available.</p>
</body>
</html>
"""


def vue_dist_ready(path: Path | str | None) -> bool:
    if not path:
        return False
    root = Path(path)
    return root.is_dir() and (root / "index.html").is_file()


def default_vue_dist(orch: Path | str | None = None) -> Path:
    root = Path(orch) if orch is not None else orchestrator_root()
    return root / "console-ui" / "dist"


def resolve_vue_console_dist(
    explicit: Path | str | bool | None = None,
    *,
    env: Mapping[str, str] | None = None,
    orch: Path | str | None = None,
) -> Path | None:
    """Return a ready Vue dist, or None to serve the stub.

    * ``explicit`` path/str — must contain ``index.html`` (raises if missing).
    * ``explicit is False`` — force stub (ignore env/auto).
    * ``explicit is None`` — ``SDLC_VUE_CONSOLE_DIST``, then ``<orch>/console-ui/dist``.
    * ``SDLC_CONSOLE_UI=stub`` disables auto-detect when ``explicit is None``.
    """
    if explicit is False:
        return None
    environ = env if env is not None else os.environ
    if explicit is not None and explicit is not True:
        path = Path(str(explicit)).expanduser().resolve()
        if not vue_dist_ready(path):
            raise FileNotFoundError(f"Vue console dist missing index.html: {path}")
        return path
    if str(environ.get("SDLC_CONSOLE_UI", "")).strip().lower() == "stub":
        return None
    raw = str(environ.get("SDLC_VUE_CONSOLE_DIST") or "").strip()
    if raw:
        path = Path(raw).expanduser().resolve()
        if not vue_dist_ready(path):
            raise FileNotFoundError(f"Vue console dist missing index.html: {path}")
        return path
    auto = default_vue_dist(orch)
    if vue_dist_ready(auto):
        return auto
    return None


def ensure_vue_console_dist(
    *,
    build: bool = False,
    orch: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    npm: str | None = None,
    timeout_sec: int = 180,
) -> Path | None:
    """Resolve an existing dist, optionally running ``npm run build``."""
    try:
        found = resolve_vue_console_dist(env=env, orch=orch)
    except FileNotFoundError:
        found = None
    if found is not None:
        return found
    environ = env if env is not None else os.environ
    if not build or str(environ.get("SDLC_VUE_SKIP_BUILD", "")).strip() in {"1", "true", "yes"}:
        return None
    root = Path(orch) if orch is not None else orchestrator_root()
    ui = root / "console-ui"
    if not (ui / "package.json").is_file():
        return None
    npm_bin = npm or str(environ.get("NPM_BIN") or "npm")
    if not (ui / "node_modules").is_dir():
        install = subprocess.run(
            [npm_bin, "ci"],
            cwd=ui,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_sec,
        )
        if install.returncode != 0:
            install = subprocess.run(
                [npm_bin, "install"],
                cwd=ui,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_sec,
            )
        if install.returncode != 0:
            return None
    built = subprocess.run(
        [npm_bin, "run", "build"],
        cwd=ui,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_sec,
    )
    if built.returncode != 0:
        return None
    dist = ui / "dist"
    return dist if vue_dist_ready(dist) else None
