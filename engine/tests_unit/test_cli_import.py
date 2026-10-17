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


FUNC_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _own_nodes(func: ast.AST) -> list[ast.AST]:
    """Nodes belonging to func, excluding nested def bodies (lizard scores those apart)."""
    own: list[ast.AST] = []
    stack: list[ast.AST] = list(ast.iter_child_nodes(func))
    while stack:
        node = stack.pop()
        if isinstance(node, FUNC_DEFS):
            continue
        own.append(node)
        stack.extend(ast.iter_child_nodes(node))
    return own


def _ccn(func: ast.AST) -> int:
    """Mirror lizard's Python conditions: if/elif/for/while/except/finally/and/or."""
    count = 1
    for node in _own_nodes(func):
        if isinstance(node, (ast.If, ast.IfExp, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler)):
            count += 1
        elif isinstance(node, ast.Try) and node.finalbody:
            count += 1
        elif isinstance(node, ast.comprehension):
            count += 1 + len(node.ifs)
        elif isinstance(node, ast.BoolOp):
            count += max(0, len(node.values) - 1)
    return count


def test_no_cmd_star_function_exceeds_ccn_10() -> None:
    hits: list[str] = []
    for path in sorted(ENGINE_SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, FUNC_DEFS) and node.name.startswith("cmd_"):
                ccn = _ccn(node)
                if ccn > 10:
                    hits.append(f"{path.name}:{node.name} CCN={ccn}")
    assert hits == []


def test_command_module_functions_stay_under_ccn_10() -> None:
    """Every function in commands/, not just run(): scripts/check-complexity.py scores them all."""
    hits: list[str] = []
    for path in sorted(COMMANDS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, FUNC_DEFS):
                ccn = _ccn(node)
                if ccn > 10:
                    hits.append(f"{path.name}:{node.name} CCN={ccn}")
    assert hits == []


def test_ccn_proxy_matches_lizard_conditions() -> None:
    """Guard the proxy itself: ternaries, comprehensions, and finally are lizard conditions."""
    source = """
def f(a, b, items):
    xs = [i for i in items if i and not b]
    y = a if b else 0
    try:
        z = 1
    except ValueError:
        z = 2
    finally:
        pass
    return xs, y, z
"""
    func = ast.parse(source).body[0]
    # 1 base + 2 comprehension (for, if) + 1 and + 1 ternary + 1 except + 1 finally
    assert _ccn(func) == 7


def test_ccn_proxy_scores_nested_defs_separately() -> None:
    source = """
def outer(items):
    def inner(x):
        return x if x else 0

    return [inner(i) for i in items]
"""
    outer = ast.parse(source).body[0]
    inner = outer.body[0]
    assert _ccn(outer) == 2
    assert _ccn(inner) == 2
