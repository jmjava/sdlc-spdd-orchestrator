# Agent Session Scripts

These scripts make the hybrid SDLC Agents + SPDD workflow runnable across agent sessions.

They solve three operational needs:

1. Set up assistant prompts, playbooks, memory, sessions, and SPDD folders.
2. Resync a new agent session with previous work.
3. Persist current session learning into durable memory.

## Script Overview

| Script | Purpose |
|--------|---------|
| `scripts/setup-agent-prompts.sh` | Integrated setup for folders, memory, sessions, playbooks, Cursor prompts, and Copilot prompts |
| `scripts/upgrade-project.sh` | Framework-only upgrade for older initialized projects without overwriting implementation files or existing memory |
| `scripts/sdlc-spdd/start-agent-session.sh` | Target-local script that creates a session brief for a new agent |
| `scripts/sdlc-spdd/resync-agent-session.sh` | Target-local script that checks or reconciles feature/canonical canvases, validates the canvas, and creates a session brief |
| `scripts/sdlc-spdd/capture-session-memory.sh` | Target-local script that persists current session summary, validation, decisions, pitfalls, patterns, and next steps |
| `scripts/sdlc-spdd/sync-agent-context.sh` | Target-local low-level canvas copy synchronization |
| `scripts/sdlc-spdd/validate-reasons-canvas.sh` | Target-local REASONS Canvas structure validation |

## 1. Set Up Prompts and Memory

Run this from the SDLC-SPDD orchestrator repository:

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all

Equivalent explicit setup:

    ./scripts/init-project.sh --target /path/to/app --cursor --copilot

The target app receives:

- `requirements/`
- `spdd/canvas/`
- `spdd/tasks/`
- `spdd/reviews/`
- `spdd/sync/`
- `agent-context/memory/`
- `agent-context/playbooks/`
- `agent-context/features/`
- `agent-context/sessions/`
- `agent-context/harness/`
- `docs/sdlc-spdd/`
- `.cursor/commands/`
- `.github/copilot-instructions.md`
- `.github/prompts/`
- `scripts/sdlc-spdd/` runtime session scripts

## Upgrade an Older Installation

Run this from the SDLC-SPDD orchestrator repository:

    ./scripts/upgrade-project.sh --target /path/to/app --all

Preview first:

    ./scripts/upgrade-project.sh --target /path/to/app --all --dry-run

The upgrade updates framework-owned prompts, playbooks, harness files, target-local docs under `docs/sdlc-spdd/`, and target-local runtime scripts. It preserves application source, application docs outside `docs/sdlc-spdd/`, requirements, canvases, feature workspaces, reviews, sync logs, and existing memory content.

## 2. Start a New Agent Session

Create a session brief before asking a new agent to continue work:

    cd /path/to/app
    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code

This writes:

    agent-context/sessions/<timestamp>-code-FEAT-001-order-status-api.md
    agent-context/sessions/current-session.md

The brief includes:

- Work ID
- phase
- recommended command
- canvas sync state
- artifact status
- memory files to read
- playbooks to consider
- git status
- copy/paste resume prompt

Then invoke the assistant with:

    For FEAT-001-order-status-api, read @agent-context/sessions/current-session.md and continue with the recommended command.

## 3. Resync Previous Work

Check whether the feature workspace canvas and canonical canvas match:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id FEAT-001-order-status-api --check-only

If the canonical `spdd/canvas/` copy is authoritative:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id FEAT-001-order-status-api --from-canvas --force --phase code

If the feature workspace copy is authoritative:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id FEAT-001-order-status-api --from-feature --force --phase code

The script:

1. Runs `sync-agent-context.sh`.
2. Validates the canonical canvas.
3. Creates a fresh session brief for the requested phase.

## 4. Capture Current Session Memory

At the end of a session, persist what happened:

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id FEAT-001-order-status-api \
      --phase code \
      --summary "Implemented operation T01 for order status lookup." \
      --validation "mvn test" \
      --decisions "Status lookup stays in OrderStatusService." \
      --pitfalls "Legacy orders may not have status history." \
      --patterns "Use focused service tests for status transitions." \
      --next "/sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md"

This updates:

- `agent-context/memory/session-history.md`
- `agent-context/features/<WORK-ID>/progress-log.md`
- `agent-context/memory/project-memory.md`
- `agent-context/memory/architecture-decisions.md` when `--decisions` is provided
- `agent-context/memory/known-pitfalls.md` when `--pitfalls` is provided
- `agent-context/memory/reusable-patterns.md` when `--patterns` is provided
- `agent-context/sessions/current-session.md` when present

## Recommended Daily Loop

Start or resume:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only
    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>

Invoke the SDLC-SPDD skill:

    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01

Review and sync:

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Capture memory:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>" --validation "<tests>" --next "<next command>"

## Hybrid Contract

The scripts enforce the combined system:

- SDLC Agents side: phase-specific handoffs, progressive context loading, playbook selection, and persistent learning.
- SPDD side: REASONS Canvas validation, prompt-first behavior changes, canvas sync, and reviewable artifacts.

Use `capture-session-memory.sh` after meaningful work so future agents do not rely on chat history.
