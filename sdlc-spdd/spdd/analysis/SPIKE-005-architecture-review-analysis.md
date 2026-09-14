# Analysis: SPIKE-005 — Full architectural review (source, tests, docs)

**Work ID:** SPIKE-005-architecture-review  
**Date:** 2026-09-13  
**Beck stage:** make it right (engineering consolidation) — opens Milestones 3, 4, 5  
**Inputs:** whole tree at `main` `8f7fef3`; four parallel read-only reviews (engine, shell/templates, tests/CI, docs) plus measured baselines below.

## Scope Lock-In

### In scope

- `engine/src/sdlc_engine` (64 modules, ~21.3k LOC), `scripts/` + `scripts/lib/` (~10.5k LOC bash), `templates/` (installed runtime, adapters, harness), `spec/commands`
- `engine/tests_*`, `tests/`, `.github/workflows` (26 workflows)
- `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `TESTING.md`, `STARTER-SPEC.md`, `docs/`, `sdlc-spdd/docs/`, grounding files, dogfood governance artifacts
- Output: this analysis, Milestone 3/4/5 definitions, Work ID requirement stubs, task lists, ROADMAP pointers

### Not in scope

- Implementing the Work IDs (each follows analysis → plan → architect → code)
- Research claims (Milestone 2 froze those; DOC-001 allow-list stands)
- Upstream PRs to `embabel/guide` (forbidden by rule)
- Product features (ADF library, Vue3 tabs) beyond noting their engineering debt

### Deferred

- Make-it-fast items (act on metrics, context-budget telemetry, Vue3 parity) → Milestone 5 outline only
- Resuming SPIKE-001/SPIKE-002 (Guide DICE, local models)

## Measured baseline (2026-09-13, this checkout)

| Measure | Value | Command |
|---------|-------|---------|
| Unit tests | 281 passed, 34 s | `pytest engine/tests_unit` |
| Integration tests | 128 passed, 3.6 s | `pytest engine/tests_integration` |
| Research tests | 87 passed | `pytest tests/research` |
| Bash harnesses | 30 scripts, ~221 cases | `tests/test-*.sh` |
| Unit coverage of `sdlc_engine` | **66.4 %** of 10 551 statements | `--cov=sdlc_engine` |
| Modules under 30 % unit coverage | `viewer/app.py` 0 %, `viewer/html_adf.py` 6 %, `viewer/adf_html.py` 8 %, `installer/dashboard.py` 14 %, `viewer/store.py` 20 %, `installer/app.py` 26 % | coverage JSON |
| Functions with CCN > 15 | **67** of 766 | `lizard -l python engine/src` |
| Functions with CCN > 10 or NLOC > 80 | **153** | `lizard -C 10 -L 80 -w` |
| Longest functions | `installer/app.create_app` 1 056 lines; `cli_parser.build_parser` 679; `viewer/app.create_app` 530 | lizard |
| Highest CCN | 97 (`cli_commands.py`), 85 (`storage_migrate.run`), 75 (`db_rebuild.py`), 64 (`viewer/html_adf.handle_starttag`), 51 (`viewer/adf_html._block`) | lizard CSV |
| Ruff, configured rules (`F401,F811`) on `engine/src scripts` | clean | CI step |
| Ruff `F821` undefined names in `engine/src` | **9** (all in `db_query.py`) | `ruff --select F821` |
| Ruff broad (`E,F,W,B,UP,SIM,C901,PLR09*`) | 190 findings (48 C901, 25 too-many-args, 25 too-many-branches) | `ruff --statistics` |
| Shellcheck (`-S warning`) over scripts/templates/tests | **34** findings, **7 errors** | `shellcheck -f gcc` |
| Doc links | **95 broken / 959 checked** | `scripts/verify-doc-links.sh` |
| Version | `pyproject`/`__init__`/README say `2.0.0a6`; git tags `v2.0.0a7`, `v2.0.0a8` exist; CHANGELOG top is `[Unreleased]` | `git tag` |
| Dogfood registry | 11 of 13 Milestone 2 Work IDs have **no** claim/release event; `SPIKE-004`, `DOC-001` still `active` | `registry.jsonl` |

The largest CLI handlers by lizard are `cmd_issues` (CCN 27, 90 NLOC), `cmd_db` (23), `cmd_template` (20), `cmd_local` (18); `workflow.gate_check` is CCN 25 / 94 NLOC. Treat "handlers over CCN 15" as the finding, not a single number.

## Recommendation

The framework is functionally complete ("make it work" done) and Milestone 2 made its research claims honest. What remains is **engineering consolidation**: the codebase carries two behavioral cores (bash and Python), several god modules, duplicated helpers, gates that prove the checker rather than the diff, and a documentation set whose install-path vocabulary no longer matches what `init` writes. None of this blocks a user today; all of it taxes every future change.

Open three milestones:

- **Milestone 3 — One flow on storage v3** (make it right, code/tests/CI): purge pre-v3 compatibility, retire the bash workflow twin, real lint/complexity gates, split god modules, hermetic test layers, consolidated CI, hardened local web surfaces.
- **Milestone 4 — Documentation truth and release hygiene** (make it right, docs): one authoring root, correct install vocabulary, generated grounding, doc-link gate, current ADRs, version/registry hygiene.
- **Milestone 5 — Make it fast** (outline only): act on FEAT-004/005/015 metrics, context-budget telemetry, Vue3 parity. Not opened until Milestone 3 P0/P1 land.

## Major findings (evidence → Work ID)

### M1. Two behavioral cores: bash workflow twin still maintained

`templates/agent-context/sdlc-workflow.sh` (2 089 LOC) and `sdlc-team-registry.sh` (981 LOC) reimplement `workflow.py`, `registry.py`, `pointer.py`, and a shell `gate` fallback (`sdlc_workflow_gate`, ledger checks via JSON regex at `sdlc-workflow.sh:904–928`). Gate tables carry "keep in sync" comments (`sdlc-workflow.sh:347–348` ↔ `phases.py`). The gate path calls bare `python3` (`:873–887`) while the dispatcher enforces 3.12 via `scripts/lib/python.sh`; a wrong interpreter silently falls back to the shell gate. `cli_commands.cmd_shell` only bridges `scripts/`, not installed `sdlc-spdd/scripts/`.

→ **REF-003-retire-bash-workflow-dual-path**

### M2. Pre-v3 compatibility is still load-bearing, and it forked the archive contract

Storage v3 (`docs/storage-v3.md`) is the only persistence model the project intends to support: committed `spdd/memory/lessons.jsonl` + `registry.jsonl`, gitignored `.sdlc/` runtime, `sdlc-spdd/` as the single home. Yet the code still carries the pre-v3 world: `project.py:57,129–133` falls back to root layouts and `agent-context/harness`; `registry.py` reads the legacy TSV registry; `storage_migrate.py` (317 LOC), `agent_context_upgrade.py` (93), `context_model.py` legacy markdown parsers (`:89+`), and `installer/rollback.py` exist only to move old trees; `upgrade-project.sh` has 43 legacy-path references and archives leftovers under `.sdlc/legacy-layout-archive/`; 40 test files assert legacy behaviors.

The archive command shows the cost. Shell `sdlc_team_archive_work` deletes artifacts (`sdlc-team-registry.sh:626–628,670`, "git history is the audit trail"); Python `ArchiveService._move` relocates them into `spdd/*/archive/` (`archive.py:60–79`) and still sweeps `agent-context/sessions`. `SDLC_ENGINE=auto` routes `archive` to Python, so users get "move" while `docs/storage-v3.md`, `TESTING.md:234`, `ROADMAP.md`, and `MILESTONE-1.md` describe "delete". `tests/test-archive-work.sh:90–99` asserts removal; `engine/tests_unit/test_registry_archive.py:47,96` asserts archive files. Two green suites prove two contracts.

Decision (owner, 2026-09-13): pre-v3 context may be lost. Purge legacy layouts, migrations, and archive folders; one data model, one flow.

### M3. Latent `NameError`s shipped because the lint gate is too narrow

`db_query.py` references `REL_AREA`, `NODE_AREA`, `NODE_LESSON`, `REL_ABOUT`, `NODE_REQUIREMENT`, `REL_REASONS`, `NODE_CANVAS` (lines 164–205) and `_utc_now` (line 425) without importing them. Reproduced: `LocalIndex(project, path).export_sql(...)` raises `NameError: name '_utc_now' is not defined`; `sdlc-engine db export` reaches it via `cli_commands.py:777`. `context_linked_to_section` has no caller. CI runs `ruff --select F401,F811` only (`test-sdlc-engine.yml:45`), so pyflakes' undefined-name check never runs.

→ **BUG-001-db-query-undefined-names**, **CHORE-004-lint-and-complexity-gates-real**

### M4. Complexity gate proves the checker, not the PR

`scripts/check-complexity.py` implements CCN > 10 / NLOC > 80 / CCN-rise on changed files, but CI only runs `scripts/test-check-complexity.sh` (a synthetic repo) and the unit test that wraps it (`test-sdlc-engine.yml:46–49`). No workflow runs `check-complexity.py --base origin/main` on the actual diff. Shellcheck is not run anywhere (only `bash -n`).

→ **CHORE-004-lint-and-complexity-gates-real**

### M5. God modules and CLI-as-monolith

`installer/app.py:154–1209` is one nested `create_app` with every `/api/*` route; `cli_parser.py:9–40` imports every `cmd_*`, so `import sdlc_engine.cli` loads `ContextStore`, `LocalIndex`, `IssueSyncService`, `SunsetService`; handlers print as their API (~100 `print` calls) and `cli.py:61–63` catches bare `Exception`. `canvas.py:668,674,739` raises `SystemExit` from library code. `__init__.py:3–6` imports workflow/registry/archive at package import.

→ **REF-004-split-installer-blueprints**, **REF-005-cli-command-modules**

### M6. Storage records are ad-hoc and appends are not atomic

`LessonRecord` is typed (`lessons_ledger.py:58–144`) but registry events are `dict[str,str]` (`registry.py:85–96`) and `ContextStore`/`PersistResult` are `dict[str, Any]` (`context_store.py:68–87,279–322`). `LEDGER_KINDS` is defined twice (`context_model.py:20`, `lessons_ledger.py:43`). Stage and registry appends are plain `open(..., "a")` with no lock (`lessons_ledger.py:192–193`, `registry.py:144–145`); `io_util.save_json_dict` is non-atomic and bypassed by `persistence.save_config`, `integration_config`, `installer/guide.py:179`.

→ **REF-006-storage-records-and-atomic-appends**

### M7. Guide HTTP transport triplicated

`GuideClient._request` (`guide_client.py:60–97`) coexists with raw `urllib` in `ContextStore.project_to_guide/guide_work/guide_stats` (`context_store.py:279–322`), `installer/guide_compliance.py:87–125`, `installer/guide_ops.py:26–45`. Base-URL resolution is inlined three times. Hardcoded Neo4j default password in `installer/guide.py:132` and `guide_ops.py:140`.

→ **REF-007-single-guide-transport**

### M8. Local web surfaces assume localhost but offer `--lan`

`viewer/store.py:22–48` browses the full filesystem by design; `--lan` binds `0.0.0.0` (`cli_commands.py:902,920`, `viewer/__main__.py:29`); no CSRF/auth on mutating POSTs; `/api/run` shells install/upgrade (`installer/app.py:230–255`). `viewer/pages.py` (1 190 LOC) is a second frontend as Python strings; the Vue3 console pattern is not applied to the ADF viewer. ADF codec logic is duplicated between `jira_format.py` and `viewer/adf_html.py`/`html_adf.py` (`_is_gwt_list_item` at `jira_format.py:399` and `adf_html.py:65`).

→ **REF-008-console-viewer-hardening**, **REF-009-adf-codec-and-viewer-assets**

### M9. Test layers are porous; CI is 26 copy-pasted workflows

Unit suite is documented as "no Flask" (`TESTING.md:106`, `engine/tests_unit/README.md`) but `test_vue3_console_serve.py`, `test_installer_templates_api.py`, `test_installer_playground.py` use Flask test clients and are also counted in the Suite 2 coverage job. Grab-bag files (`test_hard_review_gaps.py`, `test_remaining_cleanup_slices.py`, `test_installer_coverage_gaps.py`) are the only homes for `agent_context_upgrade` and `quiet` coverage. Unit tests shell out to `capture-session-memory.sh`. 26 workflows carry ~31 `checkout`, ~10 `setup-python`, ~11 `pip install -e ./engine` with no `workflow_call`/composite action; installer ≥90 % coverage runs twice; pointer/archive have standalone workflows and also run inside `test-sdlc-workflow.yml`; `validate-command-adapters` ⊂ `validate-command-spec-generation`; Playwright push paths are narrower than PR paths (`test-e2e-playwright.yml:4–16`). `TESTING.md:60,98` says 158 unit tests (actual 276).

→ **CHORE-005-ci-reusable-workflows**, **TEST-004-hermetic-unit-suite-and-fixtures**

### M10. Dogfood adapters lag the templates they were installed from

After applying the install path rewrite, `.cursor/commands/sdlc-next.md` lacks the optional DIF step 11 and `.claude/commands/sdlc-spdd-code.md` lacks Kasana I1 steps 16–20 (Validation, stop-on-repeat-failure, diff-scope) that `templates/` and `spec/commands/*.spec.md` carry. `validate-sdlc-spdd-adapters.yml` did not catch it. `/sdlc-spdd-quick` exists in all three adapter trees with **no** `spec/commands/*.spec.md`, so the generator is not its source of truth.

→ **CHORE-006-dogfood-adapters-and-quick-spec**

### M11. Documentation teaches a layout `init` does not create

`init-project.sh` installs docs to `sdlc-spdd/docs/`; `docs/installing-into-your-project.md:67,220`, `docs/README.md:3,57,155`, `CONTRIBUTING.md:53,94,162` say `docs/sdlc-spdd/`. `docs/first-day-with-sdlc-spdd.md:66` requires "`agent-context/` exists". Shipped grounding templates use `./scripts/sdlc-spdd/sdlc.sh` and `agent-context/harness/` (`templates/cursor/rules/sdlc-spdd.mdc:78–84`, `templates/claude/CLAUDE.md`, `templates/copilot/copilot-instructions.md`), paths that do not exist in a target. `CONTRIBUTING.md:145` cites `work-registry.tsv`. Workflow step count is 16 / "15" / "13" across `docs/workflow.md`, `docs/README.md:86`, `sdlc-spdd/docs/README.md:40`. `design-decisions.md` still describes `agent-context/` + duplicate canvases (SPIKE-004 M7, unfixed). `STARTER-SPEC.md` (1 881 lines) is referenced only by CHANGELOG and design-decisions.

→ **DOC-004-install-path-vocabulary**, **DOC-005-grounding-path-map-codegen**, **DOC-006-design-decisions-v3-and-starter-spec-archive**, **DOC-007-glossary-and-engine-cli-guide**

### M12. Two docs trees, 95 broken links, no link gate

`docs/` (61 md) is the authoring root; `sdlc-spdd/docs/` (45 md) is the dogfood install copy but 5 files have diverged (`storage-v3.md`, `triple-path-context.md`, `spdd-compliance.md`, `adf-template-library-and-vue3-console.md`, `README.md` by design). Shipped copies link orchestrator-only docs (`guide-flow.md`, `dice-projection-runbook.md`, `diagrams/*.svg`) that `shipped-docs-boundary.sh` excludes, so they 404 after install. `verify-doc-links.sh` is not in CI.

→ **CHORE-007-doc-links-gate**, **CHORE-008-single-docs-authoring-root**

### M13. Release and registry hygiene

Tags `v2.0.0a7`/`v2.0.0a8` exist while every declared version is `2.0.0a6` and `test_engine_shared.py:30` pins it; README "Latest release" and "Current focus" (#264–#270, #114) are stale; ROADMAP links archived canvases; `_milestone.yml` for Milestone 2 still says `planned`. `spdd/memory/registry.jsonl` has no events for 11 Milestone 2 Work IDs and leaves `SPIKE-004`/`DOC-001` active; `list-work` reports "done" from canvas status, so the registry is not the truth its docs say it is.

→ **CHORE-009-release-version-hygiene**, **CHORE-010-registry-reconciliation**

### M14. Shell-only session stack and issue-sync mega-service (P2)

`start-agent-session.sh` (625), `capture-session-memory.sh` (504), `resolve-agent-context.sh` (563), `create-work-from-milestone.sh` (498) have no Python twin; `accept` has two verbs (`sdlc.sh accept` shell, `sdlc-engine context accept`). `issues.py` (1 209 LOC) covers draft/push/pull/ADF/link in one class. `create-work-from-milestone.sh` inlines its own canvas body instead of `templates/reasons-canvas`.

→ **REF-010-pythonize-session-and-capture**, **REF-011-split-issue-sync-adapters**

## Minor findings (fold into the Work IDs above)

- `templates/cursor/sdlc-spdd-code.md:56` references `./scripts/sdlc-spdd/resolve-context-backend.sh` (nonexistent path) — DOC-005.
- `docs/engine-v2.md:66–70` says the default engine is shell; `scripts/sdlc.sh` default is `auto` — DOC-004.
- Shellcheck errors: `resolve-agent-context.sh:343` SC2066 (quoted loop runs once), `setup-engine-venv.sh:102–103` SC1087, `tests/test-command-specs.sh:333–355` SC2218, `tests/test-sdlc-engine-shim.sh:63` SC2144 — CHORE-004.
- `ls -1t` for session rotation (`capture-session-memory.sh:220`, `start-agent-session.sh:255,597`) — REF-010.
- `context_model.iter_code_areas`, `context_model.extract_memory_facts`, `installer/guide.resolve_guide_home` have no callers — REF-006.
- `issue_tracker.py` is a re-export shim; `cli.py:9–46` re-exports all `cmd_*` "for compatibility" — REF-005.
- `sdlc-spdd/docs/research/unattended-iterations.md` has no inbound links — CHORE-008.
- `tests/eval` has one test; `pyproject` `testpaths=["tests_unit"]` makes bare `pytest` silently skip two suites — TEST-004.

## Strengths (do not regress)

- Storage v3 is directionally right: one committed ledger, staged captures, derived projections, soft-fail Guide.
- Flask is consistently lazy-imported; runtime has zero dependencies.
- `timeutil.utc_now` adoption is complete; `LessonRecord`, `VerifyReceipt`, `ProcessMetrics`, `RegistryRow` are good typed models to extend.
- Recent PRs (#294–#307) already removed prose-grep and MagicMock-as-proof anti-patterns; `test_live_graph_required_ci.py` is the right meta-test pattern.
- Spec → adapter generation with `--check` in CI works for templates; the gap is only the dogfood copy.
- Diagrams have source + SVG + render script + validation workflow.

## Code areas (for the implementation Work IDs)

| Area | Paths |
|------|-------|
| engine-cli | `engine/src/sdlc_engine/{cli,cli_parser,cli_commands}.py` |
| engine-storage | `lessons_ledger.py`, `registry.py`, `pointer.py`, `context_store.py`, `context_model.py`, `db*.py`, `persistence.py`, `io_util.py` |
| engine-web | `installer/app.py`, `installer/dashboard.py`, `viewer/*.py`, `console-ui/` |
| engine-guide | `guide_client.py`, `guide_query.py`, `installer/guide*.py` |
| shell-workflow | `templates/agent-context/sdlc-*.sh`, `scripts/sdlc.sh`, `scripts/lib/python.sh` |
| shell-session | `scripts/{start-agent-session,capture-session-memory,resolve-agent-context,create-work-from-milestone,accept-lessons}.sh` |
| ci | `.github/workflows/*.yml`, `scripts/check-complexity.py`, `scripts/run-test-suites.sh` |
| docs | `docs/`, `sdlc-spdd/docs/`, `templates/project-docs/`, `templates/{cursor,claude,copilot}` grounding, root `*.md` |

## Domain Keywords

- one-flow
- storage-v3
- purge-legacy
- bash-twin
- lint-gate
- complexity-gate
- shellcheck
- god-module
- atomic-append
- guide-transport
- doc-links
- install-vocabulary
- release-hygiene

## Code Areas

- engine/src/sdlc_engine/cli_commands.py
- engine/src/sdlc_engine/cli_parser.py
- engine/src/sdlc_engine/archive.py
- engine/src/sdlc_engine/project.py
- engine/src/sdlc_engine/registry.py
- engine/src/sdlc_engine/storage_migrate.py
- engine/src/sdlc_engine/db_query.py
- engine/src/sdlc_engine/installer/app.py
- engine/src/sdlc_engine/viewer/
- templates/agent-context/sdlc-workflow.sh
- templates/agent-context/sdlc-team-registry.sh
- scripts/sdlc.sh
- scripts/upgrade-project.sh
- .github/workflows/
- docs/
- sdlc-spdd/docs/

## Assumptions

- Storage v3 is the only supported persistence model. Pre-v3 layouts (`agent-context/` trees, `work-registry.tsv`, feature mirrors, `spdd/*/archive/`) are not migrated; they are ignored or removed. Losing pre-v3 context is accepted.
- Python `sdlc-engine` is the behavioral core going forward (REF-001); bash remains for install/upgrade packaging.
- Version bump and tag reconciliation are a human release decision; CHORE-009 prepares it, it does not cut a release.
- Milestone 5 stays an outline until Milestone 3 P0 and P1 are complete (roadmap posture: do not optimize before it is right).

## Next

1. `/sdlc-spdd-plan @sdlc-spdd/requirements/milestones/milestone-3/SPIKE-005-architecture-review.md` — canvas as the program plan (sequence, stop rules).
2. Start Milestone 3 P0: BUG-001, CHORE-004, CHORE-006 (small, test-first), then REF-002 T01 (archive deletes; drop `spdd/*/archive/` and legacy session dirs).
3. Start Milestone 4 P0 in parallel (docs-only, no engine risk): DOC-004, CHORE-007.
