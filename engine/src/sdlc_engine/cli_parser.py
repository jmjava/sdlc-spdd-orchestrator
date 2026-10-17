"""Argparse surface for sdlc-engine. Command modules load inside _register_subcommands()."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-engine",
        description="SDLC-SPDD Python orchestration engine (v2)",
    )
    p.add_argument(
        "--root",
        "--target",
        dest="root",
        help="Project root (default: SDLC_ROOT or git toplevel). --target is an alias.",
    )
    p.add_argument("--version", action="store_true", help="Print engine version")
    _register_subcommands(p.add_subparsers(dest="command"))
    return p


def _register_subcommands(sub: argparse._SubParsersAction) -> None:
    from .commands.advance import register as register_advance
    from .commands.archive import register as register_archive
    from .commands.claim import register as register_claim
    from .commands.commit_message import register as register_commit_message
    from .commands.context import register as register_context
    from .commands.db import register as register_db
    from .commands.gate import register as register_gate
    from .commands.installer import register as register_installer
    from .commands.issues import register as register_issues
    from .commands.links import register as register_links
    from .commands.list_shelved import register as register_list_shelved
    from .commands.list_work import register as register_list_work
    from .commands.local import register as register_local
    from .commands.next import register as register_next
    from .commands.pointer import register as register_pointer
    from .commands.quick import register as register_quick
    from .commands.quiet_status import register as register_quiet_status
    from .commands.release import register as register_release
    from .commands.resume import register as register_resume
    from .commands.shelf import register as register_shelf
    from .commands.shell import register as register_shell
    from .commands.skip import register as register_skip
    from .commands.status import register as register_status
    from .commands.sunset import register as register_sunset
    from .commands.sync import register as register_sync
    from .commands.sync_links import register as register_sync_links
    from .commands.sync_roadmap import register as register_sync_roadmap
    from .commands.sync_team import register as register_sync_team
    from .commands.team import register as register_team
    from .commands.template import register as register_template
    from .commands.version import register as register_version
    from .commands.viewer import register as register_viewer
    from .commands.work import register as register_work

    for register in (
        register_next,
        register_quick,
        register_status,
        register_resume,
        register_advance,
        register_gate,
        register_skip,
        register_shelf,
        register_sync,
        register_list_shelved,
        register_claim,
        register_links,
        register_sync_links,
        register_sync_roadmap,
        register_issues,
        register_local,
        register_work,
        register_commit_message,
        register_sunset,
        register_db,
        register_release,
        register_team,
        register_list_work,
        register_sync_team,
        register_archive,
        register_pointer,
        register_context,
        register_quiet_status,
        register_shell,
        register_version,
        register_viewer,
        register_installer,
        register_template,
    ):
        register(sub)
