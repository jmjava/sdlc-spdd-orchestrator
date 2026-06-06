# Agent Context

This folder holds project memory, feature workspaces, playbooks, and quality harness files for SDLC-SPDD agents.

## Layout

- `memory/` — durable project context
- `playbooks/` — repeatable workflows by work type
- `features/` — per-work workspaces
- `sessions/` — generated session briefs and current-session handoffs
- `harness/` — validation rules and quality gates

## Canonical Copies

Each work item also has a canonical canvas under `spdd/canvas/`. Keep both copies aligned using `/sdlc-spdd-sync` or `./scripts/sync-agent-context.sh`.

## Session Persistence

Use scripts to keep agent sessions durable across chat boundaries:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>
    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only
    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>"

The current handoff lives at:

    agent-context/sessions/current-session.md

Durable session history lives at:

    agent-context/memory/session-history.md
