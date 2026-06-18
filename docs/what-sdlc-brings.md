# What SDLC Brings to SDLC-SPDD

This page answers one question in one place: **what does the SDLC Agents influence add**, and how does it fit with SPDD and project planning artifacts?

SDLC-SPDD is hybrid. It does not ship a separate "SDLC product." It adopts **SDLC Agents lifecycle practices** and pairs them with **SPDD REASONS Canvas governance** and a **human planning layer** (`ROADMAP.md`, `milestone-*.md`, `session-notes/`).

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

Use planning files for narrative and progress. Use SPDD canvases and agent memory for governed execution. Use code and review artifacts as evidence.

## What SDLC Agents Contributes

These are the SDLC capabilities this scaffold adopts.

### 1. Role-separated lifecycle

Work moves through specialized phases instead of one undifferentiated "fix it" chat:

    Init -> Plan -> Architect -> Code -> Review -> Prompt-update -> Retro -> Sync

Each phase has a dedicated command. Run `/sdlc-spdd-*` in **AI chat** (Cursor/Copilot/Claude Code), not a terminal — see [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands):

| Phase | Command |
|-------|---------|
| Initialize | `/sdlc-spdd-init` |
| Plan | `/sdlc-spdd-plan` |
| Architect | `/sdlc-spdd-architect` |
| Code | `/sdlc-spdd-code` |
| Review | `/sdlc-spdd-review` |
| Prompt update | `/sdlc-spdd-prompt-update` |
| Retro | `/sdlc-spdd-retro` |
| Sync | `/sdlc-spdd-sync` |

### 2. Architecture-first handoffs

Design is validated before implementation. `/sdlc-spdd-architect` checks Entities, Approach, Structure, Norms, and Safeguards before coding starts.

### 3. Incremental coding

Coding implements **one approved Operation** at a time (for example `T01`, then `T02`). This keeps diffs reviewable and scope bounded.

### 4. Progressive context loading

Each phase loads only the artifacts it needs. See the context-loading table in [Hybrid SDLC Agents + SPDD model](hybrid-model.md).

Examples:

- **Plan** loads requirements, roadmap, milestone, and memory — not unrelated source files.
- **Code** loads the canvas, one operation, and relevant files — not other operations.
- **Review** loads the canvas, diff, and tests — not new feature ideation.

### 5. Continual learning

Retros and session capture write durable memory:

- `agent-context/memory/session-history.md`
- `agent-context/memory/architecture-decisions.md`
- `agent-context/memory/known-pitfalls.md`
- `agent-context/memory/reusable-patterns.md`

A new session can resume from files instead of reconstructing context from chat.

### 6. Explicit guardrails

- No-code phases (plan, architect, prompt-update) do not edit application behavior.
- Operation boundaries limit coding scope.
- Quality gates and validation rules live in `agent-context/harness/`.
- Playbooks provide repeatable workflows by work type.

### 7. Session persistence

Session scripts create handoff briefs and resume prompts:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>

Output: `agent-context/sessions/current-session.md` with artifact status, planning context, and a copy-paste resume prompt.

### 8. Multi-assistant adapters

The same lifecycle semantics work in Cursor (`/sdlc-spdd-*` commands), GitHub Copilot (`.github/prompts/sdlc-spdd-*.prompt.md`), and Claude Code (`.claude/commands/sdlc-spdd-*.md` with `CLAUDE.md`).

## What SPDD Contributes (for contrast)

SDLC and SPDD solve different problems. You need both.

| Need | SDLC contribution | SPDD contribution |
|------|-------------------|-------------------|
| Disciplined workflow | Phase roles and handoffs | REASONS Canvas as contract |
| Scope control | One operation per coding pass | Operations section in canvas |
| Intent changes | Prompt-update phase | Update canvas before code |
| Implementation drift | Sync phase after review | Reconcile canvas with code |
| Design structure | Architect validation gate | Requirements, Entities, Approach, Structure, Norms, Safeguards |

Canonical canvas path:

    spdd/canvas/<WORK-ID>.md

## What Milestones and Session Notes Contribute

Planning artifacts are **not** framework-owned prompts. Install and upgrade preserve your content.

| Artifact | SDLC-SPDD role |
|----------|----------------|
| `ROADMAP.md` | Milestone-level progress and current focus |
| `milestone-*.md` | Goals, scope, linked Work IDs, milestone summaries |
| `session-notes/YYYY-MM-DD.md` | Daily agent-session narrative |

Scripts bridge planning and governance:

| Script | Direction |
|--------|-----------|
| `create-work-from-milestone.sh` | milestone -> SPDD work artifacts |
| `sync-roadmap-from-spdd.sh` | SPDD canvas metadata -> roadmap summary |
| `summarize-session-notes.sh` | session notes -> durable memory |
| `capture-session-memory.sh` | session -> memory, notes, milestone, roadmap |

## How the Three Concepts Connect in a Session

Typical flow:

1. **Planning** — milestone checklist or roadmap item defines the goal.
2. **Mapping** — `create-work-from-milestone.sh` creates Work IDs and draft canvases.
3. **SDLC lifecycle** — plan, architect, code one operation, review.
4. **SPDD governance** — canvas governs scope; prompt-update before behavior changes; sync after accepted drift.
5. **Capture** — `capture-session-memory.sh` writes memory, session notes, and optional milestone/roadmap updates.
6. **Summary** — `sync-roadmap-from-spdd.sh` refreshes the managed roadmap section from canvas metadata.

Start-of-session bridge:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase code --milestone milestone-1.md

The generated resume prompt includes SDLC phase context, SPDD canvas references, and planning-layer files when present.

## What SDLC-SPDD Is Not

- Not a compiled multi-agent runtime.
- Not a replacement for Cursor, Copilot, Claude Code, Jira, or OpenSPDD CLI.
- Not an official extension of upstream SDLC Agents or SPDD projects.
- Not a single source of truth that replaces all three layers — each layer has a distinct job.

## When SDLC Applies on Conflict

SDLC owns **session continuity**, not execution scope:

| Situation | SDLC role |
|-----------|-----------|
| What happened in today's session | Session notes and progress log |
| Cross-session lessons | `agent-context/memory/` |
| How to resume after a break | Session brief + Resume Prompt from `start-agent-session.sh` |

**Full conflict resolution across all three parts** — including canvas authority and planning narrative — is defined in one place: [Conflict resolution](three-part-operating-path.md#conflict-resolution-single-rule) in the three-part operating path.

## SDLC Reference

Upstream inspiration:

- [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents)

Related scaffold docs:

- [Three-part operating path](three-part-operating-path.md) — how Planning, SPDD, and SDLC work together end to end
- [What SPDD brings](what-spdd-brings.md) — REASONS Canvas governance
- [What planning brings](what-planning-brings.md) — roadmap, milestones, session notes
- [Hybrid SDLC Agents + SPDD model](hybrid-model.md) — full command mapping and context-loading rules
- [Session prompt standard](session-prompt-standard.md) — unified session prompts
- [SPDD prompt standard](spdd-prompt-standard.md) — canvas governance prompts
- [Planning prompt standard](planning-prompt-standard.md) — planning layer prompts
- [SPDD compliance](spdd-compliance.md) — prompt-first and sync rules
