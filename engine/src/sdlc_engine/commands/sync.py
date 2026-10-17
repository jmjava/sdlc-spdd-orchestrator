"""sdlc-engine sync."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    sy = sub.add_parser("sync", help="Sync workflow state from artifacts")
    sy.add_argument("--work-id")
    sy.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..workflow import WorkflowEngine

    state = WorkflowEngine(project_from(args)).sync(args.work_id)
    return CommandResult.ok(f"Synced {state.work_id} -> phase {state.phase}")
