# What SPDD Brings to SDLC-SPDD

This page answers one question in one place: **what does Structured Prompt-Driven Development (SPDD) add**, and how does it fit with SDLC lifecycle discipline and project planning artifacts?

SDLC-SPDD is hybrid. It does not ship OpenSPDD CLI. It implements the **REASONS Canvas contract** and **prompt-first governance** through repository artifacts and assistant commands.

## The Three Concepts, One Sentence Each

| Concept | Role | Primary artifacts |
|---------|------|-------------------|
| **Planning** | Tell the team and agent **why** work matters and what happened day to day | `ROADMAP.md`, `milestone-*.md`, `requirements/`, `requirements/milestones/`, `session-notes/` |
| **SPDD** | Tell the agent **what** to build and what not to change | `spdd/canvas/<WORK-ID>.md`, reviews, sync logs |
| **SDLC (Agents)** | Tell the agent **who acts when**, how to hand off, and what context to load | phase commands, playbooks, session briefs, memory |

Together:

    SDLC Agents decides who acts and when.
    SPDD decides what artifact governs the work.
    Milestones and session notes inform and summarize the delivery story.

## Three-Layer Operating Model

    ROADMAP.md / milestone-*.md / requirements/milestones/ / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

SPDD owns the **governance layer** for each Work ID. Planning files inform canvas creation; code and review artifacts validate against the canvas.

## What SPDD Contributes

These are the SPDD capabilities this scaffold adopts.

### 1. Prompts as first-class artifacts

Design contracts live in the repository alongside code:

- `spdd/canvas/<WORK-ID>.md` — canonical REASONS Canvas
- `spdd/reviews/<WORK-ID>-review.md` — review against canvas
- `spdd/sync/<WORK-ID>-sync.md` — implementation-to-canvas reconciliation
- Cursor commands and Copilot prompt files — phase-specific assistant behavior

Prompts are version controlled, reviewable, and reusable.

### 2. REASONS Canvas as the design contract

Every Work ID has a structured canvas with required sections:

| Section | Contract |
|---------|----------|
| **R** — Requirements | Problem, business outcome, acceptance criteria, definition of done |
| **E** — Entities | Domain entities, relationships, inputs, outputs, external systems |
| **A** — Approach | Strategy for satisfying the requirement |
| **S** — Structure | Components, modules, boundaries, dependencies, file locations |
| **O** — Operations | Concrete, testable, ordered implementation steps |
| **N** — Norms | Reusable engineering standards and conventions |
| **S** — Safeguards | Non-negotiable constraints, invariants, security, performance limits |

Validate structure:

    ./scripts/sdlc-spdd/validate-reasons-canvas.sh spdd/canvas/<WORK-ID>.md

### 3. Prompt-first behavior changes

When business intent changes, **update the canvas before code**:

    /sdlc-spdd-prompt-update @spdd/canvas/<WORK-ID>.md

Golden rule:

    Behavior changes update the prompt first.
    Non-behavioral refactors sync the prompt after review.

### 4. Closed-loop synchronization

When reviewed implementation reality diverges from the canvas (without behavior change), reconcile:

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Sync logs record what changed and why.

### 5. Iterative review against intent

Review compares implementation to **all REASONS sections**, not just syntax:

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md

Evidence: review report in `spdd/reviews/`, one operation per coding pass.

### 6. Abstraction before execution

Entities, Approach, and Structure are hardened before coding:

    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md

Readiness must be `Ready For Coding` before `/sdlc-spdd-code`.

### 7. Scoped operations

Coding implements exactly one approved Operation:

    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01

The Operations section is the scope boundary.

### 8. Alignment with external sources

Canvas Metadata links Work IDs to roadmap, milestone, Jira, GitHub, and PRs. Alignment prompts compare Requirements to source acceptance criteria before coding.

## What SDLC Contributes (for contrast)

SPDD and SDLC solve different problems. You need both.

| Need | SPDD contribution | SDLC contribution |
|------|-------------------|-------------------|
| Design contract | REASONS Canvas sections | Plan and architect phases produce/validate canvas |
| Scope control | Operations list | One operation per coding session |
| Intent changes | Update canvas before code | Prompt-update phase and handoff |
| Implementation drift | Sync reconciles canvas | Review and sync phases with memory capture |
| Session continuity | Canvas + progress log | Session briefs, playbooks, durable memory |

## What Planning Artifacts Contribute to SPDD

Planning files **inform** SPDD work but **do not replace** the canvas.

| Planning input | SPDD output |
|----------------|-------------|
| Milestone checklist item | Draft Work ID and canvas via `create-work-from-milestone.sh` |
| `ROADMAP.md` current focus | Canvas Metadata `Roadmap:` field |
| `milestone-*.md` goal and scope | Canvas Metadata `Milestone:` field; plan prompt context |
| `session-notes/` narrative | Informs retro and memory; does not override Operations |

Bridge from milestone to SPDD:

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

Then continue with SPDD lifecycle:

    /sdlc-spdd-plan @requirements/milestones/<WORK-ID>.md @ROADMAP.md @milestone-1.md
    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md

## SPDD Workflow in One Loop

    Business input (requirement, milestone, Jira, session note)
      -> REASONS Canvas
      -> Architecture hardening
      -> One operation of code
      -> Review against canvas
      -> Prompt-update when intent changes
      -> Sync when implementation drifts
      -> Retro into reusable memory

## SPDD Scripts

| Script | SPDD role |
|--------|-----------|
| `validate-reasons-canvas.sh` | Verify REASONS section structure |
| `create-work-from-milestone.sh` | Create draft canvases from milestone items |
| `sync-agent-context.sh` | Copy feature workspace canvas to canonical `spdd/canvas/` |
| `resync-agent-session.sh` | Check canvas drift before a new session |
| `sync-roadmap-from-spdd.sh` | Export canvas metadata summary to `ROADMAP.md` |

## When SPDD Applies on Conflict

SPDD owns **execution scope** when layers disagree:

| Situation | SPDD authority |
|-----------|----------------|
| What to implement next | Canvas Operations |
| Whether behavior changed | Canvas Requirements — prompt-update before code |
| Scope of a coding session | One approved Operation in canvas |
| Engineering constraints | Canvas Norms and Safeguards |
| Canvas copy drift | Canonical `spdd/canvas/<WORK-ID>.md` by default |

Planning narrative informs Requirements but does not replace the canvas. **Full conflict resolution** across all three parts: [Conflict resolution](three-part-operating-path.md#conflict-resolution-single-rule).

## What SPDD Is Not

- Not a replacement for the `openspdd` CLI (workflow shape is implemented via templates and commands).
- Not a Jira sync service (links are documented; transitions are team-owned).
- Not a substitute for code review or CI — it governs **intent**, not compiler output.
- Not optional when using SDLC-SPDD for governed work — without a canvas, there is no SPDD contract.

## SPDD Reference

Upstream inspiration:

- [Structured Prompt-Driven Development](https://martinfowler.com/articles/structured-prompt-driven/) (Martin Fowler)

Related scaffold docs:

- [Three-part operating path](three-part-operating-path.md) — how Planning, SPDD, and SDLC work together end to end
- [SPDD prompt standard](spdd-prompt-standard.md) — copy-paste SPDD prompts for plan, review, sync, and compliance
- [SPDD compliance](spdd-compliance.md) — full compliance matrix and checklist
- [What SDLC brings](what-sdlc-brings.md) — lifecycle discipline and session handoffs
- [What planning brings](what-planning-brings.md) — milestones, roadmap, and session notes
- [Session prompt standard](session-prompt-standard.md) — unified prompts across all three layers
