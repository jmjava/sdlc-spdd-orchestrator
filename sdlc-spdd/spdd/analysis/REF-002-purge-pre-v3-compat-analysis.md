# REF-002 Analysis — Purge pre-v3 persistence compatibility; one data model

## Metadata

- Work ID: REF-002-purge-pre-v3-compat
- Requirement: `sdlc-spdd/requirements/milestones/milestone-3/REF-002-purge-pre-v3-compat.md`
- Milestone: Milestone 3 — One flow on storage v3 (P0, size L)
- Opened by: `sdlc-spdd/spdd/analysis/SPIKE-005-architecture-review-analysis.md` finding M2
- Timestamp: 2026-09-14
- Jira key: none (frontmatter `jira_key: ""`, read-only)
- Beck stage: make it right
- Context backend: `CONTEXT_BACKEND=files` (on-demand retrieval only)
- Prior lessons consulted: `pattern:CHORE-003-dogfood-ledger:memory:chore-003-restore`
  ("Archive contracts, not the lessons ledger") — archive may delete canvas /
  analysis / review / sync / session briefs but must never truncate
  `spdd/memory/lessons.jsonl`. Already honored by T01 (#308).

## Scope Lock

### In Scope for This Work

Delete, do not maintain, every code path that reads or writes a pre-v3
layout. Storage v3 is: `<root>/sdlc-spdd/` as the only home; committed
`spdd/memory/lessons.jsonl` + `spdd/memory/registry.jsonl`; gitignored
`sdlc-spdd/.sdlc/` runtime. Owner decision 2026-09-13: pre-v3 context may
be lost.

1. **Archive contract** (T01, landed in #308): `ArchiveService` removes
   contract artifacts, appends the `archived` registry event, creates no
   `spdd/*/archive/` folders, sweeps no `agent-context/sessions`.
2. **Python engine — migration and upgrade shims**: `storage_migrate.py`
   (317 LOC), `agent_context_upgrade.py` (93 LOC), the `storage` and
   `agent-context detect|upgrade` CLI subcommands (`cli_parser.py:603-625`,
   `cli_commands.py:454-500`), and the legacy markdown parsers in
   `context_model.py:89-239` whose only consumer is `storage_migrate`.
3. **Python engine — legacy readers**: `TeamRegistry.rows()` read-only TSV
   fallback (`registry.py:7-9, 59-61, 99-115`); `Project.home` root fallback
   and `Project.harness_dir` `agent-context/harness` fallback
   (`project.py:56-64, 127-133`); `installer/detect.py` `LEGACY_MARKERS`;
   `adf_work.py:104` `agent-context/features` candidate; `quiet.py:28`
   hard-coded `agent-context/harness/quiet-mode.md`.
4. **Shell — consolidation**: `upgrade-project.sh` Phase 1 (legacy memory →
   `storage migrate`) and Phase 2 (merge root trees into home, prune
   shells, archive leftovers to `.sdlc/legacy-layout-archive/`);
   `scripts/lib/framework-install.sh` helpers `framework_merge_dir_into`,
   `framework_consolidate_path`, `framework_prune_legacy_layout_shells`,
   `framework_archive_legacy_path`, `framework_archive_remaining_legacy_layout`;
   `scripts/lib/paths.sh:96,109-110` `agent-context/harness` fallbacks;
   `init-project.sh:201` "home or legacy root" milestone lookup. Replacement
   behavior: when a pre-v3 layout is detected, `upgrade-project.sh` refuses
   with one clear message that names the offending paths and points to a
   fresh `init-project.sh`.
5. **Tests**: delete `engine/tests_unit/test_storage_migrate.py`; delete the
   legacy-seeding tests in `test_remaining_cleanup_slices.py` and
   `test_hard_review_gaps.py`; delete `tests/test-upgrade-consolidate.sh`,
   `tests/test-framework-install-consolidate.sh`, and
   `.github/workflows/test-upgrade-consolidate.yml`; add a refusal test for
   `upgrade-project.sh`; move the 72 unit tests (22 files) that today rely on
   `Project(tmp_path).home == tmp_path` onto an explicit `sdlc-spdd/` home.
6. **Docs in the same PR as the behavior**: `TESTING.md:219`,
   `docs/storage-v3.md:47` and the shipped copy `sdlc-spdd/docs/storage-v3.md`,
   `docs/engine-v2.md` (if it lists `storage migrate`), README upgrade notes,
   CHANGELOG `[Unreleased]`.

### NOT in Scope (Deferred)

| Item | Why deferred | Target |
|------|--------------|--------|
| `templates/{cursor,claude,copilot}/**` grounding text that still says `agent-context/harness/`, `scripts/sdlc-spdd/`, bare `spdd/` and is rewritten at install by `framework_rewrite_adapter_paths` | Template *text*, not a code path; owned by the grounding path-map codegen | DOC-005-grounding-path-map-codegen (Milestone 4) |
| `scripts/sdlc.sh` legacy `../../agent-context/sdlc-workflow.sh` lookup branch | The whole workflow lookup is deleted with the bash twin | REF-003-retire-bash-workflow-dual-path |
| `templates/agent-context/sdlc-{workflow,team-registry,pointer}.sh` legacy paths | Files are deleted wholesale | REF-003 |
| `installer/rollback.py` and `/api/rollback` | Restores **v3** upgrade backups under `.sdlc-spdd-upgrade-backups/`; not a pre-v3 layout. SPIKE-005 M2 over-stated this; requirement wording "rollback-of-legacy" is satisfied by deleting the legacy-layout *archive*, not the backup restore | keep (no Work ID) |
| `integration_config.py` fallback to `.sdlc/issue-tracker-config.json` | Config-file rename inside the v3 runtime dir, not a layout | REF-011-split-issue-sync-adapters |
| `installer/guide.py` legacy `~/github/jmjava/guide` clone path; viewer `*_legacy` URL routes; `issue_tracker.py` "legacy save API" | Not persistence layouts | none |
| v3 record schema, typed records, locked appends | Explicit non-goal | REF-006-storage-records-and-atomic-appends |
| `verify-project-install.sh` legacy-absent assertions | Already v3-consistent (asserts legacy paths are *absent*); keep | none |

### Reference Materials (Context Only, Not Deliverables)

- `docs/storage-v3.md` — the contract being made the only contract
- `sdlc-spdd/spdd/analysis/SPIKE-005-architecture-review-analysis.md` §M2
- `sdlc-spdd/spdd/canvas/REF-001-engine-single-source.md` — precedent for a
  one-operation-per-PR refactor canvas in this repo

## Domain Keywords

- home, root, single-folder layout, sprawled layout
- storage v3, ledger, registry (JSONL), registry TSV
- migration, consolidation, prune, legacy-layout archive, upgrade backup
- archive (Work ID), contract artifacts
- harness, quiet mode
- refusal, fresh init

## Code Areas

- `engine/src/sdlc_engine/` core: `project.py`, `registry.py`, `quiet.py`,
  `adf_work.py`, `context_model.py`, `cli_parser.py`, `cli_commands.py`
- `engine/src/sdlc_engine/` to delete: `storage_migrate.py`,
  `agent_context_upgrade.py`
- `engine/src/sdlc_engine/installer/detect.py`
- `engine/tests_unit/` (22 files touched by the home change; 3 files with
  legacy-seeding tests)
- `scripts/`: `upgrade-project.sh`, `init-project.sh`, `lib/framework-install.sh`,
  `lib/paths.sh`
- `tests/`: `test-upgrade-consolidate.sh`, `test-framework-install-consolidate.sh`,
  `test-scripts-lib.sh`
- `.github/workflows/test-upgrade-consolidate.yml`
- docs: `TESTING.md`, `docs/storage-v3.md`, `sdlc-spdd/docs/storage-v3.md`,
  `docs/engine-v2.md`, `README.md`, `CHANGELOG.md`

## Existing Concepts

- **Project home** (`project.py`): `home = root/sdlc-spdd` when that dir
  exists, else `root`. Every path helper hangs off `home`. `SDLC_HOME` env
  override exists and stays. `is_single_folder` is derived from the fallback.
- **Harness dir**: `home/harness`, else `home/agent-context/harness`.
- **TeamRegistry**: JSONL event log at `spdd/memory/registry.jsonl`; a
  read-only TSV fallback parses `agent-context/work-registry.tsv` when the
  JSONL file is absent and emits synthetic `legacy-tsv` events.
- **StorageMigration**: one-shot export of `agent-context/{memory,sessions,
  features}`, `work-registry.tsv`, `spdd/memory/{lessons,entries,sessions,…}`
  into `.sdlc/legacy-export/`, conversion into the lessons ledger, marker
  `.sdlc/storage-v3-migrated`. `AgentContextUpgrade` wraps it for the
  `agent-context upgrade` CLI.
- **context_model legacy parsers**: `parse_markdown_table`,
  `extract_prompt_entries`, session-history and lesson-file parsers; the v3
  half of the module (`CONTEXT_KINDS`, `GOVERNANCE_GLOBS`, `stable_id`,
  `work_id_from_name`, `NODE_*`) is consumed by `db.py`, `db_query.py`,
  `db_rebuild.py` and stays.
- **Upgrade consolidation** (shell): `upgrade-project.sh` merges root
  `requirements/ spdd/ session-notes/ harness/ agent-context/* scripts/sdlc-spdd
  .sdlc/` into `sdlc-spdd/`, prunes empty shells, archives leftovers under
  `sdlc-spdd/.sdlc/legacy-layout-archive/<stamp>/`.
- **Upgrade backups** (`installer/rollback.py`): v3 feature, unrelated to
  layout; stays.
- **Quiet mode**: `SDLC_QUIET=1`, `--quiet`, or a `quiet-mode.md` harness file.
  The Python check hard-codes the legacy harness path.

## New Concepts

- **Strict home**: `Project.home` is `root/sdlc-spdd` (or `SDLC_HOME`),
  unconditionally. No layout probing. `is_single_folder` becomes a constant
  `True` or is removed with its callers.
- **Legacy refusal**: `upgrade-project.sh` detects any of
  `agent-context/`, root `spdd/`, root `requirements/` (when
  `sdlc-spdd/` is absent), `scripts/sdlc-spdd/`, `docs/sdlc-spdd/`,
  `work-registry.tsv`, and exits non-zero with a single message: the paths
  found, that v3 is the only supported layout, and the fresh-init command.
  No moving, no archiving.
- **Explicit test home**: a shared pytest fixture that creates
  `tmp_path/sdlc-spdd/` and returns a `Project` whose `home` is that dir,
  replacing implicit reliance on the root fallback. (TEST-004 later
  generalizes this into the installed-target fixture; REF-002 introduces the
  minimal form it needs.)

## Strategic Direction

- **Order by blast radius, smallest first, one operation per PR-sized
  commit.** Migration shims (T02) have three test files and two importers;
  the registry TSV fallback (T03) has one; detect/adf/quiet paths (T04) have
  a handful. The strict home (T05) touches 22 test files and is done last on
  the Python side so every earlier step lands green. Shell refusal (T06) and
  docs (T07) follow.
- **Delete, don't deprecate.** No "for safety" branches (milestone stop rule).
  `storage` and `agent-context detect|upgrade` subcommands disappear from the
  parser; the `agent-context quiet-status` verb is the only survivor and is
  re-homed as a top-level `quiet-status` because the parent name is itself
  the legacy layout.
- **Refuse, don't consolidate.** An upgrade onto a sprawled tree is a
  user-visible stop with a pointer to `init-project.sh`; the refusal is
  tested in bash the same way the consolidation used to be.
- **Keep `framework_rewrite_adapter_paths`.** It still turns template
  grounding text into installed paths; that text is DOC-005's problem.
- **`installer/rollback.py` stays.** It is the v3 upgrade-backup restore;
  the requirement's "rollback-of-legacy" is met by deleting the
  legacy-layout archive.
- **Docs move with the behavior**: `TESTING.md` §upgrade, `storage-v3.md`
  "legacy layouts" paragraph, README upgrade notes, CHANGELOG.

## Risks and Gaps

1. **72 unit tests depend on the root fallback** (measured: strict `home`
   → 72 failed / 212 passed across 22 files). Mechanical but wide; must be
   its own operation with the suite green before and after. Research tests
   (`tests/research/`) and bash harnesses that drive the engine against a
   temp dir without `sdlc-spdd/` need the same check.
2. **Bash harnesses that seed `agent-context/`** to exercise the shell twin
   (`test-sdlc-workflow.sh`, `test-sdlc-pointer.sh`, `test-archive-work.sh`,
   …) are REF-003's. REF-002 must not break them: strict `home` only affects
   the Python engine; `SDLC_ENGINE=shell` paths keep reading their own layout
   until REF-003 deletes them. Verify with the full `run-test-suites.sh`.
3. **Acceptance grep is over-broad as written.** `grep -r 'agent-context\|
   work-registry' engine/src scripts templates` will always match the script
   name `resolve-agent-context.sh`, the install source `templates/agent-context/`,
   and template grounding text (DOC-005). Refined acceptance for this Work ID:
   `engine/src` has zero hits; `scripts/` hits are only the
   `templates/agent-context/` source path and the `resolve-agent-context.sh`
   file name; `verify-project-install.sh` keeps its parts-assembled
   legacy-absent assertions.
4. **`is_single_folder` callers** — need a grep before T05; if the property
   is used to branch behavior, those branches are legacy too.
5. **`installer/detect.py` LEGACY_MARKERS feed the console Install tab.**
   Removing them changes the detect card payload; the Vue tab and its
   Playwright test may assert the field. Check `console-ui` for `legacy`.
6. **Orchestrator dogfood is already v3** (`sdlc-spdd/` exists at root), so
   the strict home is a no-op for this repo's own workflow; the risk is
   entirely in tests and third-party installs still on a sprawled layout,
   which the refusal message now handles.

## Recommendation

Proceed to `/sdlc-spdd-plan`. Scope is locked; the only clarification made
is recorded above (rollback.py stays; template text is DOC-005). Operations
for the canvas, in order: T02 migration shims, T03 registry TSV, T04
detect/adf/quiet paths, T05 strict home + test fixture, T06 shell refusal +
helper deletion + harness swap, T07 docs. T01 is already Complete on `main`.

Next command:

    /sdlc-spdd-plan @sdlc-spdd/spdd/analysis/REF-002-purge-pre-v3-compat-analysis.md
