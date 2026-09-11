"""Phase order, gates, and recommended assistant commands."""

from __future__ import annotations

PHASE_ORDER: tuple[str, ...] = (
    "init",
    "analysis",
    "plan",
    "architect",
    "code",
    "api-test",
    "review",
    "prompt-update",
    "retro",
    "sync",
)

GATE_LABELS: dict[str, str] = {
    "requirement_documented": "Requirement documented",
    "canvas_exists": "REASONS Canvas exists",
    "architect_review": "Architect review completed (advisory)",
    "operations_task_sized": "Operations are task-sized (advisory)",
    "code_maps_to_ops": "Code changes map to approved operations",
    "tests_updated": "Tests added or updated (advisory)",
    "review_completed": "Review completed",
    "safeguards_checked": "Safeguards checked",
    "retro_completed": "Retro completed",
    "canvas_synced": "Canvas synced with implementation (advisory)",
}

GATE_NAMES: tuple[str, ...] = tuple(GATE_LABELS.keys())

# Gates whose labels must include "(advisory)" because gate_check does not
# enforce them. Keep in sync with GATE_LABELS and workflow.gate_check.
ADVISORY_GATES: frozenset[str] = frozenset(
    {
        "architect_review",
        "operations_task_sized",
        "tests_updated",
        "canvas_synced",
    }
)

ENFORCED_GATES: frozenset[str] = frozenset(GATE_NAMES) - ADVISORY_GATES


def phase_index(phase: str) -> int:
    try:
        return PHASE_ORDER.index(phase)
    except ValueError as exc:
        raise ValueError(f"unknown phase: {phase}") from exc


def next_phase(phase: str) -> str | None:
    idx = phase_index(phase)
    if idx + 1 >= len(PHASE_ORDER):
        return None
    return PHASE_ORDER[idx + 1]


def valid_phase(phase: str) -> bool:
    return phase in PHASE_ORDER


def recommended_command(phase: str, work_id: str = "", operation: str = "") -> str:
    wid = work_id or "<WORK-ID>"
    mapping = {
        "init": f"/sdlc-spdd-init @requirements/ @ROADMAP.md",
        "analysis": f"/sdlc-spdd-analysis @requirements/milestones/{wid}.md",
        "plan": f"/sdlc-spdd-plan @requirements/milestones/{wid}.md @ROADMAP.md",
        "architect": f"/sdlc-spdd-architect @spdd/canvas/{wid}.md",
        "code": (
            f"/sdlc-spdd-code @spdd/canvas/{wid}.md operation {operation}"
            if operation
            else f"/sdlc-spdd-code @spdd/canvas/{wid}.md"
        ),
        "api-test": f"/sdlc-spdd-api-test @spdd/canvas/{wid}.md",
        "review": f"/sdlc-spdd-review @spdd/canvas/{wid}.md",
        "prompt-update": f"/sdlc-spdd-prompt-update @spdd/canvas/{wid}.md",
        "retro": f"/sdlc-spdd-retro @spdd/canvas/{wid}.md",
        "sync": f"/sdlc-spdd-sync @spdd/canvas/{wid}.md",
    }
    return mapping.get(phase, f"/sdlc-spdd-whereami")


def gates_for_phase(phase: str) -> tuple[str, ...]:
    """Gates that should be considered open/closed for a phase (simplified v2)."""
    if phase in {"init", "analysis"}:
        return ("requirement_documented",)
    if phase == "plan":
        return ("requirement_documented", "canvas_exists")
    if phase == "architect":
        return ("requirement_documented", "canvas_exists", "architect_review", "operations_task_sized")
    if phase in {"code", "api-test"}:
        return (
            "requirement_documented",
            "canvas_exists",
            "architect_review",
            "operations_task_sized",
            "code_maps_to_ops",
            "tests_updated",
        )
    if phase == "review":
        return ("review_completed", "safeguards_checked")
    if phase == "retro":
        return ("retro_completed",)
    if phase in {"prompt-update", "sync"}:
        return ("canvas_synced",)
    return ()


def advisory_gates_for_phase(phase: str) -> tuple[str, ...]:
    """Advisory GATE_LABELS rows for ``phase`` that ``gate_check`` never runs."""
    return tuple(name for name in gates_for_phase(phase) if name in ADVISORY_GATES)


def format_advisory_gate_rows(phase: str) -> list[str]:
    """Human rows for ``sdlc.sh gate``: advisory labels that did not run."""
    return [f"  ~ {GATE_LABELS[name]} (did not run)" for name in advisory_gates_for_phase(phase)]
