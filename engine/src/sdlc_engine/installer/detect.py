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


ASSISTANT_MARKERS = {
    "cursor": ".cursor/commands/sdlc-spdd-init.md",
    "copilot": ".github/prompts/sdlc-spdd-init.prompt.md",
    "claude": ".claude/commands/sdlc-spdd-init.md",
}


def _present(root: Path, rels: tuple[str, ...]) -> list[str]:
    return [rel for rel in rels if (root / rel).exists()]


def _mode(exists: bool, unsupported: list[str], markers: list[str]) -> tuple[str, str]:
    if not exists:
        return "missing", "create"
    if unsupported:
        # Matches upgrade-project.sh: any pre-v3 path blocks upgrade until removed.
        return "unsupported", "reinit"
    if markers:
        return "upgrade", "upgrade"
    return "fresh", "install"


def detect_target(target: Path | str) -> dict[str, Any]:
    """Return install-mode diagnosis for ``target``."""
    root = Path(target).expanduser().resolve()
    exists = root.is_dir()
    markers_found = _present(root, MARKERS) if exists else []
    unsupported_found = _present(root, UNSUPPORTED_MARKERS) if exists else []
    assistants = {name: exists and (root / rel).is_file() for name, rel in ASSISTANT_MARKERS.items()}
    mode, recommendation = _mode(exists, unsupported_found, markers_found)

    return {
        "path": str(root),
        "exists": exists,
        "mode": mode,
        "recommendation": recommendation,
        "markers": markers_found,
        "unsupported_markers": unsupported_found,
        "assistants": assistants,
    }
