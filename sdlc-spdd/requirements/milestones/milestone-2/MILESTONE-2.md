# Milestone 2 — Academic contribution bar

## Goal

Make SDLC-SPDD *claim-safe* as a research project: stated research questions, a related-work position, operationalized constructs (drift, governance, context, memory), and an evaluation protocol a journal referee would accept — then harden the implementation so those constructs are observable.

**Academic review of this repo** (DOC-001 §1) is the **intent/advice stores** and a **retrievability** bar. Replication of that bar is **Python 3 only**; live Guide+Neo4j stays **optional**. This review's **scope removed** reduced-drift (RQ1) and retrieve-usefulness (RQ4). Deterministic Intent Folding (`embabel-dif`) is later / other-repo; this milestone is foundational to that attach and does not include it.

This is **make it right** for the research argument. It is not prompt optimization and not a new assistant runtime.

Analysis that opened this milestone: `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Outcome (definition of done for the milestone)

- Public claims ("governs", "fixes drift") are either measured or rewritten.
- A referee can find: RQs, construct table, related-work delta, evaluation protocol, threats to validity, replication notes.
- Gates, canvas checks, metrics, and retrieval match the paper-shaped claims (or the claims match the weaker code).
- At least one executed empirical slice exists (even small), not only CLI tests.

## Scope

P0 — desk-reject without these:

- [x] SPIKE-004-academic-contribution-bar — journal-style review + this backlog (analysis in this PR)
- [x] DOC-001-research-questions-and-constructs — freeze RQs and measures (T01 spec + T02 README hedges)
- [x] DOC-002-related-work-map — literature/positioning matrix
- [x] TEST-001-evaluation-protocol — comparative protocol before collecting data

P1 — major-revision items (observability of the method):

- [x] FEAT-014-semantic-canvas-validation — contracts beyond heading grep
- [x] FEAT-015-first-class-metrics — metrics as queryable data, not session-body prose
- [x] FEAT-016-intent-code-traceability — "code maps to ops" and review quality as checks
- [x] DOC-003-replication-package — threats to validity + frozen eval notes

P2 — strengthen the contribution:

- [x] FEAT-017-retrieval-ir-eval — retrieval as IR (rank, qrels, baselines)
- [x] TEST-002-assistant-behavior-eval — three-assistant *behavior*, not adapter text parity
- [x] CHORE-003-dogfood-ledger — committed lessons survive archive so dogfood memory exists
- [x] REF-001-engine-single-source — one gate semantics (shell vs Python) as a validity fix

Claim test after DOC-001 T03 freeze (the retrievability bar needs a named suite):

- [x] TEST-003-cretrieve-roundtrip — persist→retrieve same id on ledger, SQLite, mocked Guide

## Linked Work

| Work ID | Canvas | Requirement | Status | Notes |
|---------|--------|-------------|--------|-------|
| SPIKE-004-academic-contribution-bar | [canvas](../../../spdd/canvas/SPIKE-004-academic-contribution-bar.md) | [requirement](SPIKE-004-academic-contribution-bar.md) | Complete (T01–T04) | Program plan |
| DOC-001-research-questions-and-constructs | [canvas](../../../spdd/canvas/DOC-001-research-questions-and-constructs.md) | [requirement](DOC-001-research-questions-and-constructs.md) | Complete | T01 spec + T02 hedges + T03 review-goal freeze (stores + retrievability; DIF later) |
| DOC-002-related-work-map | [canvas](../../../spdd/canvas/DOC-002-related-work-map.md) | [requirement](DOC-002-related-work-map.md) | Complete | Matrix + structured tests; PR #221 |
| TEST-001-evaluation-protocol | [canvas](../../../spdd/canvas/TEST-001-evaluation-protocol.md) | [requirement](TEST-001-evaluation-protocol.md) | Complete | Protocol + live tests; PR #222 |
| FEAT-014-semantic-canvas-validation | [canvas](../../../spdd/canvas/FEAT-014-semantic-canvas-validation.md) | [requirement](FEAT-014-semantic-canvas-validation.md) | Complete | Structured readiness + semantic minima |
| FEAT-015-first-class-metrics | [canvas](../../../spdd/canvas/FEAT-015-first-class-metrics.md) | [requirement](FEAT-015-first-class-metrics.md) | Complete | Structured `metrics` object + `context metrics` CLI |
| FEAT-016-intent-code-traceability | [canvas](../../../spdd/canvas/FEAT-016-intent-code-traceability.md) | [requirement](FEAT-016-intent-code-traceability.md) | Complete | Empty review ≠ safeguards; Files: mapping; advisory labels |
| DOC-003-replication-package | [canvas](../../../spdd/canvas/DOC-003-replication-package.md) | [requirement](DOC-003-replication-package.md) | Complete | Threats + freeze checklist; live-consumer is not method evidence |
| FEAT-017-retrieval-ir-eval | [canvas](../../../spdd/canvas/FEAT-017-retrieval-ir-eval.md) | [requirement](FEAT-017-retrieval-ir-eval.md) | Complete | Lexical title-body vs keyword-list; DICE unmeasured |
| TEST-002-assistant-behavior-eval | [canvas](../../../spdd/canvas/TEST-002-assistant-behavior-eval.md) | [requirement](TEST-002-assistant-behavior-eval.md) | Complete (protocol incomplete; n=1) | Hello gold + farewell AC; C-DRIFT 0 vs 0.333; C-PORT not reported |
| CHORE-003-dogfood-ledger | [canvas](../../../spdd/canvas/CHORE-003-dogfood-ledger.md) | [requirement](CHORE-003-dogfood-ledger.md) | Complete | Seeded decision/pitfall/pattern; archive never truncates ledger |
| REF-001-engine-single-source | [canvas](../../../spdd/canvas/REF-001-engine-single-source.md) | [requirement](REF-001-engine-single-source.md) | Complete | Python `gate_check` is SUT; `SDLC_GATE_ENGINE=shell` is not an eval condition |
| TEST-003-cretrieve-roundtrip | [canvas](../../../spdd/canvas/TEST-003-cretrieve-roundtrip.md) | [requirement](TEST-003-cretrieve-roundtrip.md) | Complete | Named C-RETRIEVE suite; mocked Guide in default CI; live Neo4j extra |

## Iteration order

Do **not** start P1 coding until DOC-001 and DOC-002 exist. Otherwise we will harden the wrong proxies.

1. DOC-001 → DOC-002 (can overlap once RQ draft from SPIKE-004 is accepted or amended)
2. TEST-001 (protocol uses the construct table)
3. FEAT-014, FEAT-016 (make compliance observable)
4. FEAT-015 (make outcomes queryable)
5. DOC-003 (write threats using the real instruments)
6. FEAT-017, TEST-002 (empirical slices)
7. CHORE-003, REF-001 (method integrity; can be parallel once P0 is frozen)
8. TEST-003 (named C-RETRIEVE suite after the stores+retrievability freeze)

## SDLC-SPDD Flow

For each work item:

1. `/sdlc-spdd-analysis` on its requirement (SPIKE-004 analysis already covers the program; per-item analysis is scoped to that ID).
2. `/sdlc-spdd-plan` → canvas.
3. `/sdlc-spdd-architect` until Ready For Coding.
4. One operation at a time with `/sdlc-spdd-code`.
5. Review, capture, accept, retro.

## Session Updates

2026-09-06 — TEST-003 named C-RETRIEVE suite (ledger + SQLite + mocked Guide). Live Guide+Neo4j e2e already exists (`test-guide-stack-experimental`).
2026-09-06 — DOC-001 T03: academic review goal frozen as stores + retrievability (ledger + Guide); reduced-drift and `embabel-dif` out of scope.
2026-09-06 — REF-001 names Python `gate_check` as the SUT; default `SDLC_ENGINE=auto`. Milestone 2 P2 complete.
2026-09-06 — CHORE-003 seeded the dogfood ledger; archive never truncates it. Next: REF-001.
2026-09-06 — TEST-002 first slice recorded (hello gold, n=1, protocol incomplete). Next: CHORE-003, then REF-001.
2026-09-06 — SPIKE-004 analysis recorded. Milestone 2 opened. Local session `LOCAL-001-academic-hardening-review`.
