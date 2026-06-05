# Design Decisions

## SDLC Agents own lifecycle, SPDD owns prompt governance

SDLC Agents patterns define the lifecycle phases, specialized responsibilities, progressive context loading, architecture-first handoffs, and retro learning loop. SPDD defines the governed prompt artifact model through REASONS Canvas, prompt-update, review, and sync.

The hybrid keeps these concerns separate:

- SDLC Agents answer who acts, when they act, and which context they should load.
- SPDD answers what artifact governs the work and how prompt/code drift is reconciled.
- This scaffold answers how those practices are installed and invoked from Cursor or GitHub Copilot.

## Multi-assistant Markdown adapters

The first version is templates and scripts, not a compiled CLI or agent runtime. Cursor commands and GitHub Copilot prompt files are adapters over the same lifecycle semantics.

## Duplicate canvas copies

Feature workspace and `spdd/canvas/` hold the same content in MVP. Sync tooling reconciles drift.

## Safe installation

Scripts never overwrite existing files unless `--force` is passed. `--dry-run` is supported for init.

## Markdown as primary format

All contracts, memory, and commands are inspectable Markdown files.

## SDLC Agents compatibility boundary

This project adopts SDLC Agents lifecycle and context-engineering principles, but does not yet implement the full upstream runtime, dynamic skill loader, or extension loader. Teams can still use SDLC Agents-style skills by referencing `#SkillName` and storing reusable guidance in `agent-context/playbooks/`, `agent-context/memory/`, or a project-local `agent-context/extensions/` folder.
