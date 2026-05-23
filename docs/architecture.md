# Architecture

SDLC-SPDD Orchestrator combines three layers:

1. **SDLC Agents lifecycle** — role-separated phases from initialization through retro
2. **OpenSPDD REASONS Canvas** — explicit design contract for each unit of work
3. **Cursor commands** — practical execution environment for the workflow

## Workflow

    Requirement
      -> /sdlc-spdd-plan
      -> /sdlc-spdd-architect
      -> /sdlc-spdd-code (one task)
      -> /sdlc-spdd-review
      -> /sdlc-spdd-retro
      -> /sdlc-spdd-sync

## Artifact Model

- Feature workspace: `agent-context/features/<WORK-ID>/`
- Canonical canvas: `spdd/canvas/<WORK-ID>.md`
- Reviews: `spdd/reviews/`
- Sync logs: `spdd/sync/`

## Design Principles

- Markdown-first artifacts
- No-code phases stay no-code
- One approved operation per coding session
- Explicit assumptions and safeguards
- Safe defaults: no overwrite without `--force`

## Attribution

Inspired by [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents) and [OpenSPDD](https://github.com/gszhangwei/open-spdd). This project is not an official extension of either upstream project.
