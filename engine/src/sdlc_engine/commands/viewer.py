"""sdlc-engine viewer."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    vw = sub.add_parser(
        "viewer",
        help="ADF WYSIWYG ticket viewer (Flask; requires optional [viewer] extra)",
    )
    vw.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1)")
    vw.add_argument("--port", type=int, default=5050)
    vw.add_argument("--debug", action="store_true")
    vw.add_argument("--lan", action="store_true", help="Bind 0.0.0.0 for LAN access (opt-in)")
    vw.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    try:
        from ..viewer.app import run_viewer
    except ImportError as exc:
        return CommandResult.error(
            "viewer requires Flask. Install with: python3 -m pip install -e './engine[viewer]'\n"
            + str(exc)
        )
    project = project_from(args)
    host = "0.0.0.0" if getattr(args, "lan", False) else args.host
    run_viewer(project.root, host=host, port=args.port, debug=bool(args.debug))
    return CommandResult()
