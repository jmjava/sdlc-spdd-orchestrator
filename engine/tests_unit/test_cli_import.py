"""REF-005: importing the CLI must not load Flask, sqlite3, or urllib."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ENGINE_SRC = Path(__file__).resolve().parents[2] / "engine" / "src"
COMMANDS = ENGINE_SRC / "sdlc_engine" / "commands"

# pathlib (Project) imports urllib.parse; ban the HTTP client stack and Flask/SQLite.
BANNED = ("flask", "sqlite3", "urllib.request", "urllib.error")
BANNED_ENGINE = (
    "sdlc_engine.context_store",
    "sdlc_engine.db",
    "sdlc_engine.issues",
    "sdlc_engine.guide_client",
    "sdlc_engine.sunset",
    "sdlc_engine.installer.app",
    "sdlc_engine.viewer.app",
)


def test_import_sdlc_engine_cli_loads_no_heavy_modules() -> None:
    script = r"""
import sys
import sdlc_engine.cli  # noqa: F401
banned = ("flask", "sqlite3", "urllib.request", "urllib.error")
banned_engine = (
    "sdlc_engine.context_store",
    "sdlc_engine.db",
    "sdlc_engine.issues",
    "sdlc_engine.guide_client",
    "sdlc_engine.sunset",
    "sdlc_engine.installer.app",
    "sdlc_engine.viewer.app",
)
loaded = [name for name in banned + banned_engine if name in sys.modules]
if loaded:
    raise SystemExit("heavy modules loaded: " + ", ".join(loaded))
print("ok")
"""
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    env["PYTHONPATH"] = str(ENGINE_SRC) + (
        (":" + env["PYTHONPATH"]) if env.get("PYTHONPATH") else ""
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "ok" in proc.stdout


def _ccn(node: ast.AST) -> int:
    count = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With)):
            count += 1
        elif isinstance(child, ast.BoolOp):
            count += max(0, len(child.values) - 1)
    return count


def test_no_cmd_star_function_exceeds_ccn_10() -> None:
    hits: list[str] = []
    for path in sorted(ENGINE_SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
                "cmd_"
            ):
                ccn = _ccn(node)
                if ccn > 10:
                    hits.append(f"{path.name}:{node.name} CCN={ccn}")
    assert hits == []


def test_command_run_functions_stay_under_ccn_10() -> None:
    hits: list[str] = []
    for path in sorted(COMMANDS.glob("*.py")):
        if path.name.startswith("_") or path.name in {"result.py", "util.py"}:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "run":
                ccn = _ccn(node)
                if ccn > 10:
                    hits.append(f"{path.name}:run CCN={ccn}")
    assert hits == []
