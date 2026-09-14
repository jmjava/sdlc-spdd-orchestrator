# REASONS Canvas: REF-002-purge-pre-v3-compat — One data model (storage v3)

## Metadata

- Work ID: REF-002-purge-pre-v3-compat
- Work Type: Refactor
- Status: In Progress
- Readiness: Ready For Coding
- Created: 2026-09-14
- Updated: 2026-09-14
- Milestone: milestone-3
- Priority / size: P0 / L
- Depends on: SPIKE-005-architecture-review
- Blocks: REF-006-storage-records-and-atomic-appends
- Related: REF-003-retire-bash-workflow-dual-path, DOC-005-grounding-path-map-codegen
- Requirement: `sdlc-spdd/requirements/milestones/milestone-3/REF-002-purge-pre-v3-compat.md`
- Analysis: `sdlc-spdd/spdd/analysis/REF-002-purge-pre-v3-compat-analysis.md`
- Beck stage: make it right
- Branch: `cursor/milestone-3-ref-002-purge-ebca`
- Skills: none requested (`#`/`!` markers absent)

## R - Requirements

### User Goal

Storage v3 (`sdlc-spdd/` home; committed `spdd/memory/lessons.jsonl` +
`registry.jsonl`; gitignored `sdlc-spdd/.sdlc/` runtime) is the only
persistence model the framework reads or writes. Legacy layouts, migrations,
and archive folders are deleted, not maintained. Losing pre-v3 context is an
accepted cost (owner decision, 2026-09-13).

### Business / Product Goal

One flow (Milestone 3): fewer code paths for REF-003 to retire, one contract
for docs and tests to describe, and an upgrade that cannot fork behavior
between "move", "archive", and "delete".

### Acceptance Criteria

- [x] `archive_work` removes canvas / analysis / review / sync / session /
  state files; no `archive/` directories are created; unit + bash tests
  assert the same contract (T01, #308)
- [ ] `storage migrate`, `agent-context detect|upgrade`, legacy-layout
  archive, and legacy consolidation code paths are deleted with their tests
- [ ] `grep -rn 'agent-context\|work-registry' engine/src` returns nothing;
  in `scripts/` the only hits are the install-source path
  `templates/agent-context/` and the file name `resolve-agent-context.sh`
  (`verify-project-install.sh` keeps its parts-assembled legacy-absent checks)
- [ ] `upgrade-project.sh` / `init-project.sh` contain no legacy detection,
  migration, consolidation, or archive logic (owner 2026-09-14: no refusal
  helper either — pre-v3 trees are unsupported; breaking change accepted)
- [ ] `Project.home` is `root/sdlc-spdd` (or `SDLC_HOME`) unconditionally;
  `Project.harness_dir` is `home/harness`
- [ ] `TESTING.md`, `docs/storage-v3.md` (+ shipped copy), and the upgrade
  docs have no legacy-layout or migration sections; CHANGELOG updated

### Non-Goals

- Changing the v3 record schema or append locking (REF-006)
- Retiring the bash workflow twin, `SDLC_ENGINE`, or `scripts/sdlc.sh`
  lookup branches (REF-003)
- Rewriting template grounding text (`agent-context/harness/`, bare `spdd/`)
  that `framework_rewrite_adapter_paths` translates at install (DOC-005)
- Removing `installer/rollback.py` — it restores v3 upgrade backups
- Embabel upstream PRs

## E - Entities

- `Project` (`project.py`): `root`, `home`, `harness_dir`, `is_single_folder`
- `TeamRegistry` (`registry.py`): `registry.jsonl` event log; TSV fallback
- `StorageMigration` (`storage_migrate.py`) and `AgentContextUpgrade`
  (`agent_context_upgrade.py`) — deleted
- `context_model` legacy parsers (`parse_markdown_table`,
  `extract_prompt_entries`, session-history / lesson-file parsers) — deleted;
  v3 half (`CONTEXT_KINDS`, `GOVERNANCE_GLOBS`, `stable_id`,
  `work_id_from_name`, `NODE_*`) stays
- `installer.detect.LEGACY_MARKERS`
- `quiet.is_quiet` harness-file check
- `adf_work` feature-dir candidates
- Shell helpers in `scripts/lib/framework-install.sh`:
  `framework_merge_dir_into`, `framework_consolidate_path`,
  `framework_prune_legacy_layout_shells`, `framework_archive_legacy_path`,
  `framework_archive_remaining_legacy_layout` — deleted;
  `framework_rewrite_adapter_paths`, `framework_ensure_dir`,
  `framework_ensure_gitignore_runtime`, `framework_is_orchestrator_root` stay
- `upgrade-project.sh` Phase 1 (migrate) / Phase 2 (consolidate) — deleted
- `migrate_playbooks_extensions_to_skills` and its meta helpers in
  `scripts/lib/skills.sh` — deleted (pre-skills harness migration)

### Files likely affected

- `engine/src/sdlc_engine/`: `project.py`, `registry.py`, `quiet.py`,
  `adf_work.py`, `context_model.py`, `cli_parser.py`, `cli_commands.py`,
  `installer/detect.py`; delete `storage_migrate.py`, `agent_context_upgrade.py`
- `engine/tests_unit/`: delete `test_storage_migrate.py`; edit
  `test_remaining_cleanup_slices.py`, `test_hard_review_gaps.py`,
  `test_registry_archive.py`, `test_installer_*`; add `conftest.py` home
  fixture; touch the 22 files that rely on the root fallback
- `scripts/`: `upgrade-project.sh`, `init-project.sh`,
  `lib/framework-install.sh`, `lib/paths.sh`
- `tests/`: delete `test-upgrade-consolidate.sh`,
  `test-framework-install-consolidate.sh`; drop the two playbook-migration
  tests from `test-resolve-agent-context.sh`
- `.github/workflows/test-upgrade-consolidate.yml` — deleted
- docs: `TESTING.md`, `README.md`, `docs/storage-v3.md`,
  `docs/framework-upgrade.md`, `docs/installing-into-your-project.md`,
  `docs/maintaining-your-project.md`, `docs/agent-session-scripts.md`,
  `docs/engine-v2.md`, shipped copies under `sdlc-spdd/docs/`, `CHANGELOG.md`

## A - Approach

Delete in blast-radius order, one operation per commit, suite green after
each. Shell first (T02) so the Python `storage migrate` verb is orphaned
before it is removed (T03) — no commit leaves `upgrade-project.sh` calling a
missing subcommand. Then the two small Python readers (T04 registry TSV, T05
detect/adf/quiet paths). Strict home (T06) is last on the Python side because
it touches 22 test files; it introduces the minimal explicit-home fixture
that TEST-004 later generalizes. Docs (T07) close the Work ID; every
operation also removes the doc sentence that described the behavior it
deleted, so no intermediate commit documents a path that no longer exists.

No legacy awareness remains: no detection, no refusal message, no markers.
Init and upgrade install into `<target>/sdlc-spdd/` and nothing else; what an
old tree looks like is not the framework's concern (breaking change accepted
by the owner). `framework_rewrite_adapter_paths` stays because
template grounding text still needs the install-time rewrite (DOC-005 owns the
text). `installer/rollback.py` stays because upgrade backups are v3.

## S - Structure

### Files to add

- `engine/tests_unit/conftest.py` — `project_home` fixture: creates
  `tmp_path/sdlc-spdd/` and returns `Project(tmp_path)`
- `engine/tests_unit/test_project_home.py` — strict home / harness_dir /
  `SDLC_HOME` override

### Files to delete

- `engine/src/sdlc_engine/storage_migrate.py`
- `engine/src/sdlc_engine/agent_context_upgrade.py`
- `engine/tests_unit/test_storage_migrate.py`
- `tests/test-upgrade-consolidate.sh`
- `tests/test-framework-install-consolidate.sh`

### Files to modify

- listed per operation below

### Test structure

- Unit (pytest, `engine/tests_unit`): parser rejects `storage` and
  `agent-context`; `quiet-status` is top-level; `TeamRegistry.rows()` returns
  `[]` when `registry.jsonl` is absent even if a TSV exists; `detect()` has no
  legacy markers; `is_quiet` reads `project.harness_dir`; strict home.
- Bash (`tests/`): `test-scripts-lib.sh` asserts the consolidation helpers
  are gone; `test-adapter-install.sh` proves a v3 target still inits/upgrades.
- Full: `./scripts/run-test-suites.sh` (or the CI-local wrapper) green
  before and after each operation; `ruff check --select F,E9 engine/src
  scripts`; `shellcheck -S error` over touched shell files.

## O - Operations

### T01 - Archive removes contract artifacts; no `spdd/*/archive/`

- Status: Complete (#308, `d01ad8e`)
- Description: `ArchiveService` deletes canvas / analysis / review / sync /
  hot session briefs / workflow `.state`, appends the `archived` registry
  event, never touches requirements or `lessons.jsonl`; unit and bash tests
  assert the same contract.
- Files: `engine/src/sdlc_engine/archive.py`,
  `engine/tests_unit/test_registry_archive.py`, `engine/tests_unit/test_cli.py`
- Tests: `python -m pytest engine/tests_unit/test_registry_archive.py`
- Validation: no `spdd/*/archive/` directory exists in the tree after archive

### T02 - Delete upgrade consolidation, migration hooks, and legacy harness fallbacks

- Status: Complete
- Description: Delete Phase 1 (legacy memory → `storage migrate`) and Phase 2
  (merge / prune / `legacy-layout-archive`) from `upgrade-project.sh`, the
  `--consolidate` flag, the "Consolidated" summary, and the root
  `milestone-*.md` lookup. Delete `framework_merge_dir_into`,
  `framework_consolidate_path`, `framework_prune_legacy_layout_shells`,
  `framework_archive_legacy_path`, `framework_archive_remaining_legacy_layout`
  from `framework-install.sh`. Delete `migrate_playbooks_extensions_to_skills`
  and its meta helpers from `skills.sh` (and the calls in init/upgrade). Remove
  the `agent-context/harness` fallbacks from `paths.sh`. Delete the two
  consolidation harnesses, their workflow, and the two playbook-migration tests
  in `test-resolve-agent-context.sh`. No detection or refusal logic is added.
- Files: `scripts/upgrade-project.sh`, `scripts/init-project.sh`,
  `scripts/lib/framework-install.sh`, `scripts/lib/skills.sh`,
  `scripts/lib/paths.sh`, `tests/test-upgrade-consolidate.sh` (delete),
  `tests/test-framework-install-consolidate.sh` (delete),
  `.github/workflows/test-upgrade-consolidate.yml` (delete),
  `tests/test-scripts-lib.sh`, `tests/test-resolve-agent-context.sh`,
  `tests/test-sdlc-workflow.sh`, `scripts/start-agent-session.sh`,
  `scripts/capture-session-memory.sh`, `scripts/resolve-context-backend.sh`
- Tests: `./tests/test-scripts-lib.sh`; `./tests/test-resolve-agent-context.sh`; `./tests/test-sdlc-workflow.sh`;
  `./tests/test-adapter-install.sh`; `shellcheck -S error` on touched shell files
- Validation: `rg -n 'legacy-layout-archive|consolidate_into_home|framework_archive|migrate_playbooks' scripts tests .github` is empty; a v3 target still inits and upgrades

### T03 - Delete `storage migrate` / `agent-context detect|upgrade` and the migration modules

- Status: Complete (quiet.py re-homed to `<home>/harness/quiet-mode.md` here rather than in T05, since the quiet test was rewritten in this operation)
- Description: Remove `storage_migrate.py`, `agent_context_upgrade.py`, the
  `storage` subparser, the `agent-context` subparser, `cmd_storage`, and
  `cmd_agent_context`. Re-home `quiet-status` as a top-level verb backed by
  a new `cmd_quiet_status`. Delete the legacy parsers block in
  `context_model.py` (from the `# --- legacy parsers` marker to end of file)
  and its docstring sentence. Delete `test_storage_migrate.py`; rewrite the
  legacy-seeding tests in `test_remaining_cleanup_slices.py` and
  `test_hard_review_gaps.py` to keep only the v3 assertions they also make
  (quiet mode, session brief location, ledger untouched).
- Files: `engine/src/sdlc_engine/storage_migrate.py` (delete),
  `engine/src/sdlc_engine/agent_context_upgrade.py` (delete),
  `engine/src/sdlc_engine/context_model.py`, `engine/src/sdlc_engine/cli_parser.py`,
  `engine/src/sdlc_engine/cli_commands.py`,
  `engine/tests_unit/test_storage_migrate.py` (delete),
  `engine/tests_unit/test_remaining_cleanup_slices.py`,
  `engine/tests_unit/test_hard_review_gaps.py`, `docs/engine-v2.md`,
  `docs/framework-upgrade.md`, `sdlc-spdd/docs/framework-upgrade.md`
- Tests: `python -m pytest engine/tests_unit -q`; `ruff check --select F,E9 engine/src`
- Validation: `sdlc-engine storage status` and `sdlc-engine agent-context detect` exit 2 (argparse unknown command); `sdlc-engine quiet-status` exits 0; `rg -n 'storage_migrate|agent_context_upgrade|StorageMigration' engine scripts docs` is empty

### T04 - `TeamRegistry` reads `registry.jsonl` only

- Status: Complete
- Description: Remove `legacy_tsv_path`, the TSV branch in `rows()`, the
  synthetic `legacy-tsv` event, and the module docstring paragraph. Add a
  unit test that seeds `agent-context/work-registry.tsv` without
  `registry.jsonl` and asserts `rows() == []`.
- Files: `engine/src/sdlc_engine/registry.py`,
  `engine/tests_unit/test_registry_archive.py`
- Tests: `python -m pytest engine/tests_unit/test_registry_archive.py engine/tests_unit/test_cli.py -q`
- Validation: `rg -n 'tsv|legacy' engine/src/sdlc_engine/registry.py` is empty

### T05 - Detect, ADF, and quiet-mode paths are v3-only

- Status: Complete (quiet.py landed in T03; `harness_dir` fallback removal stays in T06 with strict home)
- Description: Drop `LEGACY_MARKERS` and the two sprawled entries in
  `MARKERS` (`spdd/memory/lessons.jsonl`, `scripts/sdlc-spdd/sdlc.sh`) from
  `installer/detect.py`; only v3 and adapter markers remain. Drop the
  `root/agent-context/features` candidate in `adf_work.py`; make
  `quiet.is_quiet` read `project.harness_dir / "quiet-mode.md"`. Update the
  affected unit tests; check `console-ui` for a consumer of the removed
  detect field.
- Files: `engine/src/sdlc_engine/installer/detect.py`,
  `engine/src/sdlc_engine/adf_work.py`, `engine/src/sdlc_engine/quiet.py`,
  `engine/tests_unit/test_remaining_cleanup_slices.py`,
  `engine/tests_unit/test_adf_work.py`, `engine/tests_unit/test_installer_*.py`
- Tests: `python -m pytest engine/tests_unit -q`
- Validation: `rg -n 'agent-context' engine/src` is empty

### T06 - Strict `Project.home` and `harness_dir`; explicit test home

- Status: Complete
- Description: `home` returns `SDLC_HOME` or `root / "sdlc-spdd"` with no
  directory probe; `harness_dir` returns `home / "harness"`; remove
  `is_single_folder` (no callers) and the legacy paragraph in the module
  docstring. Add `engine/tests_unit/conftest.py` with a `project_home`
  fixture and move the 22 test files that relied on `home == root` onto it
  (or onto `project.home`-relative paths). Run `tests/research/` and the bash
  harnesses that drive the Python engine to confirm no hidden dependency.
- Files: `engine/src/sdlc_engine/project.py`,
  `engine/tests_unit/conftest.py` (add), `engine/tests_unit/test_project_home.py` (add),
  the 22 unit test files listed in the analysis measurement,
  `tests/research/test_ref001_sut.py`, `tests/research/test_cretrieve.py` (verify only)
- Tests: `python -m pytest engine/tests_unit -q`; `python -m pytest tests/research -q`; `./scripts/run-test-suites.sh`
- Validation: unit count unchanged minus deleted legacy tests; `rg -n 'is_single_folder|agent-context' engine/src` is empty

### T07 - Docs describe only v3; CHANGELOG

- Status: Complete
- Description: Remove the "legacy layouts / migrating a legacy install"
  sections from `docs/storage-v3.md`; the "Storage migration and
  consolidation" section from `docs/framework-upgrade.md`; the migration
  sentences in `installing-into-your-project.md`, `maintaining-your-project.md`,
  `agent-session-scripts.md`, `README.md:307-308`; the `storage` verbs from
  `docs/engine-v2.md`; the `legacy-layout-archive` paragraph and consolidate
  harness rows from `TESTING.md`. State in `framework-upgrade.md` that v3 is
  the only layout and older installs are unsupported. Sync shipped copies under `sdlc-spdd/docs/`.
  CHANGELOG `[Unreleased]` → Removed / Changed entries.
- Files: `docs/storage-v3.md`, `docs/framework-upgrade.md`,
  `docs/installing-into-your-project.md`, `docs/maintaining-your-project.md`,
  `docs/agent-session-scripts.md`, `docs/engine-v2.md`, matching
  `sdlc-spdd/docs/*.md`, `README.md`, `TESTING.md`, `CHANGELOG.md`
- Tests: `./scripts/verify-docgen-dev-boundary.sh` (if applicable); the docs
  link check used in CI
- Validation: `rg -n -i 'storage migrate|legacy-layout-archive|consolidat' docs sdlc-spdd/docs README.md TESTING.md` returns only historical CHANGELOG lines

## N - Norms

- One operation per commit; each commit leaves unit + touched bash suites green.
- Delete, don't deprecate: no `--legacy`, no "for safety" branch, no
  deprecation warning that keeps the path alive (milestone stop rule).
- The doc sentence that describes a deleted path goes in the same commit.
- Shipped docs under `sdlc-spdd/docs/` mirror `docs/` for every touched file.
- `ruff check --select F,E9` and `shellcheck -S error` clean on touched files.
- Stage progress after each operation with `./sdlc-spdd/scripts/sdlc.sh capture`
  (verify receipt: command, exit, pass).

## S - Safeguards

- Never truncate, filter, or delete `spdd/memory/lessons.jsonl`
  (`pattern:CHORE-003-dogfood-ledger:memory:chore-003-restore`).
- Never hand-edit `spdd/memory/registry.jsonl`; only `sdlc.sh claim/release`.
- Keep the bash workflow twin and `SDLC_ENGINE` behavior for REF-003, but its
  executable paths are v3-only (owner direction, 2026-09-14).
- Do not rewrite template grounding text (DOC-005) or remove
  `framework_rewrite_adapter_paths`.
- Keep `installer/rollback.py` and `/api/rollback`.
- `SDLC_HOME` override remains; `SDLC_ROOT` remains.
- `verify-project-install.sh` legacy-absent assertions stay (they enforce v3).
- No Embabel upstream.

## Architecture Notes (architect pass, 2026-09-14)

- Entities complete for locked scope; `is_single_folder` has no callers
  outside `project.py` (grep), so T06 removes it outright.
- `context_model` split is clean: consumers (`db.py`, `db_query.py`,
  `db_rebuild.py`) import only v3 names; the legacy parsers are consumed by
  `storage_migrate` alone.
- `test-scripts-lib.sh` never covered the consolidation helpers, so deleting
  them only requires removing the two dedicated harnesses and their workflow.
- Console impact of T05 is nil at the API shape level (`markers`,
  `recommendation` keys unchanged).
- Owner decision 2026-09-14: no refusal / detection helper. A first draft of
  T02 added one; it was removed before commit. Breaking change accepted.
- Owner follow-up 2026-09-14: finish v3-only behavior now. This supersedes the
  earlier defer for path fallbacks in the retained bash twin; the twin remains,
  but root-layout lookups and duplicate-canvas synchronization are deleted.
- T06 is the only operation with a wide test diff; the measured baseline is
  72 failing tests across 22 files with strict home, so the fixture-first
  approach (conftest, then mechanical path moves) is required, not optional.
- Test strategy: unit for every deleted branch's replacement behavior;
  bash for the refusal; full `run-test-suites.sh` after T02, T03, T06, T07.
- Quality gates: `ruff --select F,E9`, `shellcheck -S error`,
  `check-complexity.py --base main` (no new function may exceed CCN 10 /
  80 NLOC).
- Readiness: Ready For Coding. Optional DIF fold not run (`dif-fold.sh` absent).

## Review Checklist

- [x] T01 archive contract
- [x] T02 consolidation / migration deletion
- [x] T03 migration modules gone
- [x] T04 registry JSONL only
- [x] T05 detect / adf / quiet v3-only
- [x] T06 strict home + fixture
- [x] T07 docs + CHANGELOG
- [x] Acceptance grep (refined) clean
- [ ] Full suite green

## Sync Notes

- 2026-09-14 — Canvas created after T01 had already landed in #308 ahead of
  the canvas; T01 recorded Complete from the merged commit.

## Final Status

- Readiness: Ready For Coding
- Status: In Progress
