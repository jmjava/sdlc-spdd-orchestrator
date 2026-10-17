"""sdlc-engine version."""

from __future__ import annotations

import argparse

from .result import CommandResult


def register(sub: argparse._SubParsersAction) -> None:
    sub.add_parser("version", help="Print version").set_defaults(func=run)


def run(_: argparse.Namespace) -> CommandResult:
    from .. import __version__

    return CommandResult.ok(__version__)
