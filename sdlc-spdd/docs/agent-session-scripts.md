# Agent Session Scripts

These scripts make the hybrid SDLC Agents + SPDD workflow runnable across agent sessions.

They solve four operational needs:

1. Set up assistant prompts, playbooks, contracts, and SPDD folders.
2. Resync a new agent session with previous work.
3. Persist current session learning — captures stage quietly, accepts promote
   to the committed lessons ledger ([Storage v3](storage-v3.md)).
4. Connect session summaries to `ROADMAP.md`, `milestone-*.md`, and `session-notes/`.

## Script Overview

| Script | Purpose |
|--------|---------|
| `scripts/setup-agent-prompts.sh` | Integrated setup for folders, contracts, playbooks, Cursor prompts, Copilot prompts, and Claude Code commands |
| `scripts/upgrade-project.sh` | Framework-only upgrade for older initialized projects without overwriting implementation files or existing memory |
| `sdlc-spdd/scripts/sdlc.sh` | Workflow CLI: `next`, `claim`, `resume`, `advance`, `skip`, `shelf`, `sync`, `capture`, `accept`, `team`, `list-work`, `archive`, `gate`, `db`, `issues`, `local`, `quick` |
| `sdlc-spdd/scripts/start-agent-session.sh` | Target-local script that creates a session brief for a new agent |
| `sdlc-spdd/scripts/resync-agent-session.sh` | Target-local script that checks or reconciles the canonical canvas, validates it, and creates a session brief |
| `sdlc-spdd/scripts/capture-session-memory.sh` | Stage session summary, decisions/pitfalls/patterns, and optional metrics as lesson records in `.sdlc/staged/lessons.jsonl` |
| `sdlc-spdd/scripts/accept-lessons.sh` | Promote staged lesson records into the committed `spdd/memory/lessons.jsonl` (also `sdlc.sh accept`) |
| `sdlc-spdd/scripts/index-spdd-analysis.sh` | Stage an `analysis` lesson record from a Fowler analysis artifact |
| `sdlc-spdd/scripts/resolve-agent-context.sh` | Resolve SDLC Agents `#SkillName` / phase extensions for progressive loading |
| `sdlc-spdd/scripts/resolve-context-backend.sh` | Runtime probe: is the Guide DICE backend enabled and reachable? |
| `sdlc-spdd/scripts/create-work-from-milestone.sh` | Target-local script that maps milestone checklist items into SDLC-SPDD work artifacts |
| `sdlc-spdd/scripts/sync-roadmap-from-spdd.sh` | Target-local script that refreshes a managed roadmap summary from canvas metadata |
| `sdlc-spdd/scripts/summarize-session-notes.sh` | Target-local script that imports existing session notes as staged lesson records |
| `sdlc-spdd/scripts/sync-agent-context.sh` | Target-local low-level canvas copy synchronization |
| `sdlc-spdd/scripts/validate-command-adapters.sh` | Target-local checker that validates Cursor/Copilot/Claude Code command-pack parity in the installed project |
| `sdlc-spdd/scripts/verify-agent-command-effects.sh` | Target-local verifier for deterministic artifact side-effects after `/sdlc-spdd-*` command invocations and post-capture planning sync |
| `sdlc-spdd/scripts/validate-reasons-canvas.sh` | REASONS Canvas structure validation (+ optional readiness vocabulary) |
| `sdlc-spdd/scripts/validate-requirements-format.sh` | Jira-compatible requirements frontmatter / Work ID reference checks |
| `sdlc-spdd/scripts/verify-project-install.sh` | Target-local three-part install verification (Planning, SPDD, SDLC) |

## 1. Set Up Prompts and Memory

Run this from the SDLC-SPDD orchestrator repository:

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all

Equivalent explicit setup:

    ./scripts/init-project.sh --target /path/to/app --cursor --copilot --claude

For backward compatibility, omitting assistant flags installs Cursor and
GitHub Copilot only. Use `--all` or `--claude` to include Claude Code.

The target app receives a single framework folder plus adapter stubs at the
repo root (see the [install layout diagram](diagrams/09-install-layout.svg) and
[Installing into your project](installing-into-your-project.md)):

- `sdlc-spdd/` — the framework home:
  - `requirements/` and `requirements/milestones/`
  - `spdd/` — `canvas/`, `analysis/`, `tasks/`, `reviews/`, `sync/`, and
    `memory/` (the `lessons.jsonl` ledger + `registry.jsonl`)
  - `harness/` and `harness/skills/`
  - `scripts/` — installed workflow CLI and session scripts
  - `ROADMAP.md`, milestone definition, `session-notes/`
  - `.sdlc/` — gitignored runtime (sessions, staged captures, optional sqlite)
- Repo-root adapter stubs: `.cursor/commands/`, `.github/copilot-instructions.md`,
  `.github/prompts/`, `CLAUDE.md` + `.claude/commands/`
- `.github/workflows/validate-sdlc-spdd-adapters.yml` when both Cursor and
  Copilot adapters are installed
- `docs/sdlc-spdd/` — target-local copies of these docs

## Upgrade an Older Installation

Run this from the SDLC-SPDD orchestrator repository:

    ./scripts/upgrade-project.sh --target /path/to/app --all

Preview first:

    ./scripts/upgrade-project.sh --target /path/to/app --all --dry-run

The upgrade updates framework-owned prompts, harness/skills files, target-local docs under `docs/sdlc-spdd/`, and target-local runtime scripts. It preserves application source, application docs outside `docs/sdlc-spdd/`, requirements, canvases, reviews, sync logs, the lessons ledger, existing root `CLAUDE.md`, and target workflow customizations. Legacy memory layouts are converted by `sdlc-engine storage migrate` — see [Framework upgrade](framework-upgrade.md).

## 2. Start a New Agent Session

Create a session brief before asking a new agent to continue work. This is the
**session bootstrap**: it combines automatic Tier 1 grounding (already loaded on
every request) with work-specific context, a bounded Related Past Work digest
from the ledger, and Framework Orientation pointers.

See [Bootstrap and retrieval-based loading](context-loading-and-scaling.md#bootstrap-and-index-based-loading).

    cd /path/to/app
    ./sdlc-spdd/scripts/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code

With an explicit milestone:

    ./sdlc-spdd/scripts/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code --milestone milestone-1.md

Session-brief rotation (keeps `.sdlc/sessions/` bounded — **hot path, gitignored**):

- `--session-limit <n>` — keep at most N timestamped briefs; older move to
  `.sdlc/sessions/archive/` (default 20). `current-session.md` is never archived.
- `--no-session-rotate` — leave prior timestamped briefs in place.

This writes:

    .sdlc/sessions/<timestamp>-code-FEAT-001-order-status-api.md
    .sdlc/sessions/current-session.md

See [Runtime and ledger](runtime-and-ledger.md).

The brief includes:

- **Framework Orientation** — how to operate within SDLC-SPDD (grounding, docs, retrieval)
- Work ID, phase, active milestone (explicit `--milestone` or auto-detected)
- recommended command (honors [quiet mode](quiet-mode.md))
- canvas sync state, roadmap and milestone status, artifact status
- **Related Past Work digest** — counts + top lesson titles with ids from the
  ledger (fetch bodies on demand; query menu included)
- **Resolved Context** (phase harness files, skills, Work ID artifacts)
- optional **Local SQLite Index** snapshot (when the sqlite cache is enabled)
- git status
- copy/paste resume prompt with SDLC, SPDD, and planning-layer `@` references

Then paste the **Resume Prompt** from `.sdlc/sessions/current-session.md`. See [Session prompt standard](session-prompt-standard.md), [SPDD prompt standard](spdd-prompt-standard.md), and [Planning prompt standard](planning-prompt-standard.md).

## 3. Resync Previous Work

### Script paths

| Context | Path |
|---------|------|
| This orchestrator repository (development) | `./scripts/<script>.sh` |
| Installed target application | `./sdlc-spdd/scripts/<script>.sh` |

User-facing docs use the target path. When developing here, drop the `sdlc-spdd/` segment.

### Check only (no session brief)

Check the canonical canvas and validate it:

    ./sdlc-spdd/scripts/resync-agent-session.sh --target . --work-id FEAT-001-order-status-api --check-only

`--check-only` runs sync check and canvas validation, then stops. It does **not** create a session brief. Run `start-agent-session.sh` next.

### Reconcile drift (creates session brief)

If drift exists, reconcile and create a session brief in one step. **Default:** canonical `spdd/canvas/<WORK-ID>.md` is authoritative:

    ./sdlc-spdd/scripts/resync-agent-session.sh --target . --work-id FEAT-001-order-status-api --from-canvas --force --phase code

When reconciling, you do **not** need a separate `start-agent-session.sh` call — resync creates the brief.

The reconcile path:

1. Runs `sync-agent-context.sh`.
2. Validates the canonical canvas.
3. Creates a fresh session brief for the requested `--phase`.

## 4. Capture Current Session Memory

At the end of a session (or whenever something worth remembering happens),
stage it. The script **parses session content** (summary, hot brief, canvas,
analysis, `session-notes/`, and capture flags) for path and package tokens to
resolve **code areas**, then writes lesson records to the gitignored stage —
**no git noise**:

    ./sdlc-spdd/scripts/capture-session-memory.sh \
      --target . \
      --work-id FEAT-001-order-status-api \
      --phase code \
      --summary "Implemented T01 in com.acme.order: order status lookup in OrderStatusService." \
      --validation "mvn test" \
      --milestone milestone-1.md \
      --roadmap-note "FEAT-001 completed its first implementation operation." \
      --decisions "Status lookup stays in OrderStatusService." \
      --pitfalls "Legacy orders may not have status history." \
      --patterns "Use focused service tests for status transitions." \
      --next "/sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md"

This stages:

- a `session` record (summary, validation, next step, areas, optional metrics)
- a `decision` / `pitfall` / `pattern` record for each corresponding flag

into `.sdlc/staged/lessons.jsonl`, and appends a Captured Memory note to the
hot brief. Optional committed planning updates still happen when requested:
`--milestone` appends milestone progress, `--roadmap-note` appends to
`ROADMAP.md`, `--session-note` writes `session-notes/YYYY-MM-DD.md`.

Optional capture metrics are recorded in the session record body:
`--readiness`, `--review-result` (`pass|fail|mixed|blocked`), `--rework`,
`--context-files`, `--validate-cycles`, `--review-cycles`. When `--readiness`
is omitted, capture auto-fills from the canvas Metadata `- Readiness:` or YAML
`readiness:` value when present. Use `--areas` only to override or supplement
parsed areas, and `--dry-run` to preview the staged records.

### Accept at the gate

Staged records are promoted to the committed ledger at retro/sync via
`/sdlc-spdd-accept`, which reviews them for consistency and coherence first:

    ./sdlc-spdd/scripts/sdlc.sh accept --list                  # what is staged
    ./sdlc-spdd/scripts/sdlc.sh accept --work-id <WORK-ID>     # promote for one Work ID
    ./sdlc-spdd/scripts/sdlc.sh accept --ids <a,b,c> --discard-rest

Accept dedupes by id, drains the stage, re-derives the sqlite/Guide
projections, and leaves `spdd/memory/lessons.jsonl` ready to git-stage — one
batched human commit per gate. Never edit the ledger by hand.
See [Storage v3 — stage-then-accept](storage-v3.md#stage-then-accept).

## Recommended Daily Loop

Orient and claim:

    ./sdlc-spdd/scripts/sdlc.sh next
    ./sdlc-spdd/scripts/sdlc.sh claim <WORK-ID>    # appends to spdd/memory/registry.jsonl; commit it on shared repos

Start or resume:

    ./sdlc-spdd/scripts/sdlc.sh resume <WORK-ID> [--phase <phase>]
    ./sdlc-spdd/scripts/sdlc.sh start

Optional canvas sync check:

    ./sdlc-spdd/scripts/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

Invoke the SDLC-SPDD skill:

    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01

After completing a phase step:

    ./sdlc-spdd/scripts/sdlc.sh advance
    ./sdlc-spdd/scripts/sdlc.sh advance --force   # override Ready For Coding gate into code

Review and sync:

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Capture (stages quietly) and accept at the gate:

    ./sdlc-spdd/scripts/sdlc.sh capture --summary "<summary>" --validation "<tests>" --next "<next command>"
    /sdlc-spdd-accept          # review + promote staged records, git-stage the ledger

Map milestone planning into SPDD work:

    ./sdlc-spdd/scripts/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

Refresh roadmap from SPDD canvases:

    ./sdlc-spdd/scripts/sync-roadmap-from-spdd.sh --target .

Full loop diagram: [daily loop](diagrams/11-daily-loop.svg).

## 5. Index Analysis Context (Fowler Step 3)

After `/sdlc-spdd-analysis` writes `spdd/analysis/<WORK-ID>-analysis.md`, stage
an `analysis` lesson record so future retrieval finds the keywords and areas:

    ./sdlc-spdd/scripts/index-spdd-analysis.sh --target . --work-id <WORK-ID>

See [Context loading and scaling](context-loading-and-scaling.md).

## 6. Resolve Skills and Phase Context (SDLC Agents)

Resolve which harness and skill files to load — do not list whole directories:

    ./sdlc-spdd/scripts/resolve-agent-context.sh --target . --phase code --work-id <WORK-ID>
    ./sdlc-spdd/scripts/resolve-agent-context.sh --target . --text "Implement retry #TDD #java !Kafka"
    ./sdlc-spdd/scripts/resolve-agent-context.sh --list-skills

`start-agent-session.sh` embeds resolve output under **Resolved Context** in
`current-session.md` and passes `--work-id` when set. See [SDLC Agents and the framework](sdlc-agents-and-the-framework.md).

For cross-work lessons, use retrieval instead of file resolution:
`sdlc-engine context retrieve` or (when Guide is live) the `spdd_*` MCP tools —
see [Context loading and scaling](context-loading-and-scaling.md).

## Hybrid Contract

The scripts enforce the combined system:

- SDLC Agents side: phase-specific handoffs, progressive context loading, skill selection, and persistent learning.
- SPDD side: REASONS Canvas validation, prompt-first behavior changes, canvas sync, and reviewable artifacts.

Use `capture-session-memory.sh` after meaningful work so future agents do not rely on chat history — and `/sdlc-spdd-accept` at gates so the ledger stays the reviewed system of record.

You can verify both command effects and planning sync:

    ./sdlc-spdd/scripts/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step review
    ./sdlc-spdd/scripts/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step capture --milestone milestone-1.md --require-roadmap
