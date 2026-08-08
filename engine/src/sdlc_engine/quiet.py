"""Quiet / product-test mode (#91) — suppress T## dogfood gravity."""

from __future__ import annotations

import os
from pathlib import Path

from .project import Project


def is_quiet(
    project: Project | None = None,
    *,
    quiet_flag: bool = False,
    env: dict[str, str] | None = None,
) -> bool:
    """True when SDLC_QUIET=1, --quiet, or agent-context/harness/quiet-mode.md exists."""
    if quiet_flag:
        return True
    environ = env if env is not None else os.environ
    if str(environ.get("SDLC_QUIET", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return True
    root = (project or Project.resolve()).root
    return (root / "agent-context" / "harness" / "quiet-mode.md").is_file()


def quiet_resume_blurb(*, guide_live: bool = False) -> str:
    """Product-test oriented resume text without T## gravity."""
    if guide_live:
        return (
            "Quiet/product-test mode: retrieve context via "
            "`sdlc-engine context retrieve` / SQLite / Guide SPDD projection. "
            "Do not inject next canvas T## operation gravity."
        )
    return (
        "Quiet mode: load resolved context and continue the product task. "
        "Skip recommended /sdlc-spdd-* T## dogfood commands unless explicitly requested."
    )
