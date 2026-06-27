# Agent Context

This folder holds project memory, feature workspaces, playbooks, and quality harness files for SDLC-SPDD agents.

## Layout

- `memory/` — durable project context and retrieval indexes
- `playbooks/` — repeatable workflows by work type
- `extensions/` — SDLC Agents-style rules (`_all-agents/`, `*-agent/`, `skills/`); resolve with `resolve-agent-context.sh`
- `features/` — per-work workspaces
- `sessions/` — generated session briefs and current-session handoffs
- `harness/` — validation rules and quality gates

### Memory and indexes

**Durable knowledge** (append-only, area-tagged at capture when areas are known):

- `memory/project-memory.md`, `architecture-decisions.md`, `known-pitfalls.md`,
  `reusable-patterns.md`

### Bootstrap and index-based loading

Bootstrap orients the agent; indexes make selective loading scale. Together they
replace directory scans and chronological history reads.

| Step | Action |
|------|--------|
| Install | `setup-agent-prompts.sh` — grounding, memory seeds, `phase-index.md`, scripts |
| Every request | Tier 1 grounding loads automatically (operating model + index rules) |
| Every session | `start-agent-session.sh` → read `sessions/current-session.md` (Framework Orientation + Resume Prompt) |
| Before coding in an area | Filter `memory/domain-index.md` by keyword, then `memory/context-index.md` by Area |
| After analysis | Run `index-spdd-analysis.sh` to index domain keywords and code areas |
| Phase known, area not yet | Use `memory/phase-index.md` |
| At capture | Script parses session content (summary, `session-notes/`, analysis, canvas, …) for categories |

**Indexes** (read these instead of scanning directories):

| File | When to use |
|------|-------------|
| `memory/code-areas.md` | At capture — known categories; match session content here first |
| `memory/domain-index.md` | Fowler/Troy scoped scan — filter by domain keyword before reading code |
| `memory/context-index.md` | Before touching code — filter by Area; Kinds: analysis, session, decision, pitfall, pattern |
| `memory/session-index.md` | Session-only view — filter by Work ID or Area, newest first |
| `memory/phase-index.md` | Phase-known — playbooks, harness, planning files by SDLC phase |

**Supporting artifacts:** `memory/sessions/` (per-session detail),
`memory/session-history.md` (recent window only; archive for older entries).

Full detail: [Bootstrap and index-based loading](../docs/context-loading-and-scaling.md#bootstrap-and-index-based-loading). Why narrow context matters: [Chelsea Troy and the framework](../docs/chelsea-troy-and-the-framework.md), [SDLC Agents progressive disclosure](../docs/sdlc-agents-and-the-framework.md).

## Canonical Copies

Each work item also has a canonical canvas under `spdd/canvas/`. Keep both copies aligned using `/sdlc-spdd-sync` or `./scripts/sync-agent-context.sh`.

## SDLC Pointer (current chore/task)

Agents can drift onto the wrong Work ID when several chores are open. The pointer
manager keeps a single active chore in `.sdlc/pointer` (local state; not committed)
and provides guarded wrappers so commands refuse to run against a stale pointer.

```bash
# Source once per shell (or let start-agent-session.sh set the pointer for you)
source agent-context/sdlc-pointer.sh

# Set / inspect / clear
./agent-context/sdlc-pointer.sh set CHORE-123
./agent-context/sdlc-pointer.sh get
./agent-context/sdlc-pointer.sh reset

# Guarded execution — exits 3 when the pointer does not match
run_against_pointer "CHORE-123" -- ./scripts/sdlc-spdd/capture-session-memory.sh --work-id CHORE-123 ...

# Optional bootstrap override on agent start
export SDLC_POINTER_OVERRIDE=CHORE-123
sdlc_init
```

`start-agent-session.sh` sets the pointer automatically when `--work-id` is provided.

## Session Persistence

Use scripts to keep agent sessions durable across chat boundaries:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>
    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only
    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>"

The current handoff lives at:

    agent-context/sessions/current-session.md

Durable session history lives at:

    agent-context/memory/session-history.md
