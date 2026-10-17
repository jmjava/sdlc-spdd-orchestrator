"""sdlc-engine quick."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    qk = sub.add_parser(
        "quick",
        help="Start a LOCAL-* offline session from intent (zero ceremony)",
    )
    qk.add_argument("intent", help="One-line why this scratch work exists")
    qk.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..local_sessions import LocalSessionService

    intent = (args.intent or "").strip()
    if not intent:
        return CommandResult.error("quick requires an intent string", code=2)
    session = LocalSessionService(project_from(args)).start(intent=intent, title=intent)
    lines = (
        f"Started local session {session.id}",
        f"Pointer set. Artifacts: .sdlc/local-sessions/{session.id}/",
        "Brief: .sdlc/current-local-session.md",
        'This work stays offline until: ./scripts/sdlc.sh local promote --type feature --name "..."',
    )
    return CommandResult.ok("\n".join(lines))
