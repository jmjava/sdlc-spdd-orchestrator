"""Shared UTC timestamps used across the engine.

Twelve modules previously inlined the same ``datetime.now(timezone.utc)``
strftime. Keep one pair of formats:

- ``utc_now`` — ISO-8601 instant (``2026-08-15T02:28:00Z``)
- ``utc_stamp`` — compact filesystem-safe stamp (``20260815T022800Z``)
- ``utc_date`` — calendar day (``2026-08-15``)
"""

from __future__ import annotations

from datetime import datetime, timezone

ISO_INSTANT = "%Y-%m-%dT%H:%M:%SZ"
COMPACT_STAMP = "%Y%m%dT%H%M%SZ"
ISO_DATE = "%Y-%m-%d"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_INSTANT)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime(COMPACT_STAMP)


def utc_date() -> str:
    return datetime.now(timezone.utc).strftime(ISO_DATE)


def utc_from_timestamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(ISO_INSTANT)
