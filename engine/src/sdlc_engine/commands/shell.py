"""sdlc-engine shell."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    shell = sub.add_parser("shell", help="Run a v1 scripts/*.sh via bridge")
    shell.add_argument("script")
    shell.add_argument("script_args", nargs=argparse.REMAINDER)
    shell.set_defaults(func=run)


def _candidates(root: Path, script: str) -> list[Path]:
    names = [script] if script.endswith(".sh") else [script, f"{script}.sh"]
    directories = [root / "scripts", root / "sdlc-spdd" / "scripts"]
    return [directory / name for directory in directories for name in names]


def _resolve(root: Path, script: str) -> Path | None:
    for candidate in _candidates(root, script):
        if candidate.is_file():
            return candidate
    return None


def run(args: argparse.Namespace) -> CommandResult:
    root = project_from(args).root
    script = _resolve(root, args.script)
    if script is None:
        return CommandResult.error(f"shell bridge: script not found: {args.script}")
    return CommandResult(exit_code=subprocess.call([str(script), *args.script_args], cwd=root))
