# Three-Part Operating Path

This is the canonical guide for **how to use all three parts together**: Planning, SPDD, and SDLC. Read this when you want one path—not three separate doc piles.

For *which prompt standard to open*, see [Which prompt standard?](session-prompt-standard.md#which-prompt-standard). For *what each part contributes*, see the value guides in the table below.

## The Three Parts

| Part | Question it answers | You touch it when… |
|------|---------------------|-------------------|
| **Planning** | *Why* are we doing this? *What* is the delivery story? | Roadmap, milestones, requirement stubs, session notes |
| **SPDD** | *What* exactly should be built—and what is out of scope? | REASONS Canvas, reviews, sync logs |
| **SDLC** | *Who acts when*, and how do sessions hand off? | Phase commands, session briefs, memory, playbooks |

## Three-Part Design Mandate

**There are exactly three parts: Planning, SPDD, SDLC.** Do not collapse them into one layer. Do not delete artifacts from one part because another part exists.

### Artifact ownership (preserve all of these)

| Part | Required artifacts | Role |
|------|-------------------|------|
| **Planning** | `ROADMAP.md` | Delivery overview, current focus, managed work summary |
| **Planning** | `milestone-*.md` | Goals, scope checklists, **Linked Work** table |
| **Planning** | `requirements/milestones/<WORK-ID>.md` | Milestone-derived requirement stubs (created by `create-work-from-milestone.sh`) |
| **Planning** | `requirements/<topic>.md` | Ad-hoc requirement files (not milestone-driven) |
| **Planning** | `session-notes/YYYY-MM-DD.md` | Daily agent-session narrative |
| **SPDD** | `spdd/canvas/<WORK-ID>.md` | Canonical REASONS Canvas — **governs execution** |
| **SPDD** | `spdd/reviews/`, `spdd/sync/` | Review and reconciliation evidence |
| **SDLC** | `agent-context/sessions/`, `agent-context/memory/` | Session handoffs and durable memory |
| **SDLC** | Phase commands, playbooks | Lifecycle discipline |

Install and upgrade scripts **create missing Planning scaffolding** and **never overwrite** existing `ROADMAP.md`, `milestone-*.md`, `requirements/milestones/`, or `session-notes/`.

Verify after install:

    ./scripts/sdlc-spdd/verify-project-install.sh --target .

`init-project.sh` and `upgrade-project.sh` run this automatically unless `--dry-run` is set.

### Rules — do not break the three parts

1. **Do not delete Planning artifacts** to simplify scripts or docs. Milestones and session notes are not optional extras — they are the Planning part.
2. **Do not replace the canvas with planning files.** Milestone checklists and requirement stubs **inform** SPDD; `spdd/canvas/<WORK-ID>.md` **governs** scope and operations.
3. **Do not skip SDLC handoffs.** Session briefs, memory capture, and phase commands are the SDLC part — chat alone is not enough.
4. **`requirements/milestones/` is Planning**, not SPDD. It bridges milestone checklist items into `/sdlc-spdd-plan`; the canvas is still created under `spdd/canvas/`.
5. **Ad-hoc and milestone paths both stay.** Entry A uses `requirements/milestones/`; Entry B uses `requirements/`. Neither path removes the other.

### What went wrong once (do not repeat)

Removing `requirements/milestones/` from `create-work-from-milestone.sh` treated a Planning artifact as dead code. That violated the mandate. The folder is restored as the **canonical** location for milestone-derived requirement stubs.

Three-layer flow:

    Planning
      ROADMAP.md, milestone-*.md, requirements/, requirements/milestones/, session-notes/
            -> inform and summarize
    SPDD + SDLC memory
      spdd/canvas/, spdd/reviews/, spdd/sync/, agent-context/
            -> govern and remember
    Evidence
      code, tests, validation output
            -> execute and validate

## One Path, Two Entry Points

Most work follows the same loop. You enter at **A** (milestone-driven) or **B** (ad-hoc requirement).

### Entry A — Start from a milestone (recommended for teams)

Use when work is already on `milestone-*.md` or `ROADMAP.md`.

| Step | Part | Action |
|------|------|--------|
| A1 | **Planning** | Define goal and checklist in `milestone-1.md`; set Current Focus in `ROADMAP.md` |
| A2 | **Planning → SPDD** | `./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all` |
| A3 | **SPDD** | `/sdlc-spdd-plan @requirements/milestones/<WORK-ID>.md @ROADMAP.md @milestone-1.md` |
| A4 | **SPDD** | `/sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md` — wait for Ready For Coding |
| A5 | **SDLC** | `./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase code --milestone milestone-1.md` — session brief at **code** phase because plan/architect may span earlier chats; re-run with the matching `--phase` whenever the phase changes |
| A6 | **SDLC + SPDD** | `/sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01` → review → sync |
| A7 | **SDLC + Planning** | `capture-session-memory.sh` with `--milestone` and `--roadmap-note` |
| A8 | **Planning ← SPDD** | `./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .` |

### Entry B — Start from an ad-hoc requirement

Use when a bug, feature request, or spike arrives without a milestone item yet.

| Step | Part | Action |
|------|------|--------|
| B1 | **SDLC** | Triage: propose Work ID and whether `/sdlc-spdd-plan` is safe |
| B2 | **SDLC** | `./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase plan` |
| B3 | **SPDD** (+ Planning if applicable) | `/sdlc-spdd-plan @requirements/<file>.md` or with `@ROADMAP.md @milestone-1.md` |
| B4 | **SPDD** | `/sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md` |
| B5–B7 | **SDLC + SPDD** | Same as A5–A6 (code one operation → review → sync) |
| B8 | **SDLC + Planning** | Capture memory; link Work ID in milestone Linked Work table if it belongs to a milestone |
| B9 | **Planning ← SPDD** | `sync-roadmap-from-spdd.sh` when ready for roadmap summary |

## Daily Loop (all three parts)

Once initialized, repeat this loop every agent session:

```
┌─────────────────────────────────────────────────────────────┐
│  SDLC: resync + start-agent-session (session brief)         │
│         ↓ paste Resume Prompt (Session prompt standard)     │
├─────────────────────────────────────────────────────────────┤
│  SPDD: work one phase — plan / architect / code / review      │
│         ↓ canvas governs scope; prompt-update if intent     │
│           changed; sync if implementation drifted           │
├─────────────────────────────────────────────────────────────┤
│  SDLC + Planning: capture-session-memory                    │
│         ↓ session-notes + milestone + roadmap note          │
├─────────────────────────────────────────────────────────────┤
│  Planning: sync-roadmap-from-spdd (when summary stale)      │
└─────────────────────────────────────────────────────────────┘
```

### Morning (5 minutes)

| Part | Do this |
|------|---------|
| SDLC | `resync-agent-session.sh --check-only` then `start-agent-session.sh` |
| SDLC | Paste **Resume Prompt** from `current-session.md` |
| Planning | Resume prompt includes `@ROADMAP.md`, `@milestone-*.md`, `@session-notes/` when present |

### During work

| Part | Do this |
|------|---------|
| SPDD | Every action references `@spdd/canvas/<WORK-ID>.md` |
| SDLC | One phase command at a time; one Operation per code pass |
| Planning | Include milestone context in plan prompts when work belongs to a milestone |

### End of session (5 minutes)

| Part | Do this |
|------|---------|
| SDLC | `capture-session-memory.sh` — writes durable memory + progress log |
| Planning | Same script writes `session-notes/`, optional `--milestone`, `--roadmap-note` |
| SPDD | Set `--next` to the next phase command (review, sync, next operation) |

## Which Part Owns Each Workflow Step

Maps the [13-step workflow](workflow.md) to the three parts:

| Step | Workflow action | Primary part | Also touches |
|------|-----------------|--------------|--------------|
| 1 | Setup prompts and memory | SDLC | Planning scaffolding created |
| 2 | `/sdlc-spdd-init` | SDLC | Detects stack into memory |
| 3 | `create-work-from-milestone.sh` | Planning | Creates SPDD draft canvas |
| 4 | `start-agent-session.sh` | SDLC | Reads Planning + SPDD status |
| 5 | `/sdlc-spdd-plan` | SPDD | Planning context in prompt |
| 6 | `/sdlc-spdd-architect` | SPDD | SDLC architecture-first gate |
| 7 | `/sdlc-spdd-code` | SDLC + SPDD | One canvas Operation |
| 8 | `/sdlc-spdd-review` | SPDD | SDLC review phase |
| 9 | `/sdlc-spdd-prompt-update` | SPDD | When intent changes |
| 10 | `/sdlc-spdd-retro` | SDLC | Writes reusable memory |
| 11 | `/sdlc-spdd-sync` | SPDD | Reconciles canvas with code |
| 12 | `capture-session-memory.sh` | SDLC + Planning | Session notes, milestone |
| 13 | `sync-roadmap-from-spdd.sh` | Planning | Summary from SPDD metadata |

## Decision Guide: Which Part Right Now?

    Am I defining or summarizing delivery goals?
      -> Planning (milestone, roadmap, session-notes)

    Am I deciding what to build or whether a change is in scope?
      -> SPDD (canvas, operations, prompt-update, sync)

    Am I running a session, phase, or handoff?
      -> SDLC (start-agent-session, phase commands, capture-memory)

    Not sure?
      -> Start SDLC session brief, then let the canvas and milestone files guide you

## Prompt Standards for Each Part

| Part | Prompt standard | Value guide |
|------|-----------------|-------------|
| **Default (sessions)** | [Session prompt standard](session-prompt-standard.md) | [What SDLC brings](what-sdlc-brings.md) |
| **SPDD drill-down** | [SPDD prompt standard](spdd-prompt-standard.md) | [What SPDD brings](what-spdd-brings.md) |
| **Planning drill-down** | [Planning prompt standard](planning-prompt-standard.md) | [What planning brings](what-planning-brings.md) |

Open **Session** first. Open **SPDD** or **Planning** when your question narrows to that layer. See [Which prompt standard?](session-prompt-standard.md#which-prompt-standard).

## Session Brief Timing

Run `start-agent-session.sh` with `--phase` set to the phase you are **about to run**, then paste the generated Resume Prompt.

| Entry | When to create the first brief |
|-------|-------------------------------|
| **A** (milestone) | After plan + architect, at **code** phase (steps A3–A4 may happen without a brief, or with `--phase plan` if you prefer) |
| **B** (ad-hoc) / **First day** | At **plan** phase, before `/sdlc-spdd-plan` |
| **Daily resume** | At whatever phase you are resuming today |

Re-run the script whenever the phase changes so `current-session.md` stays accurate.

## Conflict Resolution (single rule)

This is the **only** full conflict-resolution table. The value guides ([What SDLC brings](what-sdlc-brings.md), [What SPDD brings](what-spdd-brings.md), [What planning brings](what-planning-brings.md)) list part-specific bullets and link here.

When layers disagree, use this order:

1. **Canvas governs execution** — Operations, scope, behavior (SPDD)
2. **Planning governs narrative** — why work exists, milestone story, roadmap focus
3. **Bridge intent changes** — update canvas with `/sdlc-spdd-prompt-update`, then update milestone/roadmap notes
4. **Canonical canvas** — `spdd/canvas/<WORK-ID>.md` is authoritative unless you explicitly sync from the feature workspace

| Situation | Authoritative source |
|-----------|---------------------|
| What to implement next | Canvas Operations |
| Why this work exists | Milestone goal, roadmap narrative |
| What happened today | Session notes, progress log |
| Whether behavior changed | Canvas Requirements → prompt-update before code |
| Canvas copy drift | Canonical `spdd/canvas/` by default; use `resync --from-canvas` or `--from-feature` when intentional |

## Common Mistakes

| Mistake | Wrong part emphasis | Fix |
|---------|---------------------|-----|
| Coding without a canvas | Skipped SPDD | Plan + architect first |
| Putting implementation detail only in chat | Skipped SDLC capture | `capture-session-memory.sh` |
| Replacing canvas with milestone checklist | Planning replaced SPDD | Milestone informs; canvas governs |
| "Continue" without session brief | Skipped SDLC handoff | `start-agent-session.sh` + resume prompt |
| Updating roadmap but not canvas | Planning without SPDD | `prompt-update` then `sync-roadmap-from-spdd` |

## First Time vs Daily Use

| Situation | Start here |
|-----------|------------|
| Never used SDLC-SPDD | [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md) — then return to this page |
| Installed, need the full path | **This page** |
| Daily agent session | [Daily runbook](daily-runbook.md) + [Session prompt standard](session-prompt-standard.md) |
| Prompt confusion | [Which prompt standard?](session-prompt-standard.md#which-prompt-standard) |
| Script reference | [Agent session scripts](agent-session-scripts.md) + [Workflow](workflow.md) |

## Read Next

- [Workflow](workflow.md) — 13-step command sequence
- [Daily runbook](daily-runbook.md) — day-to-day operations
- [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md) — planning file details
- [SPDD compliance](spdd-compliance.md) — canvas compliance checklist
