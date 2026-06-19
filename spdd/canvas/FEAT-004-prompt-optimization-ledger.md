# REASONS Canvas: FEAT-004-prompt-optimization-ledger - Prompt-optimization ledger + capture metrics

## Metadata

- Work ID: FEAT-004-prompt-optimization-ledger
- Work Type: Feature
- Status: Draft
- Readiness: Ready For Coding
- Created: 2026-06-18
- Updated: 2026-06-18 (architect: resolved open questions for long-term stability)
- Owner:
- Target Project: sdlc-spdd-orchestrator (self / dogfood)
- Stack: Bash + Markdown
- Source System: Roadmap
- Source Issue:
- Source URL:
- Docs URL:
- Roadmap: ROADMAP.md
- Milestone: milestone-1.md
- Delivery stage: make it fast (prompt-optimization measurement) — **deferred until make-it-right refactors land**
- Related PR:

## R - Requirements

### User Goal

Be able to record whether a prompt change improved an outcome, and retrieve that
signal later by code area or Work ID — without adding a new manual ritual.

### Business / Product Goal

Build the measurement that drives prompt optimization, so that "make it fast" work is
evidence-driven rather than guesswork. This is the first step *of* "make it fast" and
is sequenced **last** — only after the make-it-right refactors (FEAT-001→003) land.

### Acceptance Criteria

- [ ] `agent-context/memory/prompt-optimization-log.md` exists (global, single file) with a documented row schema: `date | Work ID | change | hypothesis | signal | outcome`.
- [ ] `capture-session-memory.sh` accepts optional `--readiness`, `--review-result`, `--rework`, `--context-files`; omitting them preserves current behavior exactly.
- [ ] `--review-result` accepts only `pass | fail | mixed | blocked`; unknown values warn and are skipped, never aborting capture.
- [ ] `--rework` accepts a non-negative integer (corrective prompt-update/sync cycles after first `Ready For Coding`).
- [ ] Provided metrics are indexed as `context-index.md` rows with Kind: `metric`, scoped to resolved area(s).
- [ ] The ledger is bounded by the same rotation/archive mechanism as `session-history.md` (recent inline; older to `agent-context/memory/archive/`).
- [ ] `/sdlc-spdd-prompt-update` and `/sdlc-spdd-retro` require a ledger entry in their output, with parity across the three assistants.
- [ ] Existing tests pass; a smoke test covers the new flags, enum validation, and ledger write/rotation.
- [ ] Docs updated (`context-loading-and-scaling.md` metric Kind + ledger rotation; prompt standards).

### Non-Goals

- No `spdd --metrics` query surface (make-it-fast horizon).
- No automated optimization, scoring, or external analytics.

### Assumptions

- The existing capture → index machinery is the right substrate; we extend it, not replace it.
- Ledger entries are written by humans/agents during `prompt-update`/`retro`, not auto-generated.

### Resolved Decisions (architect — chosen for long-term stability)

- **Ledger scope: global + indexed.** One file at `agent-context/memory/prompt-optimization-log.md`, retrieved via `context-index.md` (Kind: `metric`) filtered by area — never per-Work-ID. Rationale: the metric exists to answer cross-Work-ID questions; per-Work-ID storage would force directory scans and break progressive disclosure.
- **Growth is bounded by rotation.** The ledger reuses the existing `session-history.md` rotation/archive pattern (recent window inline, older entries to `agent-context/memory/archive/`) so it stays stable as it grows.
- **`--review-result` is a fixed enum:** `pass | fail | mixed | blocked`. Aggregation is the point; free text cannot be aggregated. Narrative nuance lives in the ledger `signal`/`outcome` columns. Unknown values warn (do not abort capture).
- **`--rework` is defined precisely:** a non-negative integer counting corrective `prompt-update`/`sync` cycles on the canvas *after* it first reached `Ready For Coding`. A perfectly-specced prompt scores 0. Re-run code operations are excluded (too noisy to attribute to prompt quality).

## E - Entities

### Domain Entities

- Prompt-optimization entry (date, Work ID, change, hypothesis, signal, outcome)
- Capture metric (readiness, review-result, rework, context-files)

### Application Components

- `scripts/capture-session-memory.sh` (extended with metric flags + ledger write)
- `scripts/resolve-agent-context.sh` (reads `context-index.md`; must tolerate Kind: metric)
- Command templates: `sdlc-spdd-prompt-update`, `sdlc-spdd-retro` (×3 assistants)

### External Systems

- None.

### Data / Persistence

- `agent-context/memory/prompt-optimization-log.md` (new)
- `agent-context/memory/context-index.md` (new Kind: `metric` rows)

### Files Likely Affected

- `scripts/capture-session-memory.sh`
- `templates/cursor/sdlc-spdd-prompt-update.md`, `templates/cursor/sdlc-spdd-retro.md`
- `templates/copilot/prompts/sdlc-spdd-prompt-update.prompt.md`, `.../sdlc-spdd-retro.prompt.md`
- `templates/claude/commands/sdlc-spdd-prompt-update.md`, `.../sdlc-spdd-retro.md`
- `docs/context-loading-and-scaling.md`

## A - Approach

### Proposed Approach

1. Add the global ledger file with a header documenting the row schema.
2. Extend `capture-session-memory.sh` with optional metric flags; validate `--review-result` against the enum and `--rework` as a non-negative integer (warn-and-skip on bad input); when present, append a `metric` row to `context-index.md` scoped to the resolved area(s), reusing existing area-resolution logic.
3. Reuse the existing `rotate_session_history` pattern to bound the ledger (recent inline; older to `archive/`).
4. Update the three `prompt-update` and `retro` command templates to require a ledger entry, keeping wording in parity for `validate-command-adapters.sh`.
5. Document the `metric` Kind, enum, rework definition, and ledger rotation.

### Alternatives Considered

- A separate metrics file per Work ID (rejected for MVP: harder to query across areas).
- A structured (YAML/JSON) metrics store (rejected: breaks markdown-first principle; defer until a query surface is justified).

### Trade-Offs

- Markdown ledger is easy and reviewable but not directly queryable — acceptable until "make it fast".
- Required ledger entries add a small authoring cost; mitigated by wiring into existing commands rather than a new step.

### Risks

- Metric flags become noise if unused → enforce via command templates, not docs.
- Parity drift across the three assistant adapters → covered by `validate-command-adapters.sh`.

### Failure Modes

- Capture run without flags must never fail or change prior behavior.
- Malformed metric values should warn, not abort capture.

## S - Structure

### Files To Add

- `agent-context/memory/prompt-optimization-log.md`
- `agent-context/memory/archive/` entries (created on rotation; mirrors session-history archive)

### Files To Modify

- `scripts/capture-session-memory.sh`
- `templates/cursor/sdlc-spdd-prompt-update.md`, `templates/cursor/sdlc-spdd-retro.md`
- `templates/copilot/prompts/sdlc-spdd-prompt-update.prompt.md`, `templates/copilot/prompts/sdlc-spdd-retro.prompt.md`
- `templates/claude/commands/sdlc-spdd-prompt-update.md`, `templates/claude/commands/sdlc-spdd-retro.md`
- `docs/context-loading-and-scaling.md`

### Package / Module Structure

- No new modules; extends existing scripts and templates.

### Test Structure

- Extend `tests/` smoke coverage for capture with/without metric flags.

### Documentation Structure

- Update `context-loading-and-scaling.md` index catalog with Kind: `metric`.

## O - Operations

### T01 - Add the ledger file + schema

- Status: Not Started
- Description: Create `prompt-optimization-log.md` with a documented row schema and example.
- Files: agent-context/memory/prompt-optimization-log.md
- Tests: Not applicable (doc artifact)
- Validation: Manual review against schema

### T02 - Extend capture-session-memory.sh with metric flags

- Status: Not Started
- Description: Add optional `--readiness/--review-result/--rework/--context-files`; write `metric` rows to context-index scoped by resolved area; no-op when omitted.
- Files: scripts/capture-session-memory.sh
- Tests: capture smoke test with and without flags
- Validation: `--dry-run` shows correct rows; existing capture unchanged

### T03 - Require ledger entry in prompt-update + retro templates

- Status: Not Started
- Description: Update all three assistant adapters for both commands to require a ledger entry; keep parity anchors.
- Files: templates/cursor/*, templates/copilot/prompts/*, templates/claude/commands/*
- Tests: ./scripts/validate-command-adapters.sh
- Validation: adapter parity CI passes

### T04 - Bound ledger growth (rotation/archive)

- Status: Not Started
- Description: Apply the existing `session-history.md` rotation pattern to the ledger — keep a recent inline window, move older entries to `agent-context/memory/archive/`.
- Files: scripts/capture-session-memory.sh
- Tests: rotation smoke test (entries beyond the window move to archive)
- Validation: `--dry-run` shows correct rotation; recent window intact

### T05 - Document the metric Kind + workflow

- Status: Not Started
- Description: Add Kind: metric to the index catalog; document the enum, `--rework` definition, and ledger rotation.
- Files: docs/context-loading-and-scaling.md
- Tests: Not applicable
- Validation: Doc consistency checklist

## N - Norms

### General

- Follow existing project conventions.
- Keep implementation aligned with this canvas.
- Do not invent requirements that were not requested.
- Update the canvas before behavior changes.
- Markdown-first: no new structured datastore for MVP.

### Testing

- Add or update tests for behavior changes.
- Document tests that could not be run.
- Capture without flags must remain behavior-identical.

## S - Safeguards

- Do not code until the canvas is Ready For Coding.
- Do not implement behavior changes until this canvas is updated with `/sdlc-spdd-prompt-update`.
- Do not let implementation drift from this canvas without running `/sdlc-spdd-sync`.
- This Work ID is measurement only: do not add a `spdd --metrics` query surface, scoring, or auto-optimization here — those are separate, later make-it-fast Work IDs.
- **Ship neutral.** The shipped artifacts touched by T03/T05 (`templates/**`,
  `docs/context-loading-and-scaling.md` → `docs/sdlc-spdd/`) must describe the ledger
  as a neutral capability — *what it does*, never our internal make-it-work/right/fast
  posture or goals. Posture language stays in `ROADMAP.md` and `CONTRIBUTING.md` only.
- T03/T05 must pass `./scripts/check-posture-boundary.sh` before merge.

## Architecture Notes

- **Stability principle applied:** every decision reuses an existing, proven mechanism (memory file + `context-index` + `rotate_session_history`) rather than introducing a new store. This minimizes new surface area and keeps the change reversible.
- **Extensibility preserved:** new metric Kind is additive to the index catalog; readers that do not understand `metric` rows simply ignore them. No schema migration for existing indexes.
- **Quality gates:** `validate-command-adapters.sh` (adapter parity) and capture smoke tests are the gates. Behavior-identical capture when flags are omitted is a hard requirement.
- **Readiness rationale:** all open questions resolved with stable, low-risk choices; operations are small and independently testable; no unresolved external dependency. Marked **Ready For Coding**.
- **Sequencing:** T01 (ledger) and T02 (flags) are the minimum viable slice; T03 (templates) makes entries mandatory; T04 (rotation) and T05 (docs) harden and explain. Implement one operation per session per project norms.

## Review Checklist

- [ ] Requirements satisfied
- [ ] Entities updated correctly
- [ ] Approach followed or synced
- [ ] Structure followed or synced
- [ ] Operations completed
- [ ] Norms followed
- [ ] Safeguards respected
- [ ] Tests added or updated
- [ ] No unrelated refactors
- [ ] Documentation updated if needed

## Sync Notes

Created during framework self-improvement (dogfood). Classified as "make it fast"
(prompt-optimization measurement) and deferred until the make-it-right refactors
(FEAT-001→003) land — see ROADMAP Delivery posture and milestone-1.md. The canvas is
specced and Ready For Coding so it can start immediately once its turn comes. Use
sync notes to track drift between the roadmap, canvas, and implementation.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
