# Agent Context

This folder holds project memory, feature workspaces, harness skills, and quality harness files for SDLC-SPDD agents.

## Layout

- `memory/` — durable project context and retrieval indexes
- `harness/skills/` — phase-matching and `#SkillName` skills; resolve with `resolve-agent-context.sh`
- `features/` — per-work workspaces
- `sessions/` — generated session briefs and current-session handoffs
- `harness/` — validation rules, quality gates, and `phase-index.md`

### Memory and indexes

**Durable knowledge** (append-only, area-tagged at capture when areas are known):

- `memory/project-memory.md`, `architecture-decisions.md`, `known-pitfalls.md`,
  `reusable-patterns.md`

### Bootstrap and index-based loading

Bootstrap orients the agent; indexes make selective loading scale. Together they
replace directory scans and chronological history reads.

| Step | Action |
|------|--------|
| Install | `setup-agent-prompts.sh` — grounding, memory seeds, `harness/phase-index.md`, scripts |
| Every request | Tier 1 grounding loads automatically (operating model + index rules) |
| Every session | `start-agent-session.sh` → read `sessions/current-session.md` (Framework Orientation + Resume Prompt) |
| Before coding in an area | Filter `memory/domain-index.md` by keyword, then `memory/context-index.md` by Area |
| After analysis | Run `index-spdd-analysis.sh` to index domain keywords and code areas |
| Phase known, area not yet | Use `harness/phase-index.md` + phase-matching skills |
| At capture | Script parses session content (summary, `session-notes/`, analysis, canvas, …) for categories |

**Indexes** (read these instead of scanning directories):

| File | When to use |
|------|-------------|
| `memory/code-areas.md` | At capture — known categories; match session content here first |
| `memory/domain-index.md` | Fowler/Troy scoped scan — filter by domain keyword before reading code |
| `memory/context-index.md` | Before touching code — filter by Area; Kinds: analysis, session, decision, pitfall, pattern, metric |
| `memory/session-index.md` | Session-only view — filter by Work ID or Area, newest first |
| `harness/phase-index.md` | Phase-known — core harness files and planning artifacts by SDLC phase |

**Supporting artifacts:** `memory/sessions/` (per-session detail),
`memory/session-history.md` (recent window only; archive for older entries).

Full detail: [Bootstrap and index-based loading](../docs/context-loading-and-scaling.md#bootstrap-and-index-based-loading). Why narrow context matters: [Chelsea Troy and the framework](../docs/chelsea-troy-and-the-framework.md), [SDLC Agents progressive disclosure](../docs/sdlc-agents-and-the-framework.md).

## Canonical Copies

Each work item also has a canonical canvas under `spdd/canvas/`. Keep both copies aligned using `/sdlc-spdd-sync` or `./scripts/sync-agent-context.sh`.

## SDLC Pointer (current chore/task)

**Quick start:** `./scripts/sdlc.sh` (or `./scripts/sdlc.sh next`) shows what to do now.
In chat: `/sdlc-next` or `/sdlc-spdd-whereami`. Workflow chat wrappers for the same
CLI: `/sdlc-claim`, `/sdlc-shelf`, `/sdlc-advance`, `/sdlc-next`, `/sdlc-team`.

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

## SDLC Workflow (phase + gate tracking)

**Python engine (v2, opt-in):** set `SDLC_ENGINE=python` (or `auto`) on
`scripts/sdlc.sh` / `scripts/sdlc-spdd/sdlc.sh` to use `engine/sdlc_engine`.
Default remains the bash workflow. See [docs/engine-v2.md](../docs/engine-v2.md).

**Local/offline sessions:** if an agent starts work without a documented FEAT/SPIKE,
do **not** invent one. Start a machine-private session instead (always routed to
the Python engine, even when `SDLC_ENGINE=shell`):

```bash
./scripts/sdlc.sh local start --name <slug> --intent "why this scratch work"
./scripts/sdlc.sh local capture --summary "interim note"
./scripts/sdlc.sh local promote --type feature --name "Documented title"
```

**Local SQLite index (pre-GUIDE):** regenerable query cache in `.sdlc/index.sqlite`
(gitignored). Multi-user sync stays git — rebuild after pull. See
[docs/local-sqlite-index.md](../docs/local-sqlite-index.md).

```bash
./scripts/sdlc.sh db rebuild
./scripts/sdlc.sh db query --search "orchestration"
```

```bash
SDLC_ENGINE=python ./scripts/sdlc.sh links
SDLC_ENGINE=python ./scripts/sdlc.sh sync-links --repair
SDLC_ENGINE=python ./scripts/sdlc.sh issues push <WORK-ID> --system github --apply
```

**Short commands** (installed at `scripts/sdlc-spdd/sdlc.sh`; orchestrator repo: `scripts/sdlc.sh`):

```bash
./scripts/sdlc.sh              # what to do now (default)
./scripts/sdlc.sh next           # concise orientation
./scripts/sdlc.sh status         # full dashboard (auto-syncs)
./scripts/sdlc.sh status --json  # machine-readable status
./scripts/sdlc.sh start          # open session brief at current phase
./scripts/sdlc.sh resume FEAT-001-order-status-api
./scripts/sdlc.sh advance
./scripts/sdlc.sh skip api-test --reason "no HTTP surface"
./scripts/sdlc.sh sync           # re-read artifacts into workflow state
./scripts/sdlc.sh shelf --reason "blocked"
./scripts/sdlc.sh list-shelved
./scripts/sdlc.sh list-work      # discover Work IDs in the repo
./scripts/sdlc.sh capture --summary "finished T02"   # pointer-guarded
./scripts/sdlc.sh sync-team      # mark done/cancelled from canvas Final Status
./scripts/sdlc.sh archive <ID>   # move Complete/Cancelled work into archive/
./scripts/sdlc.sh archive --all  # archive every eligible Complete/Cancelled Work ID
```

In **code** phase, the next canvas operation (`T01`, `T02`, …) is inferred automatically from the REASONS Canvas.

The workflow manager builds on the pointer to answer **where am I?**, **what is next?**,
and **how do I shelf or resume work?** State lives under `.sdlc/workflows/` (local,
gitignored). Committed artifacts (`progress-log.md`, canvas, reviews) remain the audit trail;
run `sync` to reconcile workflow state from those files.

```bash
# Where am I on the current task?
./agent-context/sdlc-workflow.sh status

# Pick up a shelved task (auto-shelves the current pointer if different)
./agent-context/sdlc-workflow.sh resume FEAT-001-order-status-api

# Resume at a specific phase (e.g. after intentionally skipping ahead)
./agent-context/sdlc-workflow.sh resume FEAT-001-order-status-api --phase code

# Move to the next phase after finishing a step
./agent-context/sdlc-workflow.sh advance

# Jump ahead to a later phase
./agent-context/sdlc-workflow.sh advance --to review

# Skip a phase with a recorded reason
./agent-context/sdlc-workflow.sh skip api-test --reason "no HTTP surface"

# Park current work and clear the pointer
./agent-context/sdlc-workflow.sh shelf --reason "blocked on dependency"

# Re-read canvas, progress log, and session brief into workflow state
./agent-context/sdlc-workflow.sh sync

# List shelved work ids
./agent-context/sdlc-workflow.sh list-shelved
```

`start-agent-session.sh` and `capture-session-memory.sh` update workflow timestamps
automatically. After shelving, run `resume <WORK-ID>` then `start-agent-session.sh`
with the suggested phase to sync back into the chat workflow.

## Team Work ID sharing

Local pointer (`.sdlc/`) is private to your machine. **Team coordination** uses the
committed file `agent-context/work-registry.tsv` — commit it after claim/release so
teammates see who is on which Work ID, phase, and operation.

```bash
./scripts/sdlc.sh list-work              # discover Work IDs in the repo
./scripts/sdlc.sh team                   # team registry + your pointer
./scripts/sdlc.sh claim FEAT-001-alpha   # resume + register as active owner
./scripts/sdlc.sh release --reason "handoff to QA"
# Take over a teammate's active claim (after coordinating with them):
./scripts/sdlc.sh claim OTHER-ID --force
./scripts/sdlc.sh resume OTHER-ID --force   # equivalent takeover via resume
```

Set `SDLC_USER="Jane"` to label registry rows. Set `SDLC_NO_TEAM_REGISTRY=1` to opt out.

**Stale claims:** active rows older than `SDLC_TEAM_STALE_DAYS` (default 7) show `[STALE>Nd]` in
`team` / `list-work`. Stale claims warn but do not block; non-stale claims block until
`claim --force` or `resume --force`.

**Done / cancelled status:** canvases with `## Final Status` → `Status: Complete` are marked `done`,
and `Status: Cancelled` / `Canceled` are marked `cancelled`, when you run `team`, `list-work`, or
`sync-team`.

**Archive completed/cancelled work** (keeps milestones in place; moves canvases, feature workspaces,
analysis/review/sync, and matching session briefs under `archive/`):

```bash
./scripts/sdlc.sh archive FEAT-001-alpha
./scripts/sdlc.sh archive --all
./scripts/sdlc.sh archive FEAT-001-alpha --dry-run
./scripts/sdlc.sh archive FEAT-001-alpha --force   # non-terminal Final Status
```

**Branch / PR / Jira linking** (stored in the `note` column):

```bash
./scripts/sdlc.sh claim FEAT-001 --branch cursor/feat-001 --pr "#21" --jira "PROJ-123"
# auto-detects current git branch on claim (disable: SDLC_TEAM_AUTO_BRANCH=0)
# auto-reads Jira Key from requirements/milestones/<WORK-ID>.md ## Jira (disable: SDLC_TEAM_AUTO_JIRA=0)
```

Jira **draft syntax** for issue creation lives in `requirements/milestones/<WORK-ID>.md` under
`## Jira`. Set `- Key: ABC-123` after create; `list-work` shows `jira:ABC-123` or `jira draft`.

**Session / orientation prompts:** `start-agent-session.sh`, `sdlc.sh next`, and `/sdlc-spdd-whereami`
resolve Jira via `sdlc_team_jira_status`. When the key is `missing` or `draft`, the Resume Prompt and
`next` output instruct the agent to ask the user for a key (then `claim --jira KEY`). Disable with
`SDLC_SESSION_ASK_JIRA=0`.

**Notifications:** copy `agent-context/hooks/notify-team-registry.example.sh` and set:

```bash
export SDLC_TEAM_REGISTRY_HOOK=./agent-context/hooks/notify-team-registry.sh
export SDLC_TEAM_SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

## Session Persistence

Use scripts to keep agent sessions durable across chat boundaries:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>
    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only
    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>"

The current handoff lives at:

    agent-context/sessions/current-session.md

Durable session history lives at:

    agent-context/memory/session-history.md
