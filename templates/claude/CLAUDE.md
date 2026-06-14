# SDLC-SPDD Claude Code Instructions

Use these instructions for every Claude Code request in this workspace.

## Operating Model

This repository uses SDLC-SPDD: SDLC Agents-style lifecycle roles backed by SPDD REASONS Canvas design contracts.

Default lifecycle:

    Initialize -> Plan -> Architect -> Code -> Review -> Retro -> Sync

The matching slash commands live in `.claude/commands/`:

    /sdlc-spdd-init
    /sdlc-spdd-plan
    /sdlc-spdd-architect
    /sdlc-spdd-code
    /sdlc-spdd-review
    /sdlc-spdd-prompt-update
    /sdlc-spdd-retro
    /sdlc-spdd-sync

Preserve context by reading relevant artifacts before answering:

- `requirements/`
- `spdd/canvas/`
- `spdd/tasks/`
- `spdd/reviews/`
- `spdd/sync/`
- `ROADMAP.md`
- `milestone-*.md`
- `session-notes/`
- `agent-context/memory/`
- `agent-context/features/`
- `agent-context/harness/`

Use progressive disclosure: load only the artifacts relevant to the current Work ID, phase, and operation.

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
- Treat `#SkillName` markers as explicit skill requests and `!SkillName` markers as exclusions. Record selected skills in the canvas or progress log when relevant.

## Context-Preserving Questions

When the user asks a question, answer using the current Work ID and relevant artifacts when available. If a Work ID is not provided, ask for it or infer it from the active files and say what you inferred.

Good question patterns:

    For FEAT-001, read @spdd/canvas/FEAT-001-order-status-api.md and answer: what operation should I do next?

    For BUG-003, compare @agent-context/features/BUG-003/progress-log.md with the current diff. What context am I missing before coding?

    Using the current canvas and @agent-context/memory/known-pitfalls.md, what risks should I check before review?
