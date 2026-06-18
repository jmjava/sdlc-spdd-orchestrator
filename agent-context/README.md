# Agent Context

This folder holds project memory, feature workspaces, playbooks, and quality harness files for SDLC-SPDD agents.

## Layout

- `memory/` — durable project context and retrieval indexes
- `playbooks/` — repeatable workflows by work type
- `features/` — per-work workspaces
- `sessions/` — generated session briefs and current-session handoffs
- `harness/` — validation rules and quality gates

### Memory and indexes

- `memory/project-memory.md`, `architecture-decisions.md`, `known-pitfalls.md`,
  `reusable-patterns.md` — durable knowledge.
- `memory/session-history.md` — recent session window (rotated; older entries in
  `memory/archive/`).
- `memory/sessions/` — one immutable file per captured session (full detail).
- `memory/session-index.md` — newest-first session index (Work ID + Areas columns).
- `memory/code-area-index.md` — reverse index: code area → work/sessions, for
  relevance-based retrieval. The agent determines a session's code areas by
  matching the prose REASONS Canvas to the code, and records them with
  `capture-session-memory.sh --areas`.

Retrieve by relevance, not recency: start at `sessions/current-session.md`, scope
to one Work ID, and filter the indexes by code area. See
`docs/context-loading-and-scaling.md` (installed at `docs/sdlc-spdd/`).

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
