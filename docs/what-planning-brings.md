# What Planning Brings to SDLC-SPDD

This page answers one question in one place: **what does the Planning part add** — roadmap, milestones, requirement stubs, and session notes — and how does it fit with SPDD governance and SDLC lifecycle discipline?

The Planning part is **not** optional. See the [Three-part design mandate](three-part-operating-path.md#three-part-design-mandate).

The planning layer is the **human-readable narrative** for delivery. It is project-owned content — install and upgrade scripts create scaffolding but never overwrite your existing planning files.

## The Three Concepts, One Sentence Each

| Concept | Role | Primary artifacts |
|---------|------|-------------------|
| **Planning** | Tell the team and agent **why** work matters and what happened day to day | `ROADMAP.md`, `milestone-*.md`, `requirements/`, `requirements/milestones/`, `session-notes/` |
| **SPDD** | Tell the agent **what** to build and what not to change | `spdd/canvas/<WORK-ID>.md`, reviews, sync logs |
| **SDLC (Agents)** | Tell the agent **who acts when**, how to hand off, and what context to load | phase commands, playbooks, session briefs, memory |

Together:

    Planning artifacts inform and summarize.
    SPDD canvases govern execution.
    SDLC lifecycle structures how agents work.

## Three-Layer Operating Model

    ROADMAP.md, milestone-*.md, requirements/, requirements/milestones/, session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

**Do not migrate away from planning files.** Keep them as the story layer. Use SPDD and SDLC artifacts for governed execution and durable agent memory.

## What Planning Artifacts Contribute

### 1. Roadmap — delivery overview

`ROADMAP.md` answers:

- What milestones exist and their status?
- What is the current focus (Work ID, phase, next command)?
- What is the high-level progress summary?

Managed SPDD summary section (auto-refreshed):

    <!-- SDLC-SPDD-ROADMAP-SUMMARY:START -->
    <!-- SDLC-SPDD-ROADMAP-SUMMARY:END -->

Handwritten content outside those markers is always preserved.

### 2. Milestones — scoped delivery goals

`milestone-*.md` answers:

- What outcome does this milestone deliver?
- What checklist items remain?
- Which Work IDs are linked to this milestone?

Typical sections:

- **Goal** — outcome statement
- **Scope** — checklist of work items
- **Linked Work** — table mapping Work IDs to status, issues, canvases
- **Session Updates** — milestone-level summaries (details live in `session-notes/`)

### 3. Milestone requirements — per-item stubs

`requirements/milestones/<WORK-ID>.md` holds requirement stubs derived from milestone checklist items.

Created by `create-work-from-milestone.sh`. Use in plan prompts:

    /sdlc-spdd-plan @requirements/milestones/<WORK-ID>.md @ROADMAP.md @milestone-1.md

Ad-hoc requirements (not milestone-driven) live under `requirements/` at the project root.

### 4. Session notes — daily agent narrative

`session-notes/YYYY-MM-DD.md` answers:

- What happened in today's agent sessions?
- What was validated?
- What is the next step?

Session notes are the **human-readable daily log**. Durable agent memory (`agent-context/memory/`) is the **machine-resumable** layer. Both are valuable; scripts bridge them.

## What SPDD and SDLC Contribute (for contrast)

| Need | Planning contribution | SPDD / SDLC contribution |
|------|----------------------|--------------------------|
| Why work matters | Milestone goal, roadmap focus | Canvas Requirements (derived from planning) |
| Daily story | Session notes | Progress log, session history |
| What to build | Informs plan prompts | REASONS Canvas governs scope |
| Who acts when | Current focus in roadmap | SDLC phase commands |
| Cross-session memory | Imported via summarize script | `agent-context/memory/` |

**The roadmap and milestones tell the agent why the work matters. The canvas tells the agent what to build.**

## Planning Scripts

| Script | Direction | Purpose |
|--------|-----------|---------|
| `create-work-from-milestone.sh` | milestone → SPDD | Create Work IDs, requirements, draft canvases from checklist items |
| `sync-roadmap-from-spdd.sh` | SPDD → roadmap | Refresh managed roadmap summary from canvas metadata |
| `summarize-session-notes.sh` | session notes → memory | Import historical notes into durable agent memory |
| `capture-session-memory.sh` | session → all layers | Write memory, progress log, session notes, milestone, roadmap |
| `start-agent-session.sh` | all layers → session brief | Include roadmap, milestone, session-note status in resume prompt |

## Typical Planning Flow

### 1. Define milestone scope

Edit `milestone-1.md`:

    ## Goal
    Deliver order status lookup for customer support.

    ## Scope
    - [ ] Add order status API
    - [ ] Add order status tests

### 2. Map checklist to governed work

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

### 3. Plan with planning context

    /sdlc-spdd-plan @requirements/milestones/<WORK-ID>.md @ROADMAP.md @milestone-1.md

Canvas Metadata should include:

    - Roadmap: ROADMAP.md
    - Milestone: milestone-1.md

### 4. Work through SDLC + SPDD lifecycle

Use phase commands (plan → architect → code → review → sync). See [What SDLC brings](what-sdlc-brings.md) and [What SPDD brings](what-spdd-brings.md).

### 5. Capture session to all layers

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id <WORK-ID> \
      --phase code \
      --summary "Implemented T01." \
      --validation "mvn test" \
      --milestone milestone-1.md \
      --roadmap-note "FEAT-001 completed first operation." \
      --next "/sdlc-spdd-review @spdd/canvas/<WORK-ID>.md"

When `--milestone` is omitted, `capture-session-memory.sh` searches `milestone-*.md` for the Work ID.

### 6. Refresh roadmap summary from SPDD

    ./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .

### 7. Import historical session notes

    ./scripts/sdlc-spdd/summarize-session-notes.sh --target . --all

## Starting a Session with Planning Context

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase code --milestone milestone-1.md

The generated resume prompt includes `@ROADMAP.md`, `@milestone-*.md`, and today's `@session-notes/YYYY-MM-DD.md` when those files exist.

## When Planning Applies on Conflict

Planning owns **delivery narrative**, not execution scope:

| Situation | Planning authority |
|-----------|-------------------|
| Why this work exists | Milestone goal and roadmap narrative |
| High-level delivery status | Roadmap (managed summary from canvas metadata) |
| Daily story | Session notes (detail) and milestone summaries |

When planning intent changes, update the milestone or roadmap **and** run `/sdlc-spdd-prompt-update` so the canvas stays aligned. **Full conflict resolution** across all three parts: [Conflict resolution](three-part-operating-path.md#conflict-resolution-single-rule).

## Suggested Update Patterns

**Roadmap — keep it high level:**

    ## Current Focus
    - Work ID: FEAT-001-order-status-api
    - Active milestone: milestone-1.md
    - Current phase: Review
    - Next command: /sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md

**Milestone — tie to Work IDs:**

    ## Linked Work
    | Work ID | Canvas | Requirement | Status | Notes |
    | FEAT-001-order-status-api | spdd/canvas/FEAT-001-order-status-api.md | requirements/milestones/FEAT-001-order-status-api.md | In Review | T01 implemented |

**Session notes — daily detail; roadmap/milestone — summaries.**

## What Planning Is Not

- Not a replacement for REASONS Canvas — canvases govern execution per Work ID.
- Not framework-owned prompts — your team controls content; upgrades preserve it.
- Not auto-synced bidirectionally — milestone checkboxes do not auto-update from canvas operation status (capture and manual updates bridge the gap).
- Not the same as durable agent memory — use `summarize-session-notes.sh` and `capture-session-memory.sh` to feed memory.

## Related Scaffold Docs

- [Three-part operating path](three-part-operating-path.md) — how Planning, SPDD, and SDLC work together end to end
- [Planning prompt standard](planning-prompt-standard.md) — copy-paste prompts for roadmap, milestones, and session notes
- [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md) — operational guide and file layout
- [What SDLC brings](what-sdlc-brings.md) — lifecycle discipline
- [What SPDD brings](what-spdd-brings.md) — REASONS Canvas governance
- [Session prompt standard](session-prompt-standard.md) — unified prompts across all three layers
