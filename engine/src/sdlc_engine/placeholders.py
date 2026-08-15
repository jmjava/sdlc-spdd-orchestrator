"""Sentinel values used in milestone/canvas link fields.

Planning docs often leave ``TBD`` / ``TODO`` / ``NONE`` / ``N/A`` in Jira
and GitHub slots. Treat them as empty so sync/sunset do not persist junk.
"""

from __future__ import annotations

PLACEHOLDER_TOKENS = frozenset({"TBD", "TODO", "NONE", "N/A"})


def is_placeholder(raw: str | None) -> bool:
    text = (raw or "").strip()
    return not text or text.upper() in PLACEHOLDER_TOKENS
