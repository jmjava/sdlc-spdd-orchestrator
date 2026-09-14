"""CLI entrypoint: sdlc-engine / python -m sdlc_engine."""

from __future__ import annotations

import sys

from .cli_parser import build_parser

from .commands import cmd_next, cmd_version

PASSTHROUGH_VERBS = frozenset({"capture", "complete"})


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args, extra = parser.parse_known_args(argv)
    if extra:
        if getattr(args, "command", None) in PASSTHROUGH_VERBS:
            # capture/complete forward unknown options to the session script.
            args.script_args = list(getattr(args, "script_args", None) or []) + extra
        else:
            parser.error(f"unrecognized arguments: {' '.join(extra)}")
    if getattr(args, "version", False) and not getattr(args, "command", None):
        return cmd_version(args)
    if not getattr(args, "command", None):
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
