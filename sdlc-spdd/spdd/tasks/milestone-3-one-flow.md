# Milestone 3 task list — One flow on storage v3

Iteration list for consolidating `sdlc-spdd-orchestrator` onto one engine (Python `sdlc-engine`) and one persistence model (storage v3), with code, tests, and docs aligned.

Full review: [`../analysis/SPIKE-005-architecture-review-analysis.md`](../analysis/SPIKE-005-architecture-review-analysis.md)  
Milestone: [`../../requirements/milestones/milestone-3/MILESTONE-3.md`](../../requirements/milestones/milestone-3/MILESTONE-3.md)  
Monthly goals (Obsidian): [`2026-10-monthly-goals.md`](2026-10-monthly-goals.md)

## How to use this list

One Work ID at a time. For each row: analysis → plan/canvas → architect → code one operation → review. Beck stage for the whole list: **make it right**.

## P0 — one flow

| # | Work ID | Task | Done when |
|---|---------|------|-----------|
| 0 | `SPIKE-005-architecture-review` | Review + program (this list) | Analysis, milestones 3/4/5, stubs, canvas |
| 1 | `BUG-001-db-query-undefined-names` | Fix `NameError` in `db export`; test it | `ruff --select F821` clean; export test |
| 2 | `CHORE-004-lint-and-complexity-gates-real` | Full pyflakes, complexity on PR diff, shellcheck in CI | A CCN-11 function fails CI; shellcheck `-S error` green |
| 3 | `CHORE-006-dogfood-adapters-and-quick-spec` | Dogfood packs from spec; `quick` spec | Rewritten templates diff clean vs dogfood |
| 4 | `REF-002-purge-pre-v3-compat` | Delete legacy layouts, migrations, archive folders | Acceptance greps in stub |
| 5 | `REF-003-retire-bash-workflow-dual-path` | Delete bash workflow twin and engine switches | No `sdlc-workflow.sh`; `SDLC_ENGINE` gone |

## P1 — maintainable

| # | Work ID | Task | Done when |
|---|---------|------|-----------|
| 6 | `REF-004-split-installer-blueprints` | Blueprints per console tab | No installer fn > 80 NLOC / CCN 10 |
| 7 | `REF-005-cli-command-modules` | Command modules + result objects | `import sdlc_engine.cli` loads no heavy deps |
| 8 | `REF-006-storage-records-and-atomic-appends` | Typed records; locked appends | 20 parallel captures → 20 lines |
| 9 | `REF-007-single-guide-transport` | `GuideClient` only | No raw `urllib` outside client/issues |
| 10 | `REF-008-console-viewer-hardening` | Threat model, `--lan` token, root allow-list, CSRF | Rejection tests pass |
| 11 | `CHORE-005-ci-reusable-workflows` | 26 → ≤ 10 workflows | Mapping table in TESTING.md |
| 12 | `TEST-004-hermetic-unit-suite-and-fixtures` | Flask-free unit; shared fixture; no grab-bags | Import test; counts match tree |

## P2 — finish

| # | Work ID | Task | Done when |
|---|---------|------|-----------|
| 13 | `REF-009-adf-codec-and-viewer-assets` | One ADF codec; drop `pages.py` | Viewer Playwright green |
| 14 | `REF-010-pythonize-session-and-capture` | Session/capture/resolve/create-work in Python | One `accept` verb |
| 15 | `REF-011-split-issue-sync-adapters` | Jira + GitHub adapters | No issues fn > CCN 10 |

## Review findings → Work IDs

| Finding (SPIKE-005) | Work ID |
|---------------------|---------|
| M1 two behavioral cores | REF-003 |
| M2 pre-v3 compat load-bearing; archive fork | REF-002 |
| M3 latent NameErrors; narrow lint gate | BUG-001, CHORE-004 |
| M4 complexity gate proves the checker | CHORE-004 |
| M5 god modules / CLI monolith | REF-004, REF-005 |
| M6 ad-hoc records; unlocked appends | REF-006 |
| M7 Guide transport ×3 | REF-007 |
| M8 web surfaces assume localhost | REF-008, REF-009 |
| M9 porous test layers; 26 workflows | TEST-004, CHORE-005 |
| M10 dogfood adapters lag templates | CHORE-006 |
| M14 shell-only session stack; issues mega-service | REF-010, REF-011 |

Docs findings M11–M13 are Milestone 4: [`../../requirements/milestones/milestone-4/MILESTONE-4.md`](../../requirements/milestones/milestone-4/MILESTONE-4.md).

## First next action

    /sdlc-spdd-plan @sdlc-spdd/requirements/milestones/milestone-3/SPIKE-005-architecture-review.md

Then BUG-001 (smallest, proves the gate widening is needed).
