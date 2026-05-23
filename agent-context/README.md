# Agent Context

This folder holds project memory, feature workspaces, playbooks, and quality harness files for SDLC-SPDD agents.

## Layout

- `memory/` — durable project context
- `playbooks/` — repeatable workflows by work type
- `features/` — per-work workspaces
- `harness/` — validation rules and quality gates

## Canonical Copies

Each work item also has a canonical canvas under `spdd/canvas/`. Keep both copies aligned using `/sdlc-spdd-sync` or `./scripts/sync-agent-context.sh`.
