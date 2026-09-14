# REASONS Canvas: REF-003-retire-bash-workflow-dual-path — Python-only lifecycle flow

## Metadata

- Work ID: REF-003-retire-bash-workflow-dual-path
- Work Type: Refactor
- Status: In Progress
- Readiness: Ready For Coding
- Created: 2026-09-14
- Updated: 2026-09-14
- Milestone: milestone-3
- Depends on: REF-002-purge-pre-v3-compat (Complete)
- Blocks: REF-010-pythonize-session-and-capture
- Related: REF-001-engine-single-source
- Requirement: `sdlc-spdd/requirements/milestones/milestone-3/REF-003-retire-bash-workflow-dual-path.md`
- Analysis: `sdlc-spdd/spdd/analysis/REF-003-retire-bash-workflow-dual-path-analysis.md`
- Beck stage: make it right

## R - Requirements

### User Goal

Operate one lifecycle implementation. Workflow, gate, pointer, and team
registry behavior comes only from Python `sdlc_engine`; bash remains only for
install/upgrade packaging and retained session/capture utilities.

### Acceptance Criteria

- [ ] `templates/agent-context/` and `sdlc-spdd/scripts/` contain no
  `sdlc-workflow.sh`, `sdlc-team-registry.sh`, or `sdlc-pointer.sh`.
- [ ] `SDLC_ENGINE=shell ./scripts/sdlc.sh next` exits non-zero with a clear
  Python-only message.
- [ ] `SDLC_GATE_ENGINE=shell ./scripts/sdlc.sh gate ...` exits non-zero with
  the same single-engine contract.
- [ ] Missing/unusable Python 3.12 or `sdlc_engine` exits non-zero with the
  install/setup hint; no bash fallback runs.
- [ ] Gate and utility engine calls resolve `SDLC_PY`; no touched path invokes
  bare `python3` for engine behavior.
- [ ] `cmd_shell` bridges both orchestrator `scripts/` and installed
  `sdlc-spdd/scripts/`.
- [ ] Fresh installs and upgrades omit/remove the three retired files, and
  install verification asserts their absence.
- [ ] All current 28 shell harnesses pass against the Python-only dispatcher
  or are replaced by equivalent pytest coverage.
- [ ] Shipped duplicate implementation decreases by at least 3,000 LOC
  (measured template deletion: 3,100 LOC).
- [ ] Current README, testing, engine, template, and shipped documentation
  describe one mandatory Python engine.

### Non-Goals

- Pythonizing session/capture scripts (REF-010)
- Removing install/upgrade shell
- Typed/locked storage records (REF-006)
- Splitting issue synchronization (REF-011)
- Embabel Guide work or upstream contributions
- Rewriting historical records that accurately describe the former twin

## E - Entities

- `scripts/sdlc.sh`: mandatory-engine dispatcher
- `resolve_engine_python` / `SDLC_PY`: sole interpreter resolution path
- `sdlc_engine` CLI: lifecycle parser and behavior
- `cmd_shell`: retained utility bridge
- `start-agent-session.sh`, `capture-session-memory.sh`,
  `accept-lessons.sh`: shell utilities, not lifecycle implementations
- Retired files: `sdlc-workflow.sh`, `sdlc-team-registry.sh`,
  `sdlc-pointer.sh`
- Installed home: `<target>/sdlc-spdd/scripts/`
- Current shell harness inventory: 28 `tests/test-*.sh` files

## A - Approach

Remove runtime dependencies before deleting files. First teach the Python shell
bridge to find installed utilities. Then make `sdlc.sh` require Python and
rewire retained utilities to use the Python CLI. After focused tests show no
dependency on the twins, update packaging and delete exact framework-owned
paths. Finally migrate affected harnesses, synchronize docs, and run the full
matrix.

`SDLC_ENGINE=python` remains accepted as a compatibility no-op because it
already means the only supported engine. `SDLC_ENGINE=shell` and any
`SDLC_GATE_ENGINE` override are rejected; neither can select behavior.

## S - Structure

### Files to add

- `sdlc-spdd/spdd/reviews/REF-003-retire-bash-workflow-dual-path-review.md`
- `sdlc-spdd/spdd/sync/REF-003-retire-bash-workflow-dual-path-sync.md`
- Focused pytest coverage in an existing or new
  `engine/tests_unit/test_cli_shell.py`

### Files to delete

- `templates/agent-context/sdlc-workflow.sh`
- `templates/agent-context/sdlc-team-registry.sh`
- `templates/agent-context/sdlc-pointer.sh`
- `sdlc-spdd/scripts/sdlc-workflow.sh`
- `sdlc-spdd/scripts/sdlc-team-registry.sh`
- `sdlc-spdd/scripts/sdlc-pointer.sh`
- Obsolete shell harnesses/workflows only when equivalent pytest coverage is
  committed in the same operation

### Files to modify

- Dispatcher/bridge: `scripts/sdlc.sh`, `sdlc-spdd/scripts/sdlc.sh`,
  `engine/src/sdlc_engine/cli_commands.py`
- Utilities: `scripts/start-agent-session.sh`,
  `scripts/capture-session-memory.sh`, `scripts/accept-lessons.sh` and
  installed dogfood copies
- Packaging: `scripts/init-project.sh`, `scripts/upgrade-project.sh`,
  `scripts/verify-project-install.sh` and installed dogfood copies
- Tests/workflows: affected `engine/tests_*`, `tests/test-*.sh`,
  `tests/live-consumer/`, `.github/workflows/`
- Docs: `README.md`, `TESTING.md`, `docs/engine-v2.md`, relevant
  `sdlc-spdd/docs/` mirrors, `templates/agent-context/README.md`,
  `CHANGELOG.md`
- Lifecycle artifacts: requirement, milestone, roadmap, review, sync, registry,
  and accepted lessons

## O - Operations

### T01 - Bridge retained shell utilities in source and installed targets

- Status: Complete
- Description: Extend Python `cmd_shell` resolution to executable utilities in
  orchestrator `scripts/` or installed `<target>/sdlc-spdd/scripts/`, with
  stable missing-script, argument-forwarding, and working-directory behavior.
- Files: `engine/src/sdlc_engine/cli_commands.py`,
  `engine/tests_unit/test_cli_shell.py` (or nearest existing CLI test module)
- Tests: focused pytest for source, installed, missing, and forwarding cases
- Validation: an installed-target fixture executes a helper through
  `sdlc-engine shell`

### T02 - Make the dispatcher and retained utilities Python-only

- Status: Pending
- Description: Remove workflow probing/fallback from both `sdlc.sh` copies;
  reject shell engine overrides; require resolved Python 3.12; route
  start/capture/complete/accept through Python or its shell bridge; stop
  retained utilities from sourcing the retired scripts or invoking bare
  Python for engine behavior.
- Files: `scripts/sdlc.sh`, `sdlc-spdd/scripts/sdlc.sh`,
  `scripts/start-agent-session.sh`, `sdlc-spdd/scripts/start-agent-session.sh`,
  `scripts/capture-session-memory.sh`,
  `sdlc-spdd/scripts/capture-session-memory.sh`,
  `scripts/accept-lessons.sh`, `sdlc-spdd/scripts/accept-lessons.sh`,
  dispatcher/session/capture tests
- Tests: `tests/test-sdlc-engine-shim.sh`, focused session/capture/accept pytest
- Validation: default/`python` execute one engine; shell/gate overrides fail;
  no retained utility requires a twin

### T03 - Stop shipping and delete the bash twin

- Status: Pending
- Description: Remove twin installation from init/upgrade, delete exact
  retired paths during upgrade, require their absence in install verification,
  and delete template plus dogfood copies.
- Files: `scripts/init-project.sh`, `scripts/upgrade-project.sh`,
  `scripts/verify-project-install.sh`, dogfood copies,
  `templates/agent-context/sdlc-{workflow,team-registry,pointer}.sh`,
  `sdlc-spdd/scripts/sdlc-{workflow,team-registry,pointer}.sh`,
  installer tests
- Tests: installer unit/integration, init, upgrade, verify-install,
  live-consumer install scenario
- Validation: fresh and upgraded fixtures contain `sdlc.sh`, omit all three
  twins, and report at least 3,000 shipped LOC removed

### T04 - Migrate the shell-harness and CI matrix

- Status: Pending
- Description: Rewrite affected workflow, pointer, gate, archive, integration,
  and live-consumer harnesses to exercise Python-only behavior; remove only
  tests/workflows made obsolete by equivalent pytest coverage. Reconcile the
  requirement's pre-REF-002 count of 30 with the current inventory of 28.
- Files: affected `tests/test-*.sh`, `tests/live-consumer/`,
  `tests/research/test_ref001_sut.py`, `.github/workflows/`
- Tests: all remaining `tests/test-*.sh`, engine unit and integration suites
- Validation: no active test sets `SDLC_ENGINE=shell` or
  `SDLC_GATE_ENGINE=shell` except explicit rejection assertions

### T05 - Synchronize the one-engine documentation contract

- Status: Pending
- Description: Update active operator, testing, engine, template, and shipped
  docs to state the mandatory Python contract; preserve historical audit
  records; update changelog and REF-003 lifecycle status.
- Files: `README.md`, `TESTING.md`, `docs/engine-v2.md`,
  `templates/agent-context/README.md`, relevant `sdlc-spdd/docs/` mirrors,
  `CHANGELOG.md`, this canvas and requirement
- Tests: doc mirror checks, command-spec generation, active-reference grep
- Validation: no current operator instruction offers shell engine selection

### T06 - Full validation, review, retro, and sync

- Status: Pending
- Description: Run the complete local unit/integration/shell/live-consumer and
  documentation validation matrix, perform scope/review checks, capture and
  accept lessons, synchronize milestone/roadmap/dependencies, and release the
  Work ID.
- Files: review, sync, canvas, requirement, milestone, roadmap, dependency
  requirements, registry, lessons, derived context index
- Tests: full local CI runner plus operation diff-scope and lifecycle gates
- Validation: all checks terminal and green; no pending REF-003 lifecycle
  artifact

## N - Norms

- One approved operation per commit
- Delete duplicate behavior; do not preserve untested safety fallbacks
- Python 3.12 resolution always uses the shared resolver
- Bash may package or host a retained utility, but may not decide lifecycle
  semantics
- Current documentation changes with behavior; historical audit evidence stays
- Never contribute Guide work upstream to `embabel/guide`

## S - Safeguards

- Exact-path deletion only under framework-owned template/install locations
- Upgrade never deletes unrelated user scripts
- Missing Python fails loudly with setup guidance
- Shell-engine requests fail; they never silently switch behavior
- Retained utility output and persisted records receive focused regression
  coverage before twin deletion
- Installed-target smoke proves source-checkout assumptions did not leak
- Full current harness inventory is measured and run, not inferred from stale
  requirement prose

## Test Plan

- Automated: focused bridge/dispatcher/unit tests, retained utility tests,
  installer/integration/live-consumer tests, all current shell harnesses,
  ShellCheck, docs/spec generation, and full engine unit/integration suites.
- Terminal smoke: initialize and verify a temporary target; run claim, next,
  status, gate, pointer, capture, and accept; confirm retired files are absent
  and unsupported engine overrides fail.
- Evidence: save final full-suite and smoke output under
  `/opt/cursor/artifacts/`.

## Review Checklist

- [x] T01 bridge is covered for source and installed targets
- [ ] T02 dispatcher has one mandatory engine
- [ ] T02 retained utilities have no twin dependency
- [ ] T03 twin files are absent from source and installs
- [ ] T03 shipped LOC reduction is at least 3,000
- [ ] T04 current shell/pytest matrix is green
- [ ] T05 current docs state one engine
- [ ] T06 review, retro, sync, and dependency docs are complete
- [ ] Full validation suite is green

## Sync Notes

Begins from PR #320 merge commit `5ea5c8f`; all four post-merge `main`
workflows passed before REF-003 coding began.

## Final Status

- Readiness: Ready For Coding
- Status: In Progress
