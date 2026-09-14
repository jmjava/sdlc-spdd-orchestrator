# Milestone 3 — One flow on storage v3

## Goal

There is exactly one engine (Python `sdlc-engine`), one persistence model (storage v3: committed `spdd/memory/lessons.jsonl` + `registry.jsonl`, gitignored `.sdlc/` runtime, single `sdlc-spdd/` home), and code, tests, and docs that all describe that one flow. Competing implementations (bash workflow twin, `SDLC_ENGINE=shell`), pre-v3 compatibility (legacy `agent-context/` layouts, `work-registry.tsv`, feature mirrors, `spdd/*/archive/` folders, migration shims) are removed, not maintained. Losing pre-v3 context is an accepted cost (owner decision, 2026-09-13).

**Stage:** make it right. No new capability; the framework does the same job with one implementation, real quality gates, and honest test layers.

Analysis that opened this milestone: `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Outcome (definition of done)

- `SDLC_ENGINE` and `SDLC_GATE_ENGINE` no longer exist; `sdlc.sh` is a thin dispatcher into the Python engine and errors clearly when it is missing.
- `templates/agent-context/` ships no workflow/registry/pointer bash; shipped script LOC drops by ≥ 3 000.
- No code path reads or writes pre-v3 layouts; `archive` deletes (git history is the record); no `spdd/*/archive/` directories.
- Lint (full pyflakes), complexity (on the PR diff), and shellcheck gates run in CI and fail on regressions.
- No function in `engine/src` exceeds CCN 15; `installer/app.py` and `cli_*` are split into units under 80 NLOC.
- Unit suite is hermetic (no Flask, no subprocess to bash); every module has a focused test file; `TESTING.md` numbers are generated from the tree.
- ≤ 10 GitHub workflows with one reusable setup.
- Local web surfaces have a written threat model; `--lan` requires a token.

## Scope

P0 — one flow (do first, in order):

- [x] SPIKE-005-architecture-review — review + this program (canvas pending)
- [x] BUG-001-db-query-undefined-names — live `NameError` in `db export` (#308)
- [x] CHORE-004-lint-and-complexity-gates-real — gates run on the real diff (#308)
- [x] CHORE-006-dogfood-adapters-and-quick-spec — dogfood packs and `quick` regenerate from canonical specs (#308, #320)
- [x] REF-002-purge-pre-v3-compat — one data model; archive deletes; no migrations (#314)
- [x] REF-003-retire-bash-workflow-dual-path — one engine; no shell twin

P1 — make the one flow maintainable:

- [ ] REF-004-split-installer-blueprints
- [ ] REF-005-cli-command-modules
- [ ] REF-006-storage-records-and-atomic-appends
- [ ] REF-007-single-guide-transport
- [ ] REF-008-console-viewer-hardening
- [ ] CHORE-005-ci-reusable-workflows
- [ ] TEST-004-hermetic-unit-suite-and-fixtures

P2 — finish the consolidation:

- [ ] REF-009-adf-codec-and-viewer-assets
- [ ] REF-010-pythonize-session-and-capture
- [ ] REF-011-split-issue-sync-adapters

## Linked Work

| Work ID | Pri | Size | Requirement | Status | Notes |
|---------|-----|------|-------------|--------|-------|
| SPIKE-005-architecture-review | P0 | M | [requirement](SPIKE-005-architecture-review.md) | In Progress | Program opened in #308; spike canvas close-out pending; claim released 2026-09-14 |
| BUG-001-db-query-undefined-names | P0 | S | [requirement](BUG-001-db-query-undefined-names.md) | Complete | Fix undefined names in db_query.py (export_sql NameError) |
| CHORE-004-lint-and-complexity-gates-real | P0 | M | [requirement](CHORE-004-lint-and-complexity-gates-real.md) | Complete | Lint, complexity, shellcheck gates on the real diff |
| CHORE-006-dogfood-adapters-and-quick-spec | P0 | S | [requirement](CHORE-006-dogfood-adapters-and-quick-spec.md) | Complete | Dogfood parity in #308; canonical quick spec in #320 |
| REF-002-purge-pre-v3-compat | P0 | L | [requirement](REF-002-purge-pre-v3-compat.md) | Complete | Storage v3 is the only supported layout (#314) |
| REF-003-retire-bash-workflow-dual-path | P0 | L | [requirement](REF-003-retire-bash-workflow-dual-path.md) | Complete | Bash workflow twin retired; Python is the only flow (#321) |
| REF-004-split-installer-blueprints | P1 | M | [requirement](REF-004-split-installer-blueprints.md) | To Do | Split `installer/app.py` `create_app` into blueprints |
| REF-005-cli-command-modules | P1 | M | [requirement](REF-005-cli-command-modules.md) | To Do | One module per CLI command; result objects, not prints |
| REF-006-storage-records-and-atomic-appends | P1 | M | [requirement](REF-006-storage-records-and-atomic-appends.md) | To Do | Typed storage records; atomic, locked JSONL appends |
| REF-007-single-guide-transport | P1 | S | [requirement](REF-007-single-guide-transport.md) | To Do | `GuideClient` is the only Guide HTTP path |
| REF-008-console-viewer-hardening | P1 | M | [requirement](REF-008-console-viewer-hardening.md) | To Do | Threat model and hardening for console and viewer |
| CHORE-005-ci-reusable-workflows | P1 | M | [requirement](CHORE-005-ci-reusable-workflows.md) | To Do | 26 workflows → ~9 with a reusable setup |
| TEST-004-hermetic-unit-suite-and-fixtures | P1 | M | [requirement](TEST-004-hermetic-unit-suite-and-fixtures.md) | To Do | Hermetic unit suite; shared installed-target fixture |
| REF-009-adf-codec-and-viewer-assets | P2 | M | [requirement](REF-009-adf-codec-and-viewer-assets.md) | To Do | One ADF codec; viewer UI as assets or Vue tab |
| REF-010-pythonize-session-and-capture | P2 | L | [requirement](REF-010-pythonize-session-and-capture.md) | To Do | Session, capture, resolve, create-work in Python |
| REF-011-split-issue-sync-adapters | P2 | M | [requirement](REF-011-split-issue-sync-adapters.md) | To Do | Split `IssueSyncService` into Jira and GitHub adapters |

## Iteration order

1. BUG-001, CHORE-004, CHORE-006 — small, independent, test-first; they make every later PR safer.
2. REF-002 then REF-003 — the purge first (fewer code paths to retire), then the engine twin. Each lands as a sequence of one-operation PRs; the acceptance greps are the stop rule.
3. REF-004, REF-005, REF-006 in parallel once REF-003 is in (they no longer need shell parity).
4. REF-007, REF-008, CHORE-005, TEST-004.
5. P2 items.

## Stop rules

- A PR that adds a second implementation of anything already in Python is rejected.
- A PR that keeps a legacy path "for safety" must name the user who needs it; otherwise the path is deleted.
- Docs change in the same PR as the behavior they describe (`TESTING.md`, `docs/storage-v3.md`, `docs/engine-v2.md`).

## SDLC-SPDD Flow

For each work item: `/sdlc-spdd-analysis` on its requirement → `/sdlc-spdd-plan` → `/sdlc-spdd-architect` until Ready For Coding → one operation at a time with `/sdlc-spdd-code` → review, capture, accept, retro.

## Session Updates

2026-09-13 — Milestone opened from SPIKE-005. Owner decision: one engine, one persistence model; pre-v3 context may be lost. First P0 fixes started in the SPIKE-005 branch.

2026-09-14 — Bookkeeping sync with `main` (#308): BUG-001 and CHORE-004 Complete; CHORE-006 In Progress (packs regenerated, `quick` spec outstanding); REF-002 T01 (archive deletes, no `spdd/*/archive/`) landed ahead of its canvas. SPIKE-005 claim released. REF-002 claimed; analysis → canvas → remaining purge operations start here.

2026-09-14 — REF-002 Complete in #314 (`06ddb23`): storage v3 is the only
supported layout, migration and compatibility paths are removed, product and
shipped docs match, and all 25 merge-commit checks pass. Next one-flow item:
REF-003.

2026-09-14 — CHORE-006 Complete in #320: all three dogfood command packs match
path-rewritten templates, and `/sdlc-spdd-quick` is generated from
`lifecycle-quick.spec.md`. P0 continues with REF-003.
