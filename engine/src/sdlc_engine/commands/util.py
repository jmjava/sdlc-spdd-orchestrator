"""Shared CLI helpers that stay import-light."""

from __future__ import annotations

import argparse

from ..project import Project


def project_from(args: argparse.Namespace) -> Project:
    return Project.resolve(getattr(args, "root", None))


def arg_str(args: argparse.Namespace, name: str, default: str = "") -> str:
    """Optional string option. A missing attribute, None, or "" all give default."""
    return getattr(args, name, None) or default


def arg_int(args: argparse.Namespace, name: str, default: int) -> int:
    """Optional integer option, tolerating a missing attribute or None."""
    return int(getattr(args, name, None) or default)


def arg_flag(args: argparse.Namespace, name: str) -> bool:
    """store_true option, tolerating a missing attribute."""
    return bool(getattr(args, name, False))


def arg_list(args: argparse.Namespace, name: str) -> list[str]:
    """Comma-separated option as trimmed, non-empty parts."""
    return [part.strip() for part in arg_str(args, name).split(",") if part.strip()]
