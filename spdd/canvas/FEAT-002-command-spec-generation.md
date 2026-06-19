# REASONS Canvas: FEAT-002-command-spec-generation - Single command spec → generated adapters

## Metadata

- Work ID: FEAT-002-command-spec-generation
- Work Type: Feature (refactor)
- Status: Draft
- Readiness: Needs Analysis
- Created: 2026-06-19
- Updated: 2026-06-19
- Owner:
- Target Project: sdlc-spdd-orchestrator (self / dogfood)
- Stack: Bash + Markdown
- Source System: Roadmap
- Roadmap: ROADMAP.md
- Milestone: milestone-1.md
- Delivery stage: make it right (maintainability — kills drift)
- Related PR:

## R - Requirements

### User Goal

Edit each SDLC-SPDD command in one place and have all three assistant adapters stay
identical automatically.

### Business / Product Goal

Make adapter parity structural instead of hand-maintained, removing a whole class of
drift bugs and review burden.

### Acceptance Criteria

- [ ] One canonical spec per command (shared body + per-assistant framing/front matter).
- [ ] A generator emits the Cursor, Copilot, and Claude adapter files from the spec.
- [ ] Generated adapters preserve today's behavior and pass `validate-command-adapters.sh`.
- [ ] Command edits happen in the spec only; regeneration updates all three.
- [ ] CI fails if checked-in adapters are stale relative to the spec.
- [ ] Shipped generated adapters pass `check-posture-boundary.sh` (no posture language).

### Non-Goals

- No new commands; no behavior changes.
- No change to install/consumption of adapters.

### Assumptions

- The three adapters differ mostly in framing/front matter, not core instructions (confirm in analysis).
- `validate-command-adapters.sh` already encodes the parity contract we must preserve.

### Open Questions

- Spec format: single markdown-with-front-matter source vs. a small structured file — decide in analysis.
- Where the spec lives (`spec/commands/` vs. `templates/_spec/`) so it does not itself ship as an adapter.

## E - Entities

### Application Components

- New: canonical command spec source + generator script
- Existing: `validate-command-adapters.sh` (becomes a verifier of generated output)

### Files Likely Affected

- New spec directory + `scripts/generate-command-adapters.sh`
- Generated: `templates/cursor/*`, `templates/copilot/prompts/*`, `templates/claude/commands/*`
- CI workflow that checks adapter freshness

## A - Approach

### Proposed Approach

1. Analyze the current three adapter sets; extract the shared content and the per-assistant deltas.
2. Define the canonical spec format and migrate one command end to end as a proof.
3. Build the generator; generate all commands and diff against current adapters until equivalent.
4. Wire generation + a staleness check into CI alongside the parity validator.
5. Document the authoring workflow (edit spec → regenerate).

### Alternatives Considered

- Keep hand-maintained adapters + stronger validation (rejected: does not remove the drift source).
- Full templating engine (overkill; prefer minimal bash + markdown).

### Trade-Offs

- A generation step is added, but three-way manual sync is removed.

### Risks

- Hidden intentional differences between adapters → surface them during the extraction proof.
- Generator output churn (whitespace) → normalize so diffs are meaningful.

### Failure Modes

- A stale checked-in adapter must fail CI, never ship silently.

## S - Structure

### Files To Add

- Canonical command spec source (location TBD in analysis)
- `scripts/generate-command-adapters.sh`

### Files To Modify

- The generated adapter files (become outputs)
- CI workflow to check freshness

### Test Structure

- Generation + `validate-command-adapters.sh` + staleness diff in CI.

## O - Operations

### T01 - Extract shared vs. per-assistant content

- Status: Not Started
- Description: Analyze the three adapter sets; document shared body and per-assistant deltas.
- Files: spdd/analysis/FEAT-002-command-spec-generation-analysis.md
- Tests: Not applicable
- Validation: Analysis review

### T02 - Define spec format + migrate one command

- Status: Not Started
- Description: Lock the spec format; convert one command end to end as a proof of equivalence.
- Files: spec source, scripts/generate-command-adapters.sh (initial)
- Tests: diff generated vs. existing for that command
- Validation: byte/intent-equivalent output

### T03 - Generate all commands

- Status: Not Started
- Description: Generate every adapter from specs; reconcile until equivalent to current.
- Files: templates/cursor/*, templates/copilot/prompts/*, templates/claude/commands/*
- Tests: ./scripts/validate-command-adapters.sh
- Validation: parity CI passes

### T04 - Wire generation + staleness check into CI

- Status: Not Started
- Description: Fail CI when checked-in adapters differ from regeneration; enforce posture boundary on output.
- Files: .github/workflows/*
- Tests: CI dry-run
- Validation: stale adapter fails; clean tree passes; check-posture-boundary.sh green

### T05 - Document the authoring workflow

- Status: Not Started
- Description: Document "edit spec → regenerate"; update contributor docs.
- Files: docs/, CONTRIBUTING.md
- Tests: Not applicable
- Validation: doc consistency

## N - Norms

### General

- Behavior-identical: generated adapters must match today's intent.
- Update this canvas before behavior changes.
- No new commands under this Work ID.

### Testing

- Parity validator + staleness check are the gates.

## S - Safeguards

- Do not code until this canvas is Ready For Coding.
- **Ship neutral.** Generated adapters under `templates/**` describe commands as neutral capabilities; never emit make-it-work/right/fast posture language. Posture stays in ROADMAP.md/CONTRIBUTING.md.
- Generated output must pass `./scripts/check-posture-boundary.sh` and `./scripts/validate-command-adapters.sh` before merge.
- Do not let implementation drift from this canvas without running `/sdlc-spdd-sync`.

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

Depends on a clean script layer (FEAT-001 helps but is not a hard blocker). Needs an
analysis pass before coding. Use sync notes to track drift.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
