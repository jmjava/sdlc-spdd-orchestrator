"""CLI entrypoint: sdlc-engine / python -m sdlc_engine."""

from __future__ import annotations

import sys

from .cli_parser import build_parser
from .commands.result import CommandResult


def _emit(result: CommandResult | int) -> int:
    if isinstance(result, CommandResult):
        return result.emit()
    return int(result)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "version", False) and not getattr(args, "command", None):
        from .commands.version import run as run_version

        return _emit(run_version(args))
    if not getattr(args, "command", None):
        from .commands.next import run as run_next

        args.command = "next"
        args.func = run_next
    try:
        return _emit(args.func(args))
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"sdlc-engine: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
