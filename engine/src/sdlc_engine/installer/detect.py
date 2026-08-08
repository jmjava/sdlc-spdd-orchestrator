"""Detect whether a target path needs a fresh install or an upgrade."""

from __future__ import annotations

from pathlib import Path
from typing import Any


MARKERS = (
    # storage v3 single-folder home
    "sdlc-spdd/scripts/sdlc.sh",
    "sdlc-spdd/spdd/memory/lessons.jsonl",
    "spdd/memory/lessons.jsonl",
    "scripts/sdlc-spdd/sdlc.sh",
    ".cursor/commands/sdlc-spdd-init.md",
    ".github/prompts/sdlc-spdd-init.prompt.md",
    ".claude/commands/sdlc-spdd-init.md",
)

# Pre-v3 sprawled layouts, detected only so upgrade (and storage migrate)
# can be recommended for old installs.
LEGACY_MARKERS = (
    "agent-context/sdlc-workflow.sh",
    "agent-context/work-registry.tsv",
)


def detect_target(target: Path | str) -> dict[str, Any]:
    """Return install-mode diagnosis for ``target``."""
    root = Path(target).expanduser().resolve()
    exists = root.is_dir()
    markers_found: list[str] = []
    if exists:
        for rel in (*MARKERS, *LEGACY_MARKERS):
            if (root / rel).exists():
                markers_found.append(rel)

    has_cursor = (root / ".cursor/commands/sdlc-spdd-init.md").is_file() if exists else False
    has_copilot = (root / ".github/prompts/sdlc-spdd-init.prompt.md").is_file() if exists else False
    has_claude = (root / ".claude/commands/sdlc-spdd-init.md").is_file() if exists else False

    if not exists:
        mode = "missing"
        recommendation = "create"
    elif markers_found:
        mode = "upgrade"
        recommendation = "upgrade"
    else:
        mode = "fresh"
        recommendation = "install"

    return {
        "path": str(root),
        "exists": exists,
        "mode": mode,
        "recommendation": recommendation,
        "markers": markers_found,
        "assistants": {
            "cursor": has_cursor,
            "copilot": has_copilot,
            "claude": has_claude,
        },
    }
