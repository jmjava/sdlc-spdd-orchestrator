# Architecture

SDLC-SPDD Orchestrator combines four layers:

1. **SDLC Agents lifecycle** — role-separated phases, architecture-first handoffs, progressive context loading, and continual learning
2. **SPDD REASONS Canvas** — explicit prompt/design contract for each unit of work
3. **Assistant adapters** — Cursor commands and GitHub Copilot prompt files that invoke the same skills
4. **Integration runbooks** — Jira, GitHub Pages, and daily-use guidance that keep external systems aligned

## Workflow

    Requirement
      -> /sdlc-spdd-plan
      -> /sdlc-spdd-architect
      -> /sdlc-spdd-code (one task)
      -> /sdlc-spdd-review
      -> /sdlc-spdd-prompt-update (when intent changes)
      -> /sdlc-spdd-retro
      -> /sdlc-spdd-sync

## Artifact Model

- Feature workspace: `agent-context/features/<WORK-ID>/`
- Session handoffs: `agent-context/sessions/`
- Durable session history: `agent-context/memory/session-history.md`
- Canonical canvas: `spdd/canvas/<WORK-ID>.md`
- Reviews: `spdd/reviews/`
- Sync logs: `spdd/sync/`

## Design Principles

- Markdown-first artifacts
- No-code phases stay no-code
- One approved operation per coding session
- Explicit assumptions and safeguards
- Progressive context loading by Work ID and phase
- Architecture validation before implementation
- Retro learning captured into durable memory
- Safe defaults: no overwrite without `--force`

## Hybrid Responsibilities

| Responsibility | SDLC Agents influence | SPDD influence |
|----------------|-----------------------|----------------|
| Lifecycle | Initializer, Planning, Architect, Coding, Review, Retro, Curator-style responsibilities | Prompt assets move through plan, generate, review, update, and sync loops |
| Context | Load only phase-relevant artifacts and skills | Anchor context in the REASONS Canvas |
| Governance | Guardrails, handoffs, architecture-first review | Versioned structured prompts and prompt-first behavior changes |
| Learning | Retro and memory prevent repeated mistakes | Reusable prompt contracts accumulate project knowledge |

See [hybrid-model.md](hybrid-model.md) for the full mapping.

## Attribution

Inspired by [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents) and [OpenSPDD](https://github.com/gszhangwei/open-spdd). This project is not an official extension of either upstream project.
