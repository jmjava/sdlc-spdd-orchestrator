"""Context capability model (storage v3) + legacy markdown parsers.

The committed memory surface is one ledger (``spdd/memory/lessons.jsonl``)
holding the pared-down, highest-value kinds. Governance documents
(analysis/review/sync) stay first-class git artifacts and are indexed as
entries. Everything else is runtime state (``.sdlc/`` or SQLite-only).

The markdown parsing helpers below exist for the one-shot legacy migration
(``sdlc-engine storage migrate``) and are not part of the live write path.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Iterable

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


# --- legacy parsers (migration only) ---


def parse_md_table(text: str) -> list[dict[str, str]]:
    """Parse a simple GitHub-style markdown table into row dicts."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for ln in lines:
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if all(re.fullmatch(r":?-+:?", c or "") for c in cells):
            continue
        if len(cells) < len(header):
            cells.extend([""] * (len(header) - len(cells)))
        rows.append({header[i]: cells[i] for i in range(len(header))})
    return rows


def iter_code_areas(text: str) -> Iterable[str]:
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("- "):
            area = s[2:].strip()
            if area:
                area = area.split(" — ")[0].split(" - ")[0].strip()
                yield area


def extract_prompt_entries(text: str) -> list[dict[str, Any]]:
    """Split prompt-optimization-log style headed sections into entries."""
    entries: list[dict[str, Any]] = []
    blocks = re.split(r"\n(?=## )", text)
    for block in blocks:
        if not block.strip().startswith("## "):
            continue
        first, _, rest = block.partition("\n")
        title = first.lstrip("# ").strip()
        entries.append(
            {
                "title": title,
                "body": rest.strip()[:2000],
                "kind": "prompt",
            }
        )
    return entries


def extract_memory_facts(text: str) -> list[dict[str, Any]]:
    """Parse ## Recent Learnings subsections from project-memory.md."""
    facts: list[dict[str, Any]] = []
    if "## Recent Learnings" not in text:
        return facts
    section = text.split("## Recent Learnings", 1)[1]
    for m in re.finditer(
        r"###\s+(\S+)\s+-\s+(\S+)\s*\n(.*?)(?=\n### |\Z)",
        section,
        re.DOTALL,
    ):
        ts, work_id, body = m.group(1), m.group(2), m.group(3)
        phase = ""
        summary = ""
        nxt = ""
        for ln in body.splitlines():
            if ln.strip().startswith("- Phase:"):
                phase = ln.split(":", 1)[1].strip()
            elif ln.strip().startswith("- Summary:"):
                summary = ln.split(":", 1)[1].strip()
            elif ln.strip().startswith("- Next:"):
                nxt = ln.split(":", 1)[1].strip()
        facts.append(
            {
                "ts": ts,
                "work_id": work_id,
                "phase": phase,
                "summary": summary or body.strip()[:500],
                "next_step": nxt,
            }
        )
    return facts


def extract_session_history(text: str) -> list[dict[str, Any]]:
    """Parse legacy session-history.md ``### <ts> - <WORK-ID> - <phase>`` blocks."""
    sessions: list[dict[str, Any]] = []
    for m in re.finditer(
        r"(?m)^###\s+(\S+)\s+-\s+(\S+?)(?:\s+-\s+(\S+))?\s*\n(.*?)(?=^###\s+|\Z)",
        text,
        re.DOTALL,
    ):
        ts, work_id, phase, body = (
            m.group(1),
            m.group(2),
            m.group(3) or "",
            m.group(4),
        )
        summary = ""
        for ln in body.splitlines():
            if ln.strip().startswith("- Summary:"):
                summary = ln.split(":", 1)[1].strip()
                break
        sessions.append(
            {
                "ts": ts,
                "work_id": work_id,
                "phase": phase,
                "summary": summary,
                "body": body.strip()[:4000],
            }
        )
    return sessions


def extract_lesson_blocks(text: str) -> list[dict[str, Any]]:
    """Parse legacy lesson files (known-pitfalls / reusable-patterns /
    architecture-decisions and spdd lesson files) into records.

    Supports both ``## <WORK-ID> — <ts>`` blocks written by the old
    ContextStore and free-form ``## <title>`` sections.
    """
    out: list[dict[str, Any]] = []
    wid_re = r"((?:FEAT|BUG|SPIKE|REF|DOC|TEST|CHORE|LOCAL)-[A-Za-z0-9][\w.-]*)"
    for block in re.split(r"(?m)^##\s+", text):
        if not block.strip():
            continue
        first = block.splitlines()[0].strip()
        if first.startswith("#"):
            continue
        body = "\n".join(block.splitlines()[1:]).strip()
        m = re.match(rf"^{wid_re}", first)
        wid = m.group(1) if m else ""
        ts_m = re.search(r"(\d{4}-\d{2}-\d{2}(?:T[\d:]+Z)?)", first)
        area_m = re.search(r"(?m)^-\s*Area:\s*(.+)$", block)
        id_m = re.search(r"<!--\s*id:\s*([^>]+?)\s*-->", block)
        if not body and not first:
            continue
        out.append(
            {
                "work_id": wid,
                "title": first[:120],
                "body": body[:4000],
                "ts": ts_m.group(1) if ts_m else "",
                "area": area_m.group(1).strip() if area_m else "",
                "legacy_id": id_m.group(1).strip() if id_m else "",
            }
        )
    return out
