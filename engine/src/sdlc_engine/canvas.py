"""REASONS Canvas helpers: Final Status and next operation inference."""

from __future__ import annotations

import re
from pathlib import Path


def final_status_text(canvas_path: Path) -> str:
    if not canvas_path.is_file():
        return ""
    text = canvas_path.read_text(encoding="utf-8")
    in_final = False
    for line in text.splitlines():
        if line.startswith("## Final Status"):
            in_final = True
            continue
        if in_final and line.startswith("## "):
            break
        if in_final and line.startswith("- Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def final_kind(canvas_path: Path) -> str:
    """Return complete | cancelled | other."""
    line = final_status_text(canvas_path).lower()
    if not line:
        return "other"
    if "cancel" in line:
        return "cancelled"
    if "complete" in line and "in progress" not in line:
        return "complete"
    return "other"


def is_archivable(canvas_path: Path) -> bool:
    return final_kind(canvas_path) in {"complete", "cancelled"}


_OP_HEADER = re.compile(r"^###\s+(T\d+)\s*[-–—:]\s*(.+)$")
_OP_STATUS = re.compile(r"^- Status:\s*(.+)$", re.IGNORECASE)
_OP_STATUS_ANY = re.compile(r"^- Status:\s*\S", re.IGNORECASE)
_YAML_READINESS = re.compile(r"^readiness:\s*(.+)$", re.IGNORECASE)
_META_READINESS = re.compile(r"^-+\s*Readiness:\s*(.+)$", re.IGNORECASE)

# Mirror scripts/lib/readiness.sh — keep these lists in sync.
READINESS_CANONICAL = (
    "needs-analysis",
    "needs-clarification",
    "needs-redesign",
    "ready-for-coding",
    "blocked",
    "reviewed",
    "complete",
)
CODING_ALLOWED_READINESS = frozenset({"ready-for-coding", "reviewed", "complete"})


def section_body(text: str, heading: str) -> str:
    """Body under ``## {heading}`` until the next ``## `` heading."""
    lines = text.splitlines()
    collecting = False
    body: list[str] = []
    needle = f"## {heading}"
    for line in lines:
        if line.startswith(needle):
            collecting = True
            continue
        if collecting and line.startswith("## "):
            break
        if collecting:
            body.append(line)
    return "\n".join(body)


def _frontmatter_readiness(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = _YAML_READINESS.match(line.strip())
        if match:
            return match.group(1).strip().strip("'\"")
    return ""


def extract_readiness_raw(text: str) -> str:
    """Structured readiness only: YAML frontmatter or Metadata ``- Readiness:``.

    A 'Ready For Coding' phrase in Sync Notes or Architecture Notes does not count.
    """
    raw = _frontmatter_readiness(text)
    if raw:
        return raw
    meta = section_body(text, "Metadata")
    for line in meta.splitlines():
        match = _META_READINESS.match(line.strip())
        if match:
            return match.group(1).strip()
    return ""


def normalize_readiness(raw: str) -> str:
    """Return a canonical readiness token, or '' if unrecognized."""
    lower = raw.strip().lower()
    lower = re.sub(r"\([^)]*\)", "", lower).strip()
    lower = re.sub(r"[\s_]+", "-", lower)
    lower = re.sub(r"[^a-z0-9-]+", "-", lower)
    lower = re.sub(r"-+", "-", lower).strip("-")
    exact = {
        "needs-analysis": "needs-analysis",
        "need-analysis": "needs-analysis",
        "needs-clarification": "needs-clarification",
        "need-clarification": "needs-clarification",
        "needs-redesign": "needs-redesign",
        "need-redesign": "needs-redesign",
        "ready-for-coding": "ready-for-coding",
        "ready-for-code": "ready-for-coding",
        "blocked": "blocked",
        "reviewed": "reviewed",
        "complete": "complete",
        "done": "complete",
        "completed": "complete",
    }
    if lower in exact:
        return exact[lower]
    if lower.startswith("ready-for-coding"):
        return "ready-for-coding"
    if lower.startswith("reviewed"):
        return "reviewed"
    if lower.startswith("complete"):
        return "complete"
    return ""


def section_has_content(text: str, heading: str) -> bool:
    """True when the section has a non-heading, non-blank line."""
    for line in section_body(text, heading).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return True
    return False


def has_operation_with_status(text: str) -> bool:
    in_ops = False
    saw_op = False
    for line in text.splitlines():
        if line.startswith("## O") or line.startswith("## Operations"):
            in_ops = True
            continue
        if in_ops and line.startswith("## ") and not line.startswith("## O"):
            break
        if not in_ops:
            continue
        if _OP_HEADER.match(line.strip()) or re.match(r"^###\s+T\d+\b", line.strip()):
            saw_op = True
            continue
        if saw_op and _OP_STATUS_ANY.match(line.strip()):
            return True
    return False


def semantic_issues(text: str, *, strict_readiness: bool = False) -> list[str]:
    """Issues for a headings-present canvas that is still semantically empty."""
    issues: list[str] = []
    if not section_has_content(text, "R - Requirements") and not section_has_content(
        text, "Requirements"
    ):
        issues.append("empty Requirements section")
    if not has_operation_with_status(text):
        issues.append("no T## operation with Status")
    if strict_readiness:
        raw = extract_readiness_raw(text)
        if raw and not normalize_readiness(raw):
            issues.append(f"unrecognized readiness {raw!r}")
    return issues


def coding_gate_issues(text: str) -> list[str]:
    """Failures that block entering the code phase (C-COMPLY semantic minima)."""
    issues = semantic_issues(text)
    raw = extract_readiness_raw(text)
    if not raw:
        issues.append(
            "missing structured Readiness field (YAML frontmatter or Metadata); "
            "a Ready For Coding phrase elsewhere does not count"
        )
        return issues
    canon = normalize_readiness(raw)
    if not canon:
        issues.append(f"unrecognized readiness {raw!r} (not Ready For Coding)")
    elif canon not in CODING_ALLOWED_READINESS:
        issues.append(f"readiness is {canon}, not Ready For Coding")
    return issues


def canvas_allows_coding(text: str) -> bool:
    return not coding_gate_issues(text)


def next_operation(canvas_path: Path) -> tuple[str, str]:
    """Return (operation_id, title) for the first incomplete Operation, else ('', '')."""
    if not canvas_path.is_file():
        return "", ""
    current_op = ""
    current_title = ""
    in_ops = False
    for line in canvas_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## O") or line.startswith("## Operations"):
            in_ops = True
            continue
        if in_ops and line.startswith("## ") and not line.startswith("## O"):
            break
        if not in_ops:
            continue
        m = _OP_HEADER.match(line.strip())
        if m:
            current_op, current_title = m.group(1), m.group(2).strip()
            continue
        if current_op:
            sm = _OP_STATUS.match(line.strip())
            if sm:
                status = sm.group(1).strip().lower()
                if "complete" not in status and "done" not in status:
                    return current_op, current_title
                current_op, current_title = "", ""
    return "", ""
