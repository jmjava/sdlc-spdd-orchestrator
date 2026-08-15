# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- Engine polish: shared `timeutil` / `io_util` / `placeholders` / installer `process_util`; `__version__` aligned to `2.0.0a6`; GitHub link sentinels treat `N/A` as empty
- Engine split: CLI handlers/parser (`cli_commands`, `cli_parser`) and SQLite index (`db_schema`, `db_rebuild`, `db_query`) — public `sdlc_engine.cli` / `sdlc_engine.db` imports unchanged
- Ops console: dashboard helpers extracted to `installer/dashboard.py` (Flask wrappers keep existing monkeypatches)
- Guide dogfood default → **`jmjava/orch-guide`** @ **`sdlc-spdd-projection-v2`** (standalone home; cutover from `jmjava/guide`)
- **`jmjava/orch-guide` seeded** (Phase 2): exact mirror of `jmjava/guide` heads+tags; not an Embabel fork
- SPIKE-089 / agent-context cleanup docs: Guide dual-read marked complete; issue #89 closeable
- FEAT-013 closed **fork-only**; orchestrator rule `.cursor/rules/no-embabel-guide-upstream.mdc` forbids asking/opening Embabel Guide PRs

### Added

- Vue3 ops console **Dashboard** + **Issues** tabs (parity with the Flask console) and Playwright coverage for refresh, tracker save/toggle, link preview, and sync dry-run
- Vue3 Persistence **Check ledger parity** / **Parity + repair** buttons (same `/api/persistence/parity` as the Flask console)
- Vue3 Playwright: Issues Jira tracker select, health refresh, persistence parity, rollback dry-run restore, Guide config save
- Experimental Guide stack: raise orch-guide codegen-gradle wrapper download timeout (10s → 180s), prefetch Gradle in CI, fail fast on Maven `BUILD FAILURE`, and skip live Guide+Neo4j (plus Vue `guide_live`) when `repo.embabel.com` is unreachable — ADF viewer live still runs

## [2.0.0a6] - 2026-08-08

Agent-context cleanup program landed on `main` (#109).

### Added

- Lean stay-set memory under `spdd/memory/` + hot sessions under `.sdlc/sessions/`
- Triple-path ContextStore (git-pointers / SQLite / Guide) with soft-fail secondaries
- Pointer ledger, SQLite schema v4 graph + capability coverage
- Quiet / product-test mode (`SDLC_QUIET`, harness marker)
- Ops console **Persistence** tab + `sdlc-engine context backends` (`CONTEXT_BACKENDS`)
- Work-scoped progress excerpts on resolve (`.sdlc/resolved/progress-<WID>.md`)
- Program docs under `docs/agent-context-cleanup/`

### Changed

- Feature mirrors no longer required for progress/requirement/review/sync/retro verify paths
- `resolve-context-backend.sh` emits `CONTEXT_BACKENDS` set; honors explicit guide-dice opt-out
- DB rebuild ingests capture-format progress (`### <ts> - <WID> - <phase>`)

### Notes

- At release time Guide lean+legacy dual-read (#89) was still pending; later merged on `jmjava/guide` via PR #7 and pinned as `sdlc-spdd-projection-v2` (see Unreleased).

## [Prior unreleased notes (pre-2.0.0a6)]

### Added

- Analysis Scope Lock-In: `/sdlc-spdd-analysis` locks IN/NOT scope before generation;
  guidance in `docs/analysis-phase-scope-validation.md` (FEAT-009)
- Jira-compatible requirements format: YAML frontmatter schema, CHORE/feature templates,
  `_milestone.yml`, `scripts/validate-requirements-format.sh`,
  `docs/jira-compatible-requirements-format.md` (FEAT-010)
- Milestone subdirectory layout: preferred
  `requirements/milestones/milestone-N/MILESTONE-N.md` with root `milestone-*.md`
  still supported; migration notes in `docs/jira-compatible-requirements-format.md` (FEAT-011)
- Session-brief archive/rotation in `start-agent-session.sh` (`--session-limit`,
  `--no-session-rotate`) → `agent-context/sessions/archive/` (FEAT-012)
- Prompt-optimization ledger + capture metrics (`--readiness`, `--review-result`,
  `--rework`, `--context-files`); ledger rotation; Kind: `metric` (FEAT-004)
- Canvas readiness vocabulary in `validate-reasons-canvas.sh` + leading indicators
  `--validate-cycles` / `--review-cycles`; plan/architect/create-work aligned (FEAT-005)
- CI: `test-canvas-readiness.yml`, `test-scripts-lib.yml`, `validate-requirements-format.yml`;
  dogfood `spdd/canvas` in `validate-canvas.yml`
- `/sdlc-spdd-commit-message` lifecycle command + Python engine `commit-message` diff report (FEAT-008): `sdlc.sh commit-message` collects staged/unstaged/ahead-of-base diffs; slash command drafts a paste-ready commit message (does not commit); Cursor/Copilot/Claude adapters + docs/tests (closes [#41](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/41))
- Local regenerable SQLite index (FEAT-007): `sdlc.sh db rebuild|status|query|export` → `.sdlc/index.sqlite` (gitignored); FTS5 search; JSON/SQL dump; docs in `docs/local-sqlite-index.md`
- Python orchestration engine v2 (`engine/sdlc_engine`) with CLI + pytest; `scripts/sdlc.sh` supports `SDLC_ENGINE=auto|python|shell` (FEAT-006)
- Engine milestone sync usability: `links`, `sync-links --repair`, `sync-roadmap`, `issues draft|push|pull` for Jira/GitHub; claim auto-reads `## Jira` Key and `## GitHub` Number
- Local/offline work sessions (`LOCAL-*`): `sdlc.sh local start|list|capture|shelf|resume|promote|abandon` — machine-private under `.sdlc/local-sessions/` until promoted into a documented Work ID
- Issue sync test harness: mocked Jira HTTP + fake `gh` write-back tests; live GitHub Issues integration (`SDLC_GITHUB_INTEGRATION=1`) and CI job with `issues: write`
- Jira description formatting: markdown → ADF (Cloud v3) / wiki (Server v2), structured sections from milestone `## Jira`, `issues draft --format adf|wiki`, pull ADF→markdown
- Shared `scripts/lib/` helpers + consumer migration (FEAT-001); `verify-script-lib-duplicates.sh`
- Canonical `spec/commands/*.spec.md` → generated Cursor/Copilot/Claude adapters (FEAT-002)
- Extension manifest + resolver fallback (FEAT-003)
- `sdlc.sh archive` / `archive --all`: move Complete/Cancelled Work ID artifacts into `archive/` folders (closes [#29](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/29))
- Expanded CI/regression harnesses: `test-scripts-lib`, `test-extension-manifest`, `test-command-spec-generation`, `test-archive-work`, `test-integration-merge`

### Fixed

- Canvas operation inference on mawk: `_wf_infer_next_operation` used `{2}` brace
  quantifiers that never matched; use `[0-9][0-9]` (Test 12)
- Empty Final Status `- Status:` no longer keeps the last T## incomplete (Test 12b)
- Architect readiness vocabulary aligned with FEAT-005 (`needs-redesign`, `blocked`, …)

- SDLC pointer manager (`agent-context/sdlc-pointer.sh`): persistent Work ID in `.sdlc/pointer`, guarded execution wrappers ([#20](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/20), closes [#19](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/19))
- Workflow CLI (`scripts/sdlc.sh` / `scripts/sdlc-spdd/sdlc.sh`): phase/gate tracking, `next`/`advance`/`skip`/`shelf`/`resume`/`sync`, guarded `capture` ([#21](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/21))
- Team Work ID registry (`agent-context/work-registry.tsv`, `sdlc-team-registry.sh`): `claim`/`release`/`team`/`list-work`, stale TTL, branch/PR/Jira notes ([#21](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/21))
- `/sdlc-spdd-whereami` assistant command (Cursor, Copilot, Claude) — chat orientation aligned with `sdlc.sh next` ([#21](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/21))
- Workflow agent commands (`/sdlc-claim`, `/sdlc-shelf`, `/sdlc-advance`, `/sdlc-next`, `/sdlc-team`) for Cursor, Copilot, and Claude — chat wrappers for `sdlc.sh claim|shelf|advance|next|team` (closes [#23](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/23))
- Milestone `## Jira` draft convention in `requirements/milestones/<WORK-ID>.md`; auto-link on claim
- CI regression harnesses: `tests/test-sdlc-pointer.sh`, `tests/test-sdlc-workflow.sh`
- Claude Code support as a third assistant adapter: `templates/claude/` command pack
  and `CLAUDE.md`, `scripts/install-claude-commands.sh`, `--claude` flags on
  setup/init/upgrade, `--require-claude` install verification, Claude command-pack
  parity validation, CI path coverage, and `docs/claude-usage.md`
- Always-on Cursor operating-model rule (`templates/cursor/rules/sdlc-spdd.mdc`,
  installed to `.cursor/rules/`) giving Cursor the same whole-ecosystem grounding
  as Copilot's `copilot-instructions.md` and Claude's `CLAUDE.md`
- Whole-ecosystem grounding norm enforced in CI: `validate-command-adapters.sh`
  asserts every assistant's always-on grounding file covers Planning + SPDD + SDLC
- Adapter install/upgrade regression harness (`tests/test-adapter-install.sh`) and
  `test-adapter-install` CI workflow proving Cursor/Copilot are not regressed,
  no-flag defaults remain backward compatible, and existing `CLAUDE.md` content
  is preserved on upgrade
- Initial repository structure per STARTER-SPEC.md
- REASONS Canvas templates (feature, bugfix, refactor, spike)
- Eight Cursor command templates for SDLC-SPDD lifecycle
- Shell scripts: init, install commands, create feature, validate canvas, detect stack, sync context
- Stack rules for Java/Spring Boot, Gradle, Maven, Kubernetes, Tekton, Python, Node, Docker
- Agent overlays, playbooks, memory, and harness files
- Spring Boot order API example workflow
- Tekton pipeline demo layout
- GitHub issue and pull request templates
- GitHub Actions workflow for canvas validation
- Project documentation under `docs/`
