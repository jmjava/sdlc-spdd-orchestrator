# SDLC-SPDD Copilot Instructions

Use these instructions for every GitHub Copilot Chat request in this workspace.

## Operating Model

This repository uses SDLC-SPDD: a software delivery lifecycle backed by REASONS Canvas design contracts.

Default lifecycle:

    Initialize -> Plan -> Architect -> Code -> Review -> Retro -> Sync

Preserve context by reading relevant artifacts before answering:

- `requirements/`
- `spdd/canvas/`
- `spdd/tasks/`
- `spdd/reviews/`
- `spdd/sync/`
- `agent-context/memory/`
- `agent-context/features/`
- `agent-context/harness/`

## Work Rules

- Use a Work ID for each unit of work, such as `FEAT-001-order-status-api`.
- Prefer prefixes: FEAT, BUG, REF, SPIKE, DOC, TEST, CHORE.
- Planning, architecture, retro, and sync requests must not modify application source code unless explicitly requested.
- Coding requests should implement exactly one approved operation from the canvas.
- Follow the canvas sections: Requirements, Entities, Approach, Structure, Operations, Norms, Safeguards.
- Update progress, review, retro, and sync artifacts when the active SDLC skill calls for it.
- Preserve useful project memory in `agent-context/memory/`.
- Ask clarifying questions only when needed to prevent incorrect work; otherwise state assumptions in the canvas or progress log.
- For behavior or requirement changes, update the REASONS Canvas before changing code.
- For non-behavioral refactors, review the code change and then sync the canvas back to implementation reality.

## Context-Preserving Questions

When the user asks a question, answer using the current Work ID and relevant artifacts when available. If a Work ID is not provided, ask for it or infer it from the active files and say what you inferred.

Good question patterns:

    For FEAT-001, read @spdd/canvas/FEAT-001-order-status-api.md and answer: what operation should I do next?

    For BUG-003, compare @agent-context/features/BUG-003/progress-log.md with the current diff. What context am I missing before coding?

    Using the current canvas and @agent-context/memory/known-pitfalls.md, what risks should I check before review?
