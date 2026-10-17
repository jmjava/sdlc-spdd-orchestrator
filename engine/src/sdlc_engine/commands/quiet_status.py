"""sdlc-engine quiet-status."""

from __future__ import annotations

import argparse
import json

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    aqs = sub.add_parser("quiet-status", help="Show quiet/product-test mode status")
    aqs.add_argument("--quiet", action="store_true", help="Treat as --quiet flag set")
    aqs.add_argument("--guide-live", action="store_true")
    aqs.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..quiet import is_quiet, quiet_resume_blurb

    project = project_from(args)
    quiet = is_quiet(project, quiet_flag=bool(getattr(args, "quiet", False)))
    payload = {
        "quiet": quiet,
        "blurb": quiet_resume_blurb(guide_live=bool(args.guide_live)),
        "hot_session_dir": str(project.hot_session_dir()),
        "current_session": str(project.current_session_path()),
    }
    return CommandResult.ok(json.dumps(payload, indent=2))
