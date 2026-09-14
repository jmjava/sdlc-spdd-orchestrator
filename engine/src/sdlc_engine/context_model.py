"""Context capability model (storage v3).

The committed memory surface is one ledger (``spdd/memory/lessons.jsonl``)
holding the pared-down, highest-value kinds. Governance documents
(analysis/review/sync) stay first-class git artifacts and are indexed as
entries. Everything else is runtime state (``.sdlc/`` or SQLite-only).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

# Ledger kinds — committed memory records.
LEDGER_KINDS = frozenset({"decision", "pitfall", "pattern", "session", "analysis"})

# Governance entry kinds — indexed from stay-set documents.
GOVERNANCE_KINDS = frozenset({"analysis", "review", "sync"})

# The full capability set the SQLite cache must cover.
CONTEXT_KINDS = frozenset(LEDGER_KINDS | GOVERNANCE_KINDS)

# Stay-set governance dirs (canonical documents, indexed as entries).
GOVERNANCE_GLOBS = (
    ("spdd/analysis", "analysis", "*-analysis.md"),
    ("spdd/reviews", "review", "*-review.md"),
    ("spdd/sync", "sync", "*.md"),
)

NODE_ENTRY = "entry"
NODE_KEYWORD = "keyword"

REL_KEYWORD = "keyword"


def stable_id(*parts: str) -> str:
    raw = "|".join(p.strip() for p in parts if p is not None)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"ce_{digest}"


def work_id_from_name(name: str) -> str:
    """Best-effort Work ID from a filename stem."""
    stem = Path(name).stem
    for suffix in (
        "-analysis",
        "-review",
        "-research",
        "-sync",
        "-retro",
        "-code",
        "-plan",
    ):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    m = re.match(
        r"^\d{8}T\d{6}Z-(.+?)(?:-(?:sync|retro|code|plan|analysis|review))?$",
        stem,
    )
    if m:
        return m.group(1)
    return stem


def capability_matrix() -> list[dict[str, str]]:
    """Human-readable matrix of kinds the model must support (v3)."""
    return [
        {"kind": "decision", "sources": "lessons.jsonl (accepted + staged)"},
        {"kind": "pitfall", "sources": "lessons.jsonl (accepted + staged)"},
        {"kind": "pattern", "sources": "lessons.jsonl (accepted + staged)"},
        {"kind": "session", "sources": "lessons.jsonl key points (full briefs stay hot in .sdlc)"},
        {"kind": "analysis", "sources": "lessons.jsonl records + spdd/analysis documents"},
        {"kind": "review", "sources": "spdd/reviews documents"},
        {"kind": "sync", "sources": "spdd/sync documents"},
    ]


def assert_kinds_covered(present_kinds: set[str]) -> list[str]:
    """Return missing CONTEXT_KINDS (empty means full coverage)."""
    return sorted(CONTEXT_KINDS - present_kinds)
