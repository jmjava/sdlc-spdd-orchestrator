# 10,000-Foot View of SDLC-SPDD Orchestrator

SDLC-SPDD Orchestrator is a lightweight scaffolding system for AI-assisted software delivery.

It does not replace your coding assistant. It gives the assistant a disciplined workflow, durable memory, reviewable prompt artifacts, and repeatable handoffs.

## The Big Idea

Most AI coding workflows fail because context lives in chat and disappears.

SDLC-SPDD moves that context into files:

- requirements
- REASONS Canvas design contracts
- task operations
- review reports
- sync logs
- memory
- session handoffs
- playbooks

The result is a workflow where a new agent session can resume from repository artifacts instead of guessing from a partial conversation.

## Three Parts

This project is hybrid.

| Part | What it contributes |
|------|---------------------|
| Planning (`ROADMAP.md`, `milestone-*.md`, `session-notes/`) | delivery narrative — why work matters, progress summaries |
| SPDD / REASONS Canvas | versioned prompt contracts, requirements-to-design-to-operations structure, prompt/code synchronization |
| SDLC Agents | role-separated lifecycle, architecture-first handoffs, progressive context loading, retro learning |

Together:

    Planning informs and summarizes.
    SPDD decides what artifact governs the work.
    SDLC Agents decides who acts and when.

See [Three-part operating path](three-part-operating-path.md) for the end-to-end path.

## The Core Loop

The system has three layers:

    ROADMAP.md / milestone-*.md / requirements/milestones/ / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

Roadmap, milestone, and session-note files stay human-readable. SPDD canvases and agent memory provide the governed execution layer.

## The Delivery Loop

    Initialize
      -> Plan
      -> Architect
      -> Code one operation
      -> Review
      -> Prompt update when intent changes
      -> Sync when implementation drifts
      -> Retro
      -> Capture memory

This is deliberately slower than asking an assistant to "just fix it." It is meant to keep changes governable, reviewable, and reusable.

## Main Artifact Folders

| Path | Purpose |
|------|---------|
| `ROADMAP.md` | project milestone progress and current focus |
| `milestone-*.md` | milestone goals, scope, linked Work IDs, and summaries |
| `session-notes/` | daily summaries of agent sessions |
| `requirements/` | raw requirements, issue notes, acceptance criteria |
| `requirements/milestones/` | milestone-derived requirement stubs (one per Work ID from checklist items) |
| `spdd/canvas/` | canonical REASONS Canvas files |
| `spdd/reviews/` | review outputs against the canvas |
| `spdd/sync/` | implementation-to-canvas reconciliation logs |
| `agent-context/features/` | per-work feature workspace |
| `agent-context/memory/` | durable learnings, decisions, pitfalls, patterns |
| `agent-context/sessions/` | current and historical session handoffs |
| `agent-context/playbooks/` | repeatable workflows for feature, bugfix, refactor, review |
| `agent-context/harness/` | quality gates and validation rules |
| `scripts/sdlc-spdd/` | target-local runtime helpers |

## Main Assistant Skills

`/sdlc-spdd-*` skills run in **AI chat** (Cursor/Copilot/Claude Code), not a terminal. [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

| Skill | Role |
|-------|------|
| `/sdlc-spdd-whereami` | orient: team registry, phase, next command |
| `/sdlc-spdd-init` | initialize project context |
| `/sdlc-spdd-plan` | turn a requirement into a canvas |
| `/sdlc-spdd-architect` | harden design before coding |
| `/sdlc-spdd-code` | implement one approved operation |
| `/sdlc-spdd-review` | compare implementation to canvas |
| `/sdlc-spdd-prompt-update` | update canvas first when intent changes |
| `/sdlc-spdd-retro` | capture learnings |
| `/sdlc-spdd-sync` | reconcile implementation reality with canvas |

## Main Scripts

| Script | Role |
|--------|------|
| `setup-agent-prompts.sh` | install the combined framework into a target app |
| `upgrade-project.sh` | upgrade framework-owned files in an older install |
| `sdlc.sh` | daily workflow CLI: pointer, phases, claim, capture, team |
| `start-agent-session.sh` | generate a session handoff brief (low-level; prefer `sdlc.sh start`) |
| `resync-agent-session.sh` | check or reconcile canvas drift |
| `capture-session-memory.sh` | persist session outcomes (low-level; prefer `sdlc.sh capture`) |
| `validate-reasons-canvas.sh` | validate canvas structure |

## How Work Flows Through the System

1. A request arrives from a person, Jira, GitHub Issue, or requirements file.
2. Triage (or `create-work-from-milestone.sh`) assigns a Work ID; `/sdlc-spdd-plan` creates the REASONS Canvas.
3. Architecture review checks that the plan is safe and structured.
4. Coding implements one operation from the canvas.
5. Review compares code to the canvas.
6. If requirements changed, prompt-update modifies the canvas before code changes.
7. If implementation details drifted, sync reconciles the canvas after review.
8. Retro and memory capture make lessons available to future sessions.

## What This Is Not

SDLC-SPDD Orchestrator is not:

- a compiled agent runtime.
- a replacement for Cursor, GitHub Copilot, or Claude Code.
- a replacement for Jira or GitHub Issues.
- a full clone of SDLC Agents.
- a drop-in replacement for the upstream OpenSPDD CLI.

It is a repository-based operating model for disciplined AI-assisted delivery.

## Read Next

- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md)
- [Installing into your project](installing-into-your-project.md)
- [Maintaining your project](maintaining-your-project.md)
- [Top useful concepts and commands](useful-concepts-and-commands.md)
