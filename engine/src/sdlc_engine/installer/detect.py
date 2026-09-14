"""Detect whether a target path needs a fresh install or an upgrade."""

from __future__ import annotations

from pathlib import Path
from typing import Any


# Storage v3 single-folder home plus the adapter stubs init writes at the root.
MARKERS = (
    "sdlc-spdd/scripts/sdlc.sh",
    "sdlc-spdd/spdd/memory/lessons.jsonl",
    ".cursor/commands/sdlc-spdd-init.md",
    ".github/prompts/sdlc-spdd-init.prompt.md",
    ".claude/commands/sdlc-spdd-init.md",
)

# Pre-v3 layouts are not migrated. They are detected only so the console can
# say "unsupported layout; re-init on a clean checkout" instead of upgrading.
UNSUPPORTED_MARKERS = (
    "agent-context/sdlc-workflow.sh",
    "agent-context/work-registry.tsv",
    "scripts/sdlc-spdd/sdlc.sh",
    "spdd/memory/lessons.jsonl",
)


def detect_target(target: Path | str) -> dict[str, Any]:
    """Return install-mode diagnosis for ``target``."""
    root = Path(target).expanduser().resolve()
    exists = root.is_dir()
    markers_found = [rel for rel in MARKERS if exists and (root / rel).exists()]
    unsupported_found = [rel for rel in UNSUPPORTED_MARKERS if exists and (root / rel).exists()]

    has_cursor = (root / ".cursor/commands/sdlc-spdd-init.md").is_file() if exists else False
    has_copilot = (root / ".github/prompts/sdlc-spdd-init.prompt.md").is_file() if exists else False
    has_claude = (root / ".claude/commands/sdlc-spdd-init.md").is_file() if exists else False

    if not exists:
        mode = "missing"
        recommendation = "create"
    elif unsupported_found:
        # Matches upgrade-project.sh: any pre-v3 path blocks upgrade until removed.
        mode = "unsupported"
        recommendation = "reinit"
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
        "unsupported_markers": unsupported_found,
        "assistants": {
            "cursor": has_cursor,
            "copilot": has_copilot,
            "claude": has_claude,
        },
    }
