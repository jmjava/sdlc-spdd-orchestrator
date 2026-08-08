# Architecture

> Deep theory. For onboarding, read [Three-part operating path](three-part-operating-path.md) and the [What each part brings](README.md#what-each-part-brings-read-before-deep-theory) value guides first.

The system has **three parts**: Planning, SPDD, and SDLC (see [Three-part operating path](three-part-operating-path.md)). Architecturally, those three parts are delivered through five concerns:

1. **Planning narrative** (Planning part) — `ROADMAP.md`, `milestone-*.md`, `requirements/`, and `session-notes/` explain where the project is going and what happened recently.
2. **SDLC Agents lifecycle** (SDLC part) — role-separated phases, architecture-first handoffs, progressive context loading, and continual learning.
3. **SPDD REASONS Canvas** (SPDD part) — explicit prompt/design contract for each unit of work.
4. **Assistant adapters** — Cursor commands, GitHub Copilot prompt files, and Claude Code commands that invoke the same skills across all three parts.
5. **Integration runbooks** — Jira, GitHub Pages, and daily-use guidance that keep external systems aligned.

Adapters and integrations are delivery mechanisms, not separate parts.

## Three-Layer Delivery Model

    ROADMAP.md / milestone-*.md / requirements/milestones/ / session-notes/
            -> inform and summarize
    spdd/canvas/ + spdd/memory/ (ledger)  [+ hot .sdlc/ runtime]
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

The planning narrative remains human-readable. SPDD artifacts provide governed execution. Code, reviews, and sync logs prove what actually changed.

See the [C4 context](diagrams/01-context.svg) and [container](diagrams/02-container.svg) diagrams for how these pieces relate inside the single `sdlc-spdd/` install folder.

## Workflow

    Roadmap / milestone / source issue
      -> milestone-to-work mapping
      -> Requirement
      -> /sdlc-spdd-plan
      -> /sdlc-spdd-architect
      -> /sdlc-spdd-code (one task)
      -> /sdlc-spdd-review
      -> /sdlc-spdd-prompt-update (when intent changes)
      -> /sdlc-spdd-retro
      -> /sdlc-spdd-sync

## Artifact Model

Committed:

- Project roadmap: `ROADMAP.md`
- Milestone docs: `milestone-*.md`
- Daily session notes: `session-notes/YYYY-MM-DD.md`
- Canonical canvas: `spdd/canvas/<WORK-ID>.md`
- Reviews: `spdd/reviews/`
- Sync logs: `spdd/sync/`
- Lessons ledger: `spdd/memory/lessons.jsonl` (accepted decisions, pitfalls, patterns, sessions, analysis records — never hand-edited)
- Work registry: `spdd/memory/registry.jsonl` (append-only claim/release events)

Gitignored runtime:

- Hot session briefs: `.sdlc/sessions/` (`current-session.md` is the entry point)
- Staged captures: `.sdlc/staged/lessons.jsonl` (promoted at accept gates)
- Optional local cache: `.sdlc/index.sqlite`

Derived working store: the Guide DICE graph, a regenerable projection of the ledger + canvases, queried on demand. Full model: [Storage v3](storage-v3.md).

## Mapping Scripts

- `scripts/sdlc-spdd/create-work-from-milestone.sh` maps milestone checklist items into Work IDs, requirement stubs, feature workspaces, and draft canvases.
- `scripts/sdlc-spdd/sync-roadmap-from-spdd.sh` refreshes a managed roadmap summary from canvas metadata.
- `scripts/sdlc-spdd/summarize-session-notes.sh` imports existing daily session notes into durable memory.

## Design Principles

- Markdown-first artifacts
- Human planning docs stay human-readable
- SPDD canvases govern work-item execution
- No-code phases stay no-code
- One approved operation per coding session
- Explicit assumptions and safeguards
- Progressive context loading by Work ID and phase — see [Context loading and scaling](context-loading-and-scaling.md)
- One write path for memory: captures stage quietly, accepts promote to the committed ledger, projections regenerate ([Storage v3](storage-v3.md))
- Architecture validation before implementation
- Retro learning captured into the lessons ledger
- Safe defaults: no overwrite without `--force`

## Hybrid Responsibilities

| Responsibility | SDLC Agents influence | SPDD influence |
|----------------|-----------------------|----------------|
| Lifecycle | Initializer, Planning, Architect, Coding, Review, Retro, Curator-style responsibilities | Prompt assets move through plan, generate, review, update, and sync loops |
| Context | Load roadmap, milestone, session, and phase-relevant artifacts progressively | Anchor execution context in the REASONS Canvas |
| Governance | Guardrails, handoffs, architecture-first review | Versioned structured prompts and prompt-first behavior changes |
| Learning | Retro, session notes, and memory prevent repeated mistakes | Reusable prompt contracts accumulate project knowledge |

See [hybrid-model.md](hybrid-model.md) and [roadmap-milestones-and-session-notes.md](roadmap-milestones-and-session-notes.md) for the full mapping.

## Attribution

Inspired by [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents) and [OpenSPDD](https://github.com/gszhangwei/open-spdd). This project is not an official extension of either upstream project.
