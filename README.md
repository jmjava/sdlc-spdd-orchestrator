# SDLC-SPDD Orchestrator

A multi-assistant scaffold for disciplined AI-assisted delivery.

SDLC-SPDD Orchestrator combines:

- **SDLC Agents** ideas: role-separated lifecycle, architecture-first handoffs, progressive context loading, agent memory, and retros.
- **SPDD / REASONS Canvas** ideas: versioned prompt contracts, prompt-first behavior changes, and closed-loop sync between prompt artifacts and code.
- **Project planning artifacts**: `ROADMAP.md`, `milestone-*.md`, and `session-notes/` as the human-readable planning and progress layer.

## Start Here

If you are new, read these in order:

1. [First day with SDLC-SPDD](docs/first-day-with-sdlc-spdd.md)
2. [10,000-foot view](docs/ten-thousand-foot-view.md)
3. [Installing into your project](docs/installing-into-your-project.md)
4. [Top useful concepts and commands](docs/useful-concepts-and-commands.md)
5. [Maintaining your project](docs/maintaining-your-project.md)

For the full documentation map, see [docs/README.md](docs/README.md).

## The Operating Model

The system uses a three-layer flow:

    ROADMAP.md / milestone-*.md / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

| Layer | Purpose | Examples |
|-------|---------|----------|
| Planning narrative | Human-readable roadmap, milestone, and daily session story | `ROADMAP.md`, `milestone-1.md`, `session-notes/2026-06-06.md` |
| Governed agent context | Work-item contract, memory, handoffs, and reusable context | `spdd/canvas/<WORK-ID>.md`, `agent-context/memory/`, `agent-context/sessions/` |
| Implementation evidence | Code, review outputs, sync logs, and validation | source files, `spdd/reviews/`, `spdd/sync/`, tests |

## Install into an Application

Clone this repo:

    git clone https://github.com/jmjava/sdlc-spdd-orchestrator.git
    cd sdlc-spdd-orchestrator

Install the complete system into a target project:

    ./scripts/setup-agent-prompts.sh --target /path/to/your/project --all

This installs:

- Cursor commands and GitHub Copilot prompt files.
- target-local runtime scripts under `scripts/sdlc-spdd/`.
- local SDLC-SPDD docs under `docs/sdlc-spdd/`.
- planning scaffolding: `ROADMAP.md`, `milestone-1.md`, and `session-notes/` when missing.
- SPDD and agent context folders: `spdd/` and `agent-context/`.

Upgrade an existing target project without overwriting application source, canvases, feature workspaces, existing memory, roadmap, milestones, or session notes:

    ./scripts/upgrade-project.sh --target /path/to/your/project --all

## Day-One Flow

In the target project:

    /sdlc-spdd-init

If you already have milestone checklist items, map them into SDLC-SPDD work:

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

Start or resume an agent session:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-my-feature --phase plan

Plan, architect, code, and review one operation:

    /sdlc-spdd-plan @requirements/my-feature.md @ROADMAP.md @milestone-1.md
    /sdlc-spdd-architect @spdd/canvas/FEAT-001-my-feature.md
    /sdlc-spdd-code @spdd/canvas/FEAT-001-my-feature.md operation T01
    /sdlc-spdd-review @spdd/canvas/FEAT-001-my-feature.md

Capture session memory and milestone progress:

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id FEAT-001-my-feature \
      --phase code \
      --summary "Completed T01" \
      --validation "tests passed" \
      --milestone milestone-1.md \
      --roadmap-note "FEAT-001 completed first implementation operation." \
      --next "/sdlc-spdd-review @spdd/canvas/FEAT-001-my-feature.md"

Refresh the roadmap summary from SPDD canvases:

    ./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .

## Core Assistant Commands

| Command | Use it for |
|---------|------------|
| `/sdlc-spdd-init` | Initialize project context |
| `/sdlc-spdd-plan` | Convert a requirement, issue, or milestone item into a REASONS Canvas |
| `/sdlc-spdd-architect` | Harden the canvas before coding |
| `/sdlc-spdd-code` | Implement one approved operation |
| `/sdlc-spdd-review` | Compare implementation to the canvas |
| `/sdlc-spdd-prompt-update` | Update the canvas first when behavior or acceptance criteria change |
| `/sdlc-spdd-retro` | Capture reusable learnings |
| `/sdlc-spdd-sync` | Reconcile accepted implementation drift back into prompt artifacts |

## Core Scripts

| Script | Use it for |
|--------|------------|
| `scripts/setup-agent-prompts.sh` | Install the framework into a target project |
| `scripts/upgrade-project.sh` | Upgrade framework-owned files in an existing target project |
| `scripts/sdlc-spdd/start-agent-session.sh` | Create a current-session handoff for a new agent |
| `scripts/sdlc-spdd/resync-agent-session.sh` | Check or reconcile feature/canonical canvas drift |
| `scripts/sdlc-spdd/capture-session-memory.sh` | Persist session summary, validation, decisions, pitfalls, patterns, and next steps |
| `scripts/sdlc-spdd/create-work-from-milestone.sh` | Map milestone checklist items to Work IDs, requirements, feature workspaces, and draft canvases |
| `scripts/sdlc-spdd/sync-roadmap-from-spdd.sh` | Refresh a managed roadmap summary from SPDD canvas metadata |
| `scripts/sdlc-spdd/summarize-session-notes.sh` | Import existing daily session notes into durable memory |

## Repository Layout

| Path | Purpose |
|------|---------|
| `docs/` | User guides, onboarding path, runbooks, and reference docs |
| `scripts/` | Install, upgrade, validation, and target-local runtime script templates |
| `templates/` | REASONS Canvas templates, Cursor commands, Copilot prompts, stack rules, project-doc templates |
| `agent-context/` | Memory, playbooks, harness files, and framework-owned context templates |
| `examples/` | Reference workflows and sample projects |

## Documentation Paths

### New-user path

1. [First day with SDLC-SPDD](docs/first-day-with-sdlc-spdd.md)
2. [10,000-foot view](docs/ten-thousand-foot-view.md)
3. [Installing into your project](docs/installing-into-your-project.md)
4. [Top useful concepts and commands](docs/useful-concepts-and-commands.md)
5. [Maintaining your project](docs/maintaining-your-project.md)

### Daily operation

- [Workflow](docs/workflow.md)
- [Daily runbook](docs/daily-runbook.md)
- [Roadmap, milestones, and session notes](docs/roadmap-milestones-and-session-notes.md)
- [Agent session scripts](docs/agent-session-scripts.md)
- [Cheat sheet](docs/sdlc-spdd-cheat-sheet.md)

### Setup and upgrade

- [Installing into your project](docs/installing-into-your-project.md)
- [Framework upgrade](docs/framework-upgrade.md)
- [Cursor usage](docs/cursor-usage.md)
- [GitHub Copilot usage](docs/copilot-usage.md)

### Integrations and theory

- [Jira runbook](docs/jira-runbook.md)
- [Integration linking](docs/integration-linking.md)
- [Hybrid SDLC Agents + SPDD model](docs/hybrid-model.md)
- [SPDD compliance](docs/spdd-compliance.md)
- [Architecture](docs/architecture.md)
- [Design decisions](docs/design-decisions.md)

## What This Is Not

This is not a compiled multi-agent runtime and not a replacement for Cursor, GitHub Copilot, Jira, SDLC Agents, or OpenSPDD.

It is a repository-based operating model that makes AI-assisted work more governable, reviewable, and reusable.

## License

MIT

## Attribution

This project is inspired by:

- [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents): multi-agent software delivery lifecycle
- [OpenSPDD](https://github.com/gszhangwei/open-spdd): structured prompt-driven development and REASONS Canvas style design contracts

This project is not an official extension of either project unless that relationship is established later.
