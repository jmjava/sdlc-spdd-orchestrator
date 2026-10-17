"""sdlc-engine installer / console / dashboard."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def _add_console_parser(sub: argparse._SubParsersAction, name: str, help_text: str) -> None:
    inst = sub.add_parser(name, help=help_text)
    inst.add_argument(
        "--target",
        default=None,
        help="Default target project path shown in the UI (default: --root / cwd)",
    )
    inst.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1)")
    inst.add_argument("--port", type=int, default=5051)
    inst.add_argument("--debug", action="store_true")
    inst.add_argument("--lan", action="store_true", help="Bind 0.0.0.0 for LAN access (opt-in)")
    inst.add_argument("--no-browser", action="store_true", help="Do not open a browser tab automatically")
    inst.add_argument(
        "--playground",
        action="store_true",
        help="Seed a disposable SPDD tree and open the console against it (no consumer install)",
    )
    inst.add_argument(
        "--playground-dir",
        default=None,
        help="Playground dest (default: <orchestrator>/.sdlc/console-playground)",
    )
    inst.set_defaults(func=run)


def register(sub: argparse._SubParsersAction) -> None:
    _add_console_parser(
        sub,
        "installer",
        "EXPERIMENTAL ops console: install/upgrade, SQLite, rollback, Guide "
        "(Flask; [viewer] extra) — not a stable consumer install path",
    )
    _add_console_parser(sub, "console", "EXPERIMENTAL alias for installer — ops console UI")
    _add_console_parser(sub, "dashboard", "EXPERIMENTAL alias for installer — ops console UI")


def run(args: argparse.Namespace) -> CommandResult:
    try:
        from ..installer.app import run_installer
    except ImportError as exc:
        return CommandResult.error(
            "installer/console requires Flask. Install with: "
            "python3 -m pip install -e './engine[viewer]'\n" + str(exc)
        )
    project = project_from(args)
    host = "0.0.0.0" if getattr(args, "lan", False) else args.host
    target = getattr(args, "target", None) or str(project.root)
    if getattr(args, "playground", False):
        from ..installer.playground import materialize_playground

        dest = materialize_playground(getattr(args, "playground_dir", None))
        target = str(dest)
        stdout = f"Playground seeded at {dest}\n"
    else:
        stdout = ""
    run_installer(
        target,
        host=host,
        port=args.port,
        debug=bool(args.debug),
        open_browser=not bool(getattr(args, "no_browser", False)),
    )
    return CommandResult(stdout=stdout)
