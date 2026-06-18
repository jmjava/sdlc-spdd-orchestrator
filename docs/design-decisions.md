# Design Decisions

> Deep theory. For onboarding, read [Three-part operating path](three-part-operating-path.md) and the [What each part brings](README.md#what-each-part-brings-read-before-deep-theory) value guides first.

## SDLC Agents own lifecycle, SPDD owns prompt governance

SDLC Agents patterns define the lifecycle phases, specialized responsibilities, progressive context loading, architecture-first handoffs, and retro learning loop. SPDD defines the governed prompt artifact model through REASONS Canvas, prompt-update, review, and sync.

The hybrid keeps these concerns separate:

- SDLC Agents answer who acts, when they act, and which context they should load.
- SPDD answers what artifact governs the work and how prompt/code drift is reconciled.
- Roadmap, milestone, and session-note files answer where the project is going and what happened recently.
- This scaffold answers how those practices are installed, mapped, and invoked from Cursor, GitHub Copilot, or Claude Code.

## Planning narrative stays separate from SPDD contracts

`ROADMAP.md`, `milestone-*.md`, `requirements/milestones/`, and `session-notes/` are intentionally preserved as human-readable planning and narrative artifacts. Milestone checklist items map to requirement stubs under `requirements/milestones/<WORK-ID>.md`. They inform SDLC-SPDD work, but they do not replace the REASONS Canvas.

The flow is:

    ROADMAP.md / milestone-*.md / requirements/milestones/ / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

This avoids over-structuring project-level planning while still giving agents enough traceability to create Work IDs, canvases, memory, and reviews.

## Multi-assistant Markdown adapters

The first version is templates and scripts, not a compiled CLI or agent runtime. Cursor commands, GitHub Copilot prompt files, and Claude Code commands are adapters over the same lifecycle semantics.

## Duplicate canvas copies

Feature workspace and `spdd/canvas/` hold the same content in MVP. Sync tooling reconciles drift.

## Safe installation

Scripts never overwrite existing files unless `--force` is passed. `--dry-run` is supported for init.

## Agent overlays are orchestrator-only today

`templates/agent-overlays/` defines per-role overlay prompts referenced in `STARTER-SPEC.md`, but install scripts do not copy them to target projects yet. Target projects use Cursor commands, Copilot prompts, Claude Code commands, and playbooks instead. Treat overlays as future/post-MVP material unless install support is added.

## Markdown as primary format

All contracts, memory, and commands are inspectable Markdown files.

## SDLC Agents compatibility boundary

This project adopts SDLC Agents lifecycle and context-engineering principles, but does not yet implement the full upstream runtime, dynamic skill loader, or extension loader. Teams can still use SDLC Agents-style skills by referencing `#SkillName` and storing reusable guidance in `agent-context/playbooks/`, `agent-context/memory/`, or a project-local `agent-context/extensions/` folder.
