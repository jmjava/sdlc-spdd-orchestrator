"""CLI entrypoint: sdlc-engine / python -m sdlc_engine."""

from __future__ import annotations

import argparse
import sys

from .cli_parser import build_parser

from .commands import cmd_next, cmd_version

PASSTHROUGH_VERBS = frozenset({"capture", "complete"})


def _parse(parser: argparse.ArgumentParser, argv: list[str]) -> argparse.Namespace:
    """Parse argv; capture/complete forward unknown options to the session script."""
    args, extra = parser.parse_known_args(argv)
    if not extra:
        return args
    if getattr(args, "command", None) not in PASSTHROUGH_VERBS:
        parser.error(f"unrecognized arguments: {' '.join(extra)}")
    args.script_args = list(getattr(args, "script_args", None) or []) + extra
    return args


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = _parse(build_parser(), argv)
    if not getattr(args, "command", None):
        if getattr(args, "version", False):
            return cmd_version(args)
        # default to next for parity with sdlc.sh
        args.command = "next"
        args.func = cmd_next
    try:
        return int(args.func(args))
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"sdlc-engine: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
