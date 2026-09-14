# Sync: REF-003-retire-bash-workflow-dual-path

**Work ID:** REF-003-retire-bash-workflow-dual-path
**Date:** 2026-09-14
**Readiness After Sync:** Complete
**Status After Sync:** Complete
**Pull Request:** https://github.com/jmjava/sdlc-spdd-orchestrator/pull/321

## What Changed

- The bash workflow twin — `sdlc-workflow.sh`, `sdlc-team-registry.sh`, and
  `sdlc-pointer.sh` — is deleted from `templates/agent-context/` and
  `sdlc-spdd/scripts/` (3,100 shipped LOC; 6,200 with dogfood copies).
- `scripts/sdlc.sh` and its dogfood copy are thin dispatchers that require
  Python 3.12 and an importable `sdlc_engine`. `SDLC_ENGINE=shell` and
  `SDLC_GATE_ENGINE=shell` exit non-zero; `SDLC_ENGINE=python` is a no-op.
- `start-agent-session.sh`, `capture-session-memory.sh`, and
  `accept-lessons.sh` call the engine through `SDLC_PY` and no longer source a
  twin or shell out to bare `python3` for engine behavior.
- `sdlc-engine shell` resolves retained utilities in both orchestrator
  `scripts/` and installed `sdlc-spdd/scripts/` layouts.
- Init and upgrade stop shipping the twins, upgrade backs up and deletes the
  exact retired paths, and install verification asserts their absence.
- `test-sdlc-workflow.sh`, `test-sdlc-pointer.sh`, and `test-archive-work.sh`
  are replaced by `engine/tests_unit/` coverage; their CI workflows are gone.
- Operator, testing, engine, template, and research docs describe one
  mandatory Python engine.

## What Drifted

- Extending `cmd_shell` for installed targets raised its CCN from 4 to 6 and
  failed the diff complexity gate, which rejects any rise in a touched
  function.
- Three migrated harnesses pinned `${REPO_ROOT}/.venv/bin/python`. CI installs
  the engine into the job interpreter and never creates a repo venv, so
  `test-sdlc-workflow` failed on a path that did not exist.
- `resolve_engine_python` reported that failure as `is 3.` because its
  here-string parse could not distinguish an unrunnable interpreter from an
  empty version string.
- T05 was scoped to operator docs, but the research docs and
  `tests/research/test_ref001_sut.py` still pinned `SDLC_ENGINE=auto` and a
  live `SDLC_GATE_ENGINE=shell` fallback.
- AC5 was unmet at review time: two retained utilities still shaped engine
  records with bare `python3` heredocs.
- The requirement's harness count of 30 predates REF-002 and the canvas's 28
  predates this Work ID's deletions.

## What Was Reconciled

- `_shell_script_candidates` and `_resolve_shell_script` carry the bridge
  logic, returning `cmd_shell` below its base complexity.
- `tests/lib/engine-python.sh` is the single harness interpreter resolver;
  `test-integration-merge.sh` and `tests/live-consumer/lib.sh` use it instead
  of their own copies of the same fallback chain.
- `resolve_engine_python` reports an unrunnable interpreter distinctly and
  prints the full `major.minor` for a wrong version, with coverage in
  `tests/test-scripts-lib.sh`.
- Research docs and the SUT test state the rejection contract.
- The three remaining `python3` heredocs use the already-resolved `SDLC_PY`.
- The canvas records all three harness counts (30 → 28 → 25) and the
  requirement explains the reconciliation.
- Requirement, canvas, Milestone 3, and `ROADMAP.md` mark REF-003 Complete.

## Review and Validation

- Review result: **Approved With Notes**.
- PR CI: **25/25 successful checks** at `cb19e84`.
- Suite 1 unit 288 passed; Suite 2 integration 151 passed at 91.58% coverage;
  research 87 passed.
- Shell harnesses 24/25 passed; `test-guide-stack-live.sh` skipped (live Guide
  + Neo4j stack).
- Live-consumer shell matrix: 113 passed, 0 failed, 1 skipped.
- Installed-target smoke: 45/45 install checks, plus claim, pointer, next,
  status, gate, capture refusal, capture with receipt, accept, and the shell
  bridge.
- ShellCheck `-S error` and `bash -n` clean; complexity gate PASS; canvas,
  requirements, adapter, and diagram validators PASS.

## Dependencies

- Depends on REF-002-purge-pre-v3-compat (Complete).
- Unblocks REF-010-pythonize-session-and-capture: the retained session and
  capture utilities are now thin Python-engine clients, which is the starting
  point REF-010 assumed.
- REF-004, REF-005, and REF-006 no longer need shell parity.

## Accepted Lessons

- `session:REF-003-retire-bash-workflow-dual-path:tests/test-:capture`
- `decision:REF-003-retire-bash-workflow-dual-path:tests/test-:capture`
- `pitfall:REF-003-retire-bash-workflow-dual-path:tests/test-:capture`
- `pattern:REF-003-retire-bash-workflow-dual-path:tests/test-:capture`

## Evidence

- `/opt/cursor/artifacts/ref003-acceptance.log`
- `/opt/cursor/artifacts/ref003-full-validation.log`
- `/opt/cursor/artifacts/ref003-installed-target-smoke.log`
- `/opt/cursor/artifacts/live-consumer-matrix.log`
