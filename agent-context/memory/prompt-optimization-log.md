# Prompt Optimization Log

Record whether a prompt or context change improved an outcome. One global ledger
for the project — retrieve by Work ID or via `context-index.md` rows with
Kind: `metric` (added when capture metric flags are used).

This file is measurement only. It does not score prompts or auto-optimize them.

## Row schema

Append one markdown section per entry (newest last, or follow project capture
conventions). Required fields:

| Field | Meaning |
|-------|---------|
| **Date** | ISO date or timestamp of the change |
| **Work ID** | Owning Work ID (for example `FEAT-004-prompt-optimization-ledger`) |
| **Change** | What changed (command template, grounding, playbook, analysis prompt, …) |
| **Hypothesis** | Why you expected the change to help |
| **Signal** | What you observed (review loops, rework count, clarity, …) |
| **Outcome** | Did it help? (`improved` / `neutral` / `worse` / `unknown`) plus a short note |

Optional capture-time metrics (when wired by `capture-session-memory.sh`):

- `--readiness` — canvas readiness value at capture
- `--review-result` — `pass` \| `fail` \| `mixed` \| `blocked`
- `--rework` — non-negative count of corrective prompt-update/sync cycles after
  first Ready For Coding
- `--context-files` — approximate context file count loaded for the session

Older entries may be rotated into `agent-context/memory/archive/` (same pattern as
`session-history.md`) once rotation is enabled.

## Entries

### Example (replace or keep as a template)

- Date: 2026-07-15
- Work ID: FEAT-004-prompt-optimization-ledger
- Change: Added this ledger file with documented schema (Operation T01)
- Hypothesis: A durable, reviewable place to record prompt outcomes will make later
  optimization evidence-driven
- Signal: n/a (bootstrap entry)
- Outcome: unknown — schema established; metrics flags land in later operations

### 2026-07-15 — FEAT-004 close-out

- Date: 2026-07-15
- Work ID: FEAT-004-prompt-optimization-ledger
- Change: Shipped ledger + capture metrics + required prompt-update/retro ledger entries + rotation + docs (T01–T05); fixed next-op inference at ## Final Status boundary
- Hypothesis: Measuring prompt outcomes via existing capture/index would be enough without a new datastore
- Signal: Tests 22–23 green; posture boundary OK; review Approved With Notes; stuck-on-T05 bug found and fixed during close
- Outcome: improved — measurement substrate is usable; first ledger entry from retro

### 2026-07-15 — FEAT-005 close-out

- Date: 2026-07-15
- Work ID: FEAT-005-canvas-readiness-indicators
- Change: Optional readiness vocabulary in validate-reasons-canvas; --validate-cycles/--review-cycles capture metrics; docs
- Hypothesis: Parsing existing Metadata Readiness + optional YAML would be enough without migrating all canvases
- Signal: tests/test-canvas-readiness.sh 6/6; posture OK
- Outcome: improved — leading indicators + machine-parseable readiness without breaking older canvases

### 2026-08-07 — SPIKE-003 absorption research close-out

- Date: 2026-08-07
- Work ID: SPIKE-003-embabel-context-graph-absorption
- Change: Dual-repo Guide+orchestrator session for fork-vs-upstream inventory; pin vs tip diffs; absorption matrix in research + Guide docs
- Hypothesis: Separating SPDD-coupled package from Embabel-general git-incremental ingest would yield a clear hybrid recommendation without opening an upstream PR
- Signal: Review Approved With Notes; Guide PR #4 merged; tip refresh (Layer D cloud env) did not change recommendation; human accept/reject still open
- Outcome: improved — decision artifacts and upstreamability matrix are reusable; dual-env reduced context-switch cost
