# REASONS Canvas: FEAT-001-shared-script-library - Shared script library (scripts/lib/)

## Metadata

- Work ID: FEAT-001-shared-script-library
- Work Type: Feature (refactor)
- Status: Draft
- Readiness: Needs Analysis
- Created: 2026-06-19
- Updated: 2026-06-19
- Owner:
- Target Project: sdlc-spdd-orchestrator (self / dogfood)
- Stack: Bash
- Source System: Roadmap
- Roadmap: ROADMAP.md
- Milestone: milestone-1.md
- Delivery stage: make it right (maintainability) — **do first**
- Related PR:

## R - Requirements

### User Goal

Stop maintaining the same bash logic in ~23 scripts. Have one place to read, fix,
and extend shared behavior.

### Business / Product Goal

Make the script layer readable and maintainable so later refactors (FEAT-002
command-spec generation, FEAT-003 extension manifest) build on a clean base.

### Acceptance Criteria

- [ ] `scripts/lib/` provides sourced helpers covering: target/path resolution, `usage`/logging, `slugify`, Work-ID parse, and `context-index.md` read/append.
- [ ] Consuming scripts `source` the library rather than redefining these functions.
- [ ] All scripts keep identical CLI, output, and exit codes (behavior-identical refactor).
- [ ] No duplicate definitions of extracted helpers remain.
- [ ] Helper behavior is covered by tests/validation; existing tests still pass.

### Non-Goals

- No new flags, output formats, or renamed scripts.
- No change to what any script does — only where shared code lives.

### Assumptions

- Scripts are POSIX-bash and already run from the repo; sourcing a relative lib is safe.
- The duplication is mechanical (same intent), so extraction is low-risk.

### Open Questions

- Resolve during analysis: exact set of helpers and their grouping into files (one `common.sh` vs. several focused libs).
- How installed/copied scripts in target projects resolve the lib path (relative vs. resolved).

## E - Entities

### Application Components

- New: `scripts/lib/*.sh` (sourced, not executable entry points)
- Consumers: the scripts in `scripts/*.sh` that currently duplicate logic

### Data / Persistence

- None new. Helpers wrap existing `agent-context/memory/context-index.md` I/O.

### Files Likely Affected

- `scripts/lib/` (new)
- High-duplication consumers first: `resolve-agent-context.sh`, `capture-session-memory.sh`, `index-spdd-analysis.sh`, `start-agent-session.sh`, `create-work-from-milestone.sh`, then the `install-*` and `sync-*` scripts.

## A - Approach

### Proposed Approach

1. Inventory the duplicated functions (analysis phase) and confirm they are behavior-identical.
2. Create `scripts/lib/` helpers with the agreed grouping and a stable sourcing convention.
3. Refactor consumers one cluster at a time to source the lib, deleting the local copies.
4. Keep each step behavior-identical; lean on existing validation scripts as the safety net.

### Alternatives Considered

- Leave as-is (rejected: drift is the problem we are fixing).
- A single mega-`utils.sh` (consider vs. focused libs during analysis).

### Trade-Offs

- Sourced libs add an indirection, but remove N copies of each function.

### Risks

- A subtle behavior difference between two "duplicate" copies surfaces during extraction → caught by per-cluster validation.
- Lib path resolution in installed target projects → resolve in analysis before refactoring installers.

### Failure Modes

- A consumer that fails to source the lib must fail loudly, not silently change behavior.

## S - Structure

### Files To Add

- `scripts/lib/common.sh` (and/or focused helper files — decided in analysis)

### Files To Modify

- The duplicating scripts under `scripts/`, refactored to source the lib.

### Test Structure

- Add coverage for the helpers; re-run existing validation scripts unchanged.

## O - Operations

### T01 - Inventory duplication

- Status: Not Started
- Description: Catalog the duplicated functions and confirm behavior-identical intent; decide lib grouping + sourcing convention.
- Files: spdd/analysis/FEAT-001-shared-script-library-analysis.md
- Tests: Not applicable
- Validation: Analysis review

### T02 - Create scripts/lib/ helpers

- Status: Not Started
- Description: Implement the agreed helpers with the sourcing convention; no consumer changes yet.
- Files: scripts/lib/*.sh
- Tests: Unit/smoke for each helper
- Validation: Helpers behave identically to the originals

### T03 - Refactor consumers to source the lib

- Status: Not Started
- Description: Migrate scripts cluster by cluster, deleting local copies; one reviewable step per cluster.
- Files: scripts/*.sh
- Tests: existing validation scripts per cluster
- Validation: Behavior-identical CLI/output/exit codes

### T04 - Verify + document the convention

- Status: Not Started
- Description: Confirm no duplicate definitions remain; document how scripts source the lib.
- Files: scripts/lib/, docs (as needed)
- Tests: repo-wide check for stray duplicate definitions
- Validation: Full validation suite green

## N - Norms

### General

- Behavior-identical refactor: do not change any script's interface or output.
- Update this canvas before behavior changes.
- No unrelated refactors.

### Testing

- Re-run existing validation scripts after each cluster.

## S - Safeguards

- Do not code until this canvas is Ready For Coding.
- Migrate in small, reviewable clusters — never all scripts at once.
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

Lead make-it-right item from ROADMAP. Needs an analysis pass before coding. Use sync
notes to track drift between the roadmap, canvas, and implementation.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
