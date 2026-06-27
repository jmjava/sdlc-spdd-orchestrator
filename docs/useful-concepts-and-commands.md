# Top Useful Concepts and Commands

This page explains **what things mean** (Work ID, canvas, operation, sync, memory). For a dense **command cheat sheet** to print or keep open, use [Cheat sheet](sdlc-spdd-cheat-sheet.md). For copy-paste prompts, use [Session prompt standard](session-prompt-standard.md).

## Top Concepts

### How the names relate

There is one name — the **Work ID** — and every other artifact name is derived from it.

Anatomy of a Work ID:

    FEAT-004-prompt-optimization-ledger
    └─┬─┘ └┬┘ └──────────┬──────────┘
      │    │             └── slug (human-readable name)
      │    └──────────────── NNN (zero-padded sequence: 001, 002, …)
      └───────────────────── PREFIX = work type
                             FEAT=Feature  BUG=Bugfix  REF=Refactor  SPIKE=Spike

Every artifact path is `<location>/<WORK-ID>`:

    FEAT-004-prompt-optimization-ledger
      ├── requirements/milestones/FEAT-004-prompt-optimization-ledger.md   (Requirement: why + acceptance)
      ├── spdd/canvas/FEAT-004-prompt-optimization-ledger.md               (REASONS Canvas: design contract)
      └── agent-context/features/FEAT-004-prompt-optimization-ledger/      (Feature workspace: memory)
            ├── requirement.md
            ├── reasons-canvas.md
            └── progress-log.md
                    │
                    └── inside the canvas → Operations T01, T02, … (restart at T01 per canvas)

The two levels to keep straight:

- **Work ID** (`FEAT-004-…`) names *the work* and all of its files.
- **Operation** (`T01`, `T02`, …) names *a step inside* that work's canvas. It never appears in a file name, branch, or roadmap entry.

| Naming scheme | Names | Derived from |
|---------------|-------|--------------|
| Work ID | The whole unit of work | — (the root key) |
| Prefix | Work type | first segment of the Work ID |
| Requirement | Intent | `requirements/milestones/<WORK-ID>.md` |
| Canvas | Design contract | `spdd/canvas/<WORK-ID>.md` |
| Feature workspace | Working memory | `agent-context/features/<WORK-ID>/` |
| Operation (`T0x`) | A task inside one canvas | scoped to that canvas |

### Work ID

A stable identifier for one unit of work.

Examples:

- `FEAT-001-order-status-api`
- `BUG-003-null-discount-checkout`
- `REF-002-split-billing-service`

Use the Work ID in prompts, canvas files, progress logs, reviews, sync logs, branches, commits, and Jira updates.

### REASONS Canvas

The SPDD design contract for a Work ID.

Sections:

- Requirements
- Entities
- Approach
- Structure
- Operations
- Norms
- Safeguards

Canonical path:

    spdd/canvas/<WORK-ID>.md

### Operation

A small, approved implementation step in the canvas.

Example:

    T01 - Add service method
    T02 - Add API endpoint
    T03 - Add tests

Coding should implement one operation at a time.

### Prompt Update

Use prompt update when the intended behavior changes.

Command:

    /sdlc-spdd-prompt-update @spdd/canvas/<WORK-ID>.md

Rule:

    Behavior changes update the canvas before code.

### Sync

Use sync when reviewed implementation reality should be reflected back into the canvas.

Command:

    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Rule:

    Non-behavioral refactors sync the canvas after review.

### Session Brief

A file that lets a new agent session resume work from repository context.

Current session:

    agent-context/sessions/current-session.md

Create one:

    ./scripts/sdlc-spdd/sdlc.sh start
    # or: ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>

### SDLC Pointer

The active Work ID on **this machine**. Stored in `.sdlc/pointer` (gitignored). Guarded commands (for example `sdlc.sh capture`) refuse to run when the pointer does not match the requested Work ID.

    ./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>    # sets pointer + team registry
    ./agent-context/sdlc-pointer.sh get

See [agent-context/README.md](../agent-context/README.md#sdlc-pointer-current-choretask).

### Workflow CLI

Phase and gate tracking for the active Work ID. State lives in `.sdlc/workflows/` (gitignored). Committed artifacts (canvas, progress log) remain the audit trail.

    ./scripts/sdlc-spdd/sdlc.sh next       # what to do now
    ./scripts/sdlc-spdd/sdlc.sh advance    # move to next phase
    ./scripts/sdlc-spdd/sdlc.sh shelf --reason "..."

In chat: `/sdlc-spdd-whereami`.

### Team Registry

Shared coordination via git. Who owns which Work ID, phase, branch, PR, and Jira key.

    ./scripts/sdlc-spdd/sdlc.sh team
    ./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>    # commit agent-context/work-registry.tsv

File: `agent-context/work-registry.tsv`.

### Durable Memory

Project knowledge that survives chat sessions.

Important files:

- `agent-context/memory/project-memory.md`
- `agent-context/memory/session-history.md`
- `agent-context/memory/architecture-decisions.md`
- `agent-context/memory/known-pitfalls.md`
- `agent-context/memory/reusable-patterns.md`

### Roadmap and Milestones

Project-owned planning files that connect SDLC-SPDD work to larger delivery goals.

Common files:

- `ROADMAP.md`
- `milestone-1.md`
- `milestone-2.md`
- `session-notes/YYYY-MM-DD.md`

Milestone requirements may include a `## Jira` draft section (`requirements/milestones/<WORK-ID>.md`). On claim, `./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>` auto-links the Jira Key into the team registry. See [requirements/milestones/README.md](../requirements/milestones/README.md).

Use roadmap and milestone docs to give planning agents delivery context. Use REASONS Canvas files to govern each Work ID.

## Commands and Prompts

`/sdlc-spdd-*` commands run in **AI chat** (Cursor/Copilot/Claude Code), not a terminal. [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

Command list (install, lifecycle, scripts): [Cheat sheet](sdlc-spdd-cheat-sheet.md).

Copy-paste prompts: [Session prompt standard](session-prompt-standard.md) — see [Which prompt standard?](session-prompt-standard.md#which-prompt-standard) when drilling into SPDD or Planning.

## Common Mistakes to Avoid

- Starting code before `/sdlc-spdd-architect`.
- Asking "continue" without a Work ID or session brief.
- Implementing multiple operations in one coding pass.
- Using `/sdlc-spdd-sync` for a new behavior requirement.
- Forgetting to capture memory at the end of a session (use `sdlc.sh capture`).
- Running capture against the wrong Work ID (pointer mismatch — use `sdlc.sh claim`/`resume` first).
- Claiming work without committing `agent-context/work-registry.tsv` on shared repos.
- Editing application behavior after Jira acceptance criteria changed without prompt-update.

## Read Next

- [What SDLC brings](what-sdlc-brings.md)
- [Session prompt standard](session-prompt-standard.md)
- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md)
- [Daily runbook](daily-runbook.md)
- [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md)
- [Agent session scripts](agent-session-scripts.md)
- [SPDD compliance](spdd-compliance.md)
