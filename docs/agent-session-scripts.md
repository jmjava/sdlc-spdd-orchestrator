# Agent Session Scripts

These scripts make the hybrid SDLC Agents + SPDD workflow runnable across agent sessions.

They solve three operational needs:

1. Set up assistant prompts, playbooks, memory, sessions, and SPDD folders.
2. Resync a new agent session with previous work.
3. Persist current session learning into durable memory.
4. Connect session summaries to `ROADMAP.md`, `milestone-*.md`, and `session-notes/`.

## Script Overview

| Script | Purpose |
|--------|---------|
| `scripts/setup-agent-prompts.sh` | Integrated setup for folders, memory, sessions, playbooks, Cursor prompts, Copilot prompts, and Claude Code commands |
| `scripts/upgrade-project.sh` | Framework-only upgrade for older initialized projects without overwriting implementation files or existing memory |
| `scripts/sdlc-spdd/sdlc.sh` | Workflow CLI: `next`, `claim`, `resume`, `advance`, `skip`, `shelf`, `sync`, `capture`, `team`, `list-work` |
| `scripts/sdlc-spdd/start-agent-session.sh` | Target-local script that creates a session brief for a new agent |
| `scripts/sdlc-spdd/resync-agent-session.sh` | Target-local script that checks or reconciles feature/canonical canvases, validates the canvas, and creates a session brief |
| `scripts/sdlc-spdd/capture-session-memory.sh` | Target-local script that persists current session summary, validation, decisions, pitfalls, patterns, and next steps |
| `scripts/sdlc-spdd/index-spdd-analysis.sh` | Index Fowler analysis artifacts into `domain-index.md` and `context-index.md` |
| `scripts/sdlc-spdd/resolve-agent-context.sh` | Resolve SDLC Agents `#SkillName` / phase extensions for progressive loading |
| `scripts/sdlc-spdd/create-work-from-milestone.sh` | Target-local script that maps milestone checklist items into SDLC-SPDD work artifacts |
| `scripts/sdlc-spdd/sync-roadmap-from-spdd.sh` | Target-local script that refreshes a managed roadmap summary from canvas metadata |
| `scripts/sdlc-spdd/summarize-session-notes.sh` | Target-local script that imports existing session notes into durable memory |
| `scripts/sdlc-spdd/sync-agent-context.sh` | Target-local low-level canvas copy synchronization |
| `scripts/sdlc-spdd/validate-command-adapters.sh` | Target-local checker that validates Cursor/Copilot/Claude Code command-pack parity in the installed project |
| `scripts/sdlc-spdd/verify-agent-command-effects.sh` | Target-local verifier for deterministic artifact side-effects after `/sdlc-spdd-*` command invocations and post-capture planning sync |
| `scripts/sdlc-spdd/validate-reasons-canvas.sh` | Target-local REASONS Canvas structure validation |
| `scripts/sdlc-spdd/verify-project-install.sh` | Target-local three-part install verification (Planning, SPDD, SDLC) |

## 1. Set Up Prompts and Memory

Run this from the SDLC-SPDD orchestrator repository:

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all

Equivalent explicit setup:

    ./scripts/init-project.sh --target /path/to/app --cursor --copilot --claude

For backward compatibility, omitting assistant flags installs Cursor and
GitHub Copilot only. Use `--all` or `--claude` to include Claude Code.

The target app receives:

- `requirements/` and `requirements/milestones/`
- `spdd/canvas/`
- `spdd/tasks/`
- `spdd/reviews/`
- `spdd/sync/`
- `ROADMAP.md`
- `.github/workflows/validate-sdlc-spdd-adapters.yml` when both Cursor and Copilot adapters are installed
- `milestone-1.md` when no `milestone-*.md` exists
- `session-notes/`
- `agent-context/memory/`
- `agent-context/playbooks/`
- `agent-context/features/`
- `agent-context/sessions/`
- `agent-context/harness/`
- `docs/sdlc-spdd/`
- `.cursor/commands/`
- `.github/copilot-instructions.md`
- `.github/prompts/`
- `CLAUDE.md` when missing
- `.claude/commands/`
- `agent-context/sdlc-pointer.sh` (local Work ID pointer)
- `agent-context/sdlc-workflow.sh` (phase/gate tracking)
- `agent-context/sdlc-team-registry.sh` (team claims)
- `agent-context/work-registry.tsv` (committed team registry)
- `scripts/sdlc-spdd/sdlc.sh` (workflow CLI wrapper)
- `scripts/sdlc-spdd/` runtime session scripts

## Upgrade an Older Installation

Run this from the SDLC-SPDD orchestrator repository:

    ./scripts/upgrade-project.sh --target /path/to/app --all

Preview first:

    ./scripts/upgrade-project.sh --target /path/to/app --all --dry-run

The upgrade updates framework-owned prompts, playbooks, harness files, target-local docs under `docs/sdlc-spdd/`, and target-local runtime scripts. It preserves application source, application docs outside `docs/sdlc-spdd/`, requirements, canvases, feature workspaces, reviews, sync logs, existing memory content, existing root `CLAUDE.md`, and target workflow customizations.

## 2. Start a New Agent Session

Create a session brief before asking a new agent to continue work. This is the
**session bootstrap**: it combines automatic Tier 1 grounding (already loaded on
every request) with work-specific context and Framework Orientation pointers.

See [Bootstrap and index-based loading](context-loading-and-scaling.md#bootstrap-and-index-based-loading).

    cd /path/to/app
    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code

With an explicit milestone:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code --milestone milestone-1.md

This writes:

    agent-context/sessions/<timestamp>-code-FEAT-001-order-status-api.md
    agent-context/sessions/current-session.md

The brief includes:

- **Framework Orientation** — how to operate within SDLC-SPDD (grounding, docs, indexes)
- Work ID
- phase
- active milestone (explicit `--milestone` or auto-detected from milestone files)
- recommended command
- canvas sync state
- roadmap and milestone status
- artifact status
- memory files to read
- playbooks to consider
- git status
- copy/paste resume prompt with SDLC, SPDD, and planning-layer `@` references

Then paste the **Resume Prompt** from `current-session.md`. See [Session prompt standard](session-prompt-standard.md), [SPDD prompt standard](spdd-prompt-standard.md), and [Planning prompt standard](planning-prompt-standard.md).

## 3. Resync Previous Work

### Script paths

| Context | Path |
|---------|------|
| This orchestrator repository (development) | `./scripts/<script>.sh` |
| Installed target application | `./scripts/sdlc-spdd/<script>.sh` |

User-facing docs use the target path. When developing here, drop the `sdlc-spdd/` segment.

### Check only (no session brief)

Check whether the feature workspace canvas and canonical canvas match:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id FEAT-001-order-status-api --check-only

`--check-only` runs sync check and canvas validation, then stops. It does **not** create a session brief. Run `start-agent-session.sh` next.

### Reconcile drift (creates session brief)

If drift exists, reconcile and create a session brief in one step. **Default:** canonical `spdd/canvas/<WORK-ID>.md` is authoritative:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id FEAT-001-order-status-api --from-canvas --force --phase code

Use `--from-feature` only when the feature workspace canvas was intentionally edited:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id FEAT-001-order-status-api --from-feature --force --phase code

When reconciling with `--from-canvas` or `--from-feature`, you do **not** need a separate `start-agent-session.sh` call — resync creates the brief.

The reconcile path:

1. Runs `sync-agent-context.sh`.
2. Validates the canonical canvas.
3. Creates a fresh session brief for the requested `--phase`.

## 4. Capture Current Session Memory

At the end of a session, persist what happened. The script **parses session
content** (summary, `session-notes/`, brief, canvas, progress log, and capture
flags) for path and package tokens, matches known categories in `code-areas.md`,
and registers new categories automatically. Use `--areas` only to override or
supplement parsed areas.

    ./scripts/sdlc-spdd/capture-session-memory.sh \
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

This updates:

- `agent-context/memory/session-history.md` (recent window; older entries archive)
- `agent-context/memory/sessions/<entry>.md` (immutable per-session detail)
- `agent-context/memory/session-index.md` (newest-first, with Areas column)
- `agent-context/memory/context-index.md` (area → session/decision/pitfall/pattern rows)
- `agent-context/memory/code-areas.md` (appends genuinely new categories)
- `agent-context/features/<WORK-ID>/progress-log.md`
- `session-notes/YYYY-MM-DD.md`
- `milestone-*.md` when `--milestone` is provided or auto-detected from `milestone-*.md`
- `ROADMAP.md` when `--roadmap-note` is provided
- `agent-context/memory/project-memory.md`
- `agent-context/memory/architecture-decisions.md` when `--decisions` is provided
- `agent-context/memory/known-pitfalls.md` when `--pitfalls` is provided
- `agent-context/memory/reusable-patterns.md` when `--patterns` is provided
- `agent-context/sessions/current-session.md` when present

Decisions, pitfalls, and patterns are indexed in `context-index.md` **only when
areas are resolved** for the session. See [Context loading and scaling](context-loading-and-scaling.md).

## Recommended Daily Loop

Orient and claim:

    ./scripts/sdlc-spdd/sdlc.sh next
    ./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>    # commit work-registry.tsv on shared repos

Start or resume:

    ./scripts/sdlc-spdd/sdlc.sh resume <WORK-ID> [--phase <phase>]
    ./scripts/sdlc-spdd/sdlc.sh start

Optional canvas sync check:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

Invoke the SDLC-SPDD skill:

    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01

After completing a phase step:

    ./scripts/sdlc-spdd/sdlc.sh advance

Review and sync:

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Capture memory (guarded):

    ./scripts/sdlc-spdd/sdlc.sh capture --summary "<summary>" --validation "<tests>" --next "<next command>"

Map milestone planning into SPDD work:

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

Refresh roadmap from SPDD canvases:

    ./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .

Import existing session notes into memory:

    ./scripts/sdlc-spdd/summarize-session-notes.sh --target . --all

## 5. Index Analysis Context (Fowler Step 3)

After `/sdlc-spdd-analysis` writes `spdd/analysis/<WORK-ID>-analysis.md`, index
domain keywords and code areas:

    ./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id <WORK-ID>

Updates `domain-index.md`, `context-index.md` (Kind: `analysis`), and
`code-areas.md`. See [Chelsea Troy and the framework](chelsea-troy-and-the-framework.md).

## 6. Resolve Skills and Phase Extensions (SDLC Agents)

Resolve which extension, playbook, and memory files to load — do not list whole directories:

    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase code --work-id <WORK-ID>
    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase code --areas src/billing,com.acme.billing
    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --text "Implement retry #TDD #java !Kafka"
    ./scripts/sdlc-spdd/resolve-agent-context.sh --list-skills

Static phase files come from `agent-context/memory/phase-index.md`. With `--work-id` or
`--areas`, `context-index.md` rows are filtered by code area (newest first); anchor-only
index entries stay in the Resolved Context table without loading whole memory logs.

`start-agent-session.sh` embeds resolve output under **Resolved Context** in
`current-session.md` and passes `--work-id` when set. See [SDLC Agents and the framework](sdlc-agents-and-the-framework.md).

## Hybrid Contract

The scripts enforce the combined system:

- SDLC Agents side: phase-specific handoffs, progressive context loading, playbook selection, and persistent learning.
- SPDD side: REASONS Canvas validation, prompt-first behavior changes, canvas sync, and reviewable artifacts.

Use `capture-session-memory.sh` after meaningful work so future agents do not rely on chat history.

You can verify both command effects and planning sync:

    ./scripts/sdlc-spdd/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step review
    ./scripts/sdlc-spdd/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step capture --milestone milestone-1.md --require-roadmap
