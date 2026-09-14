---
title: SDLC-SPDD — October 2026 goals (one flow on storage v3)
tags: [sdlc-spdd, milestone-3, milestone-4, goals, one-flow]
source: sdlc-spdd/spdd/analysis/SPIKE-005-architecture-review-analysis.md
created: 2026-09-13
---

# October 2026 goals — one engine, one persistence model, aligned docs/tests/code

Thesis for the month: **no competing versions**. Python `sdlc-engine` is the only engine; storage v3 (`spdd/memory/lessons.jsonl` + `registry.jsonl`, `.sdlc/` runtime, `sdlc-spdd/` home) is the only persistence model; docs, tests, and code describe the same flow. Pre-v3 context may be lost.

Each task below is one Work ID (requirement stub under `sdlc-spdd/requirements/milestones/milestone-3|4/`). Sizes: S ≤ 1 PR, M = 2–4 PRs, L = a sequence of one-operation PRs. Checkboxes are the acceptance greps from the stubs, so a task is done when the grep says so, not when it feels done.

## Week 1 — gates and quick wins (P0, small) #week1

- [ ] **BUG-001** Fix `db_query.py` undefined names (`export_sql` raises `NameError` today) — S
  - [ ] `ruff check --select F821 engine/src` clean
  - [ ] unit test for `LocalIndex.export_sql` on a temp project
  - [ ] `context_linked_to_section` tested or deleted
- [ ] **CHORE-004** Lint / complexity / shellcheck gates run on the real diff — M
  - [ ] pyproject ruff `select = ["F", "E9"]`; CI uses the pyproject rule set
  - [ ] `check-complexity.py --base origin/main` runs on PR diffs in `test-sdlc-engine.yml`
  - [ ] shellcheck workflow (`-S error` first) over `scripts/`, `scripts/lib/`, `templates/agent-context/`, `tests/*.sh`; fix SC2066 / SC1087 / SC2218 / SC2144
  - [ ] `test_quality_gates.py` asserts the new rule set
- [x] **CHORE-006** Regenerate dogfood adapters; spec for `/sdlc-spdd-quick` — S
  - [x] `.cursor/commands`, `.claude/commands`, `.github/prompts` diff clean vs path-rewritten templates
  - [x] `spec/commands/lifecycle-quick.spec.md` exists; `generate-command-adapters.sh --check` covers it
  - [ ] `validate-sdlc-spdd-adapters` fails on stale dogfood packs
- [ ] **DOC-004** Docs describe the layout `init` creates — S
  - [ ] `grep -rn 'docs/sdlc-spdd' docs README.md CONTRIBUTING.md` empty
  - [ ] first-day checklist verified against a fresh `init` in `/tmp`
  - [ ] `work-registry.tsv` → `registry.jsonl`; one workflow step count
- [ ] **CHORE-009** One version string; README focus points at ROADMAP — S
  - [ ] `test_engine_shared` compares `__version__` to pyproject without a literal
  - [ ] CHANGELOG top entry dated; tag ↔ version ↔ CHANGELOG checklist in CONTRIBUTING
  - [ ] ROADMAP drops links to archived canvases
- [ ] **CHORE-010** Registry reconciliation — S
  - [ ] terminal registry event for every Milestone 2 Work ID (via `sdlc.sh`, never hand-edit)
  - [ ] `list-work` shows registry vs canvas state and flags MISMATCH
  - [ ] Milestone 2 `_milestone.yml` status `complete`

## Weeks 2–3 — the purge and the single engine (P0, large) #week2 #week3

- [ ] **REF-002** Purge pre-v3 persistence compatibility — L
  - [ ] `archive` deletes canvas/analysis/review/sync/session/state; no `spdd/*/archive/`; unit + bash tests assert the same contract
  - [ ] `project.py` has no root-layout or `agent-context/harness` fallback
  - [ ] `registry.py` reads `registry.jsonl` only (no TSV)
  - [ ] `storage_migrate.py`, `agent_context_upgrade.py`, `context_model.py` legacy parsers, `installer/rollback.py` legacy-layout code deleted with their tests
  - [ ] `upgrade-project.sh` / `verify-project-install.sh` / `framework-install.sh` refuse legacy sprawl with a message; no `legacy-layout-archive`
  - [ ] `grep -r 'agent-context\|work-registry' engine/src scripts templates` returns only the folder name `templates/agent-context/`
  - [ ] `TESTING.md`, `docs/storage-v3.md` have no legacy sections
- [ ] **REF-003** Retire the bash workflow twin — L
  - [ ] `SDLC_ENGINE` / `SDLC_GATE_ENGINE` removed; `sdlc.sh` errors with an install hint when Python engine is missing
  - [ ] `templates/agent-context/` has no `sdlc-workflow.sh`, `sdlc-team-registry.sh`, `sdlc-pointer.sh`
  - [ ] gate path uses `resolve_engine_python` (`SDLC_PY`), never bare `python3`
  - [ ] `cmd_shell` bridges `sdlc-spdd/scripts` in installed targets
  - [ ] bash harnesses pass against the Python-only dispatcher or are replaced by pytest
  - [ ] shipped script LOC down ≥ 3 000; `docs/engine-v2.md`, `TESTING.md`, README say one engine
- [ ] **CHORE-007** Zero broken doc links, enforced in CI — M
  - [ ] in-tree broken links fixed (hub → ROADMAP, `agent-context/README`, milestone files)
  - [ ] `verify-doc-links.sh` resolves shipped docs against the installed layout
  - [ ] `verify-doc-links.sh` reports 0 broken and runs in a docs workflow
- [ ] **DOC-005** Generate assistant grounding from one path map — M
  - [ ] `spec/grounding.spec.md` + path map → `.mdc`, `CLAUDE.md`, `copilot-instructions.md`
  - [ ] no `scripts/sdlc-spdd/` or `agent-context/harness` in `templates/`
  - [ ] generation is idempotent and `--check`ed in CI

## Week 4 — make the one flow maintainable (P1) #week4

- [ ] **REF-004** Split `installer/app.py` `create_app` (1 056 lines) into blueprints — M
  - [ ] no function in `installer/` over 80 NLOC or CCN 10
  - [ ] integration + Vue3 Playwright pass unchanged; installer coverage ≥ 90 %
- [ ] **REF-005** One module per CLI command; result objects, not prints — M
  - [ ] `import sdlc_engine.cli` loads no Flask / sqlite3 / urllib (test)
  - [ ] no `cmd_*` over CCN 10; no `SystemExit` in library modules
  - [ ] `cli.py` re-exports and `issue_tracker.py` shim deleted
- [ ] **REF-006** Typed storage records; atomic, locked JSONL appends — M
  - [ ] `RegistryEvent`, `PersistResult` dataclasses; one `LEDGER_KINDS`
  - [ ] `io_util.append_jsonl_atomic` with lock used by ledger stage and registry
  - [ ] concurrency test: 20 parallel captures → 20 valid lines
- [ ] **TEST-004** Hermetic unit suite; shared installed-target fixture — M
  - [ ] unit suite imports no Flask (test); Flask tests moved to `tests_integration`
  - [ ] `*gaps*` / `*slices*` test files dissolved into per-module tests
  - [ ] `installed_target` fixture shared by unit / integration / research
  - [ ] `TESTING.md` counts match `grep -c 'def test_'`
- [ ] **CHORE-005** 26 workflows → ≤ 10 with a reusable setup — M
  - [ ] `workflow_call` setup (checkout, py3.12, engine install, optional node/playwright)
  - [ ] e2e push/PR path filters aligned; duplicate installer-cov job dropped; adapter validators merged
  - [ ] mapping table old job → new job in `TESTING.md`

## Carry into November (P1/P2) #next-month

- [ ] **REF-007** `GuideClient` is the only Guide HTTP path; no hardcoded Neo4j password — S
- [ ] **REF-008** Threat model + hardening for console/viewer (`--lan` token, viewer root allow-list, CSRF) — M
- [ ] **CHORE-008** `docs/` is the only authoring root; `sdlc-spdd/docs` generated; CI drift check — M
- [ ] **DOC-006** `design-decisions.md` rewritten as storage v3 ADRs; `STARTER-SPEC.md` archived — M
- [ ] **REF-009** One ADF codec; `viewer/pages.py` deleted (assets or Vue tab) — M
- [ ] **REF-010** Session brief / capture / resolve / create-work in Python; one `accept` verb — L
- [ ] **REF-011** Split `IssueSyncService` into Jira and GitHub adapters — M
- [ ] **DOC-007** Glossary + "add a CLI command" contributor guide — S
- [ ] Open **Milestone 5** (make it fast) once Milestone 3 P0/P1 are checked

## Baseline to beat (2026-09-13)

| Measure | Now | Target end of October |
|---------|-----|-----------------------|
| Engines | 2 (bash twin + Python) | 1 |
| Persistence models supported | v3 + legacy layouts | v3 only |
| Functions CCN > 15 in `engine/src` | 67 | 0 |
| Longest function | 1 056 lines (`installer/app.create_app`) | ≤ 80 NLOC everywhere |
| Unit coverage of `sdlc_engine` | 66 % | ≥ 80 % (viewer/installer no longer 0–26 %) |
| Ruff rules in CI | `F401,F811` | full `F` + `E9`, complexity on diff, shellcheck |
| Undefined names shipped | 9 | 0 |
| Broken doc links | 95 / 959 | 0, gated |
| GitHub workflows | 26 | ≤ 10 |
| Shellcheck errors | 7 | 0, gated |
| Shipped bash LOC (`templates/agent-context` + `scripts`) | ~13.7 k | ≤ 10 k |

## Rules for the month

- One Work ID, one PR series; no PR adds a second implementation of anything Python already does.
- A legacy path stays only if a named user needs it; otherwise delete.
- Docs change in the same PR as the behavior they describe.
- Capture lessons with `./scripts/sdlc.sh capture`; accept at retro.
