"""CLI entrypoint: sdlc-engine / python -m sdlc_engine."""

from __future__ import annotations

import sys

from .cli_commands import cmd_next, cmd_version
from .cli_parser import build_parser

# Keep handler names importable from sdlc_engine.cli for compatibility.
from .cli_commands import (  # noqa: F401
    _project,
    cmd_advance,
    cmd_agent_context,
    cmd_archive,
    cmd_claim,
    cmd_commit_message,
    cmd_context,
    cmd_db,
    cmd_gate,
    cmd_installer,
    cmd_issues,
    cmd_links,
    cmd_list_shelved,
    cmd_list_work,
    cmd_local,
    cmd_next,
    cmd_pointer,
    cmd_quick,
    cmd_release,
    cmd_resume,
    cmd_shelf,
    cmd_shell,
    cmd_skip,
    cmd_status,
    cmd_storage,
    cmd_sunset,
    cmd_sync,
    cmd_sync_links,
    cmd_sync_roadmap,
    cmd_sync_team,
    cmd_team,
    cmd_template,
    cmd_version,
    cmd_viewer,
    cmd_work,
)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
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
