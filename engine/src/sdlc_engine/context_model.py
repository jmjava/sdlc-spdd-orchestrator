"""Full agent-context graph model — every capability as a first-class kind.

This is the capability inventory the SQLite schema + ContextStore must cover
before the cleanup program is complete enough for integration → main.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Iterable

# Capability kinds that must appear in the relational/graph model.
CONTEXT_KINDS = frozenset(
    {
        "analysis",
        "review",
        "sync",
        "retro",
        "progress",
        "metric",
        "session",
        "decision",
        "pitfall",
        "pattern",
        "memory",
        "prompt",
        "playbook",
        "harness",
        "extension",
        "domain",
        "phase_ref",
        "requirement_mirror",
        "canvas_mirror",
    }
)

# Legacy agent-context/features/<WORK-ID>/ filenames → kind
FEATURE_MIRROR_KIND = {
    "analysis-context.md": "analysis",
    "progress-log.md": "progress",
    "review.md": "review",
    "sync-log.md": "sync",
    "retro.md": "retro",
    "requirement.md": "requirement_mirror",
    "reasons-canvas.md": "canvas_mirror",
}

# Stay-set governance dirs (canonical, not mirrors)
GOVERNANCE_GLOBS = (
    ("spdd/analysis", "analysis", "*-analysis.md"),
    ("spdd/reviews", "review", "*-review.md"),
    ("spdd/sync", "sync", "*.md"),
)

NODE_ENTRY = "entry"
NODE_KEYWORD = "keyword"
NODE_PHASE_REF = "phase_ref"
NODE_FACT = "fact"

REL_PHASE = "phase"
REL_KEYWORD = "keyword"


def stable_id(*parts: str) -> str:
    raw = "|".join(p.strip() for p in parts if p is not None)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"ce_{digest}"


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


def work_id_from_name(name: str) -> str:
    """Best-effort Work ID from a filename stem."""
    stem = Path(name).stem
    # e.g. FEAT-005-canvas-readiness-indicators-analysis
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
    # session style: 20260807T210856Z-SPIKE-003-...-sync
    m = re.match(
        r"^\d{8}T\d{6}Z-(.+?)(?:-(?:sync|retro|code|plan|analysis|review))?$",
        stem,
    )
    if m:
        return m.group(1)
    return stem


def iter_code_areas(text: str) -> Iterable[str]:
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("- "):
            area = s[2:].strip()
            if area:
                # Keep left side before em-dash commentary when present
                area = area.split(" — ")[0].split(" - ")[0].strip()
                yield area


def capability_matrix() -> list[dict[str, str]]:
    """Human-readable matrix of kinds the model must support."""
    return [
        {"kind": "analysis", "sources": "spdd/analysis + feature analysis-context"},
        {"kind": "review", "sources": "spdd/reviews + feature review.md"},
        {"kind": "sync", "sources": "spdd/sync + feature sync-log.md"},
        {"kind": "retro", "sources": "feature retro.md + project-memory"},
        {"kind": "progress", "sources": "feature progress-log.md"},
        {"kind": "metric", "sources": "context-index + prompt-optimization-log"},
        {"kind": "session", "sources": ".sdlc/sessions + legacy agent-context/sessions"},
        {"kind": "decision", "sources": "lessons + architecture-decisions"},
        {"kind": "pitfall", "sources": "lessons + known-pitfalls"},
        {"kind": "pattern", "sources": "lessons + reusable-patterns"},
        {"kind": "memory", "sources": "project-memory facts"},
        {"kind": "prompt", "sources": "prompt-optimization-log"},
        {"kind": "playbook", "sources": "agent-context/playbooks"},
        {"kind": "harness", "sources": "agent-context/harness"},
        {"kind": "extension", "sources": "agent-context/extensions"},
        {"kind": "domain", "sources": "domain-index keywords"},
        {"kind": "phase_ref", "sources": "phase-index catalog"},
        {"kind": "requirement_mirror", "sources": "legacy feature requirement.md"},
        {"kind": "canvas_mirror", "sources": "legacy feature reasons-canvas.md"},
    ]


def assert_kinds_covered(present_kinds: set[str]) -> list[str]:
    """Return missing CONTEXT_KINDS (empty means full coverage)."""
    return sorted(CONTEXT_KINDS - present_kinds)


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
