"""sdlc-engine pointer."""

from __future__ import annotations

import argparse

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    ptr = sub.add_parser("pointer", help="Pointer get/set/reset")
    ptr.add_argument("pointer_cmd", choices=["get", "set", "reset"])
    ptr.add_argument("work_id", nargs="?")
    ptr.set_defaults(func=run)


def run(args: argparse.Namespace) -> CommandResult:
    from ..pointer import PointerError, PointerStore

    store = PointerStore(project_from(args))
    try:
        if args.pointer_cmd == "get":
            return CommandResult.ok(str(store.get()))
        if args.pointer_cmd == "set":
            store.set(args.work_id)
            return CommandResult.ok(f"pointer set to: {args.work_id}")
        if args.pointer_cmd == "reset":
            store.reset()
            return CommandResult.ok("pointer cleared")
    except PointerError as exc:
        return CommandResult.error(str(exc), code=2)
    return CommandResult(exit_code=2)
