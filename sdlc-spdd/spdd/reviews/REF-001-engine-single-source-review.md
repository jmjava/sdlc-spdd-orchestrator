# Review: REF-001-engine-single-source

**Work ID:** REF-001-engine-single-source  
**Date:** 2026-09-06  
**Result:** Approved With Notes  

## Summary

T01 names Python `WorkflowEngine.gate_check` as the Milestone 2 SUT, defaults `SDLC_ENGINE` to `auto`, and makes workflow `gate` delegate to Python whenever it is importable. `SDLC_GATE_ENGINE=shell` is an explicit non-SUT fallback for the bash workflow harness.

## Proof

| Check | Result |
|-------|--------|
| Headings-only + substring “ready for coding” | Python `gate_check(code)` fails |
| Same fixture via `SDLC_ENGINE=shell` workflow | fails when engine is importable |
| `SDLC_GATE_ENGINE=shell` on the same fixture | still passes (labeled non-SUT fallback) |
| SUT doc / ROADMAP / TESTING | name Python |

## Findings

1. **Note:** Install and upgrade remain shell. That is out of scope.
2. **Safeguard:** `SDLC_GATE_ENGINE=shell` is not an evaluation condition.
3. **Note:** Default `auto` routes `archive` to Python. `ArchiveService` now moves contracts under `project.home` (storage v3 `sdlc-spdd/`), matching the live-consumer install layout.

## Required changes

None.

## Recommendation

Mark Complete. Milestone 2 P2 backlog is done; journal n remains TEST-001’s stop rule.
