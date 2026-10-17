"""Shared CLI helpers that stay import-light."""

from __future__ import annotations

import argparse

from ..project import Project


def project_from(args: argparse.Namespace) -> Project:
    return Project.resolve(getattr(args, "root", None))
