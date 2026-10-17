"""sdlc-engine next."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    sub.add_parser("next", help="Show what to do now").set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..workflow import WorkflowEngine

    return CommandResult.raw(WorkflowEngine(project_from(args)).next_text())
