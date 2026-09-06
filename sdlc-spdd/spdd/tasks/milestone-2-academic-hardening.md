# Milestone 2 task list — Academic contribution bar

Iteration list for raising `sdlc-spdd-orchestrator` from hobby/engineering research to a claim-safe academic contribution.

**Do not start P1 coding until P0 docs exist.** Hardening the wrong proxy (heading grep, file existence, exact keywords) will not satisfy a referee.

Full review: [`../analysis/SPIKE-004-academic-contribution-bar-analysis.md`](../analysis/SPIKE-004-academic-contribution-bar-analysis.md)  
**Program plan (canvas):** [`../canvas/SPIKE-004-academic-contribution-bar.md`](../canvas/SPIKE-004-academic-contribution-bar.md)  
Milestone: [`../../requirements/milestones/milestone-2/MILESTONE-2.md`](../../requirements/milestones/milestone-2/MILESTONE-2.md)

## How to use this list

One Work ID at a time. For each row: analysis → plan/canvas → architect → code one operation → review.

Beck stage for the whole list: **make it right** (research argument and observability), not make it fast.

## P0 — desk-reject without these

| # | Work ID | Task | Done when |
|---|---------|------|-----------|
| 0 | `SPIKE-004-academic-contribution-bar` | Journal review + program canvas + unblock P0 | Analysis + milestone + [canvas](../canvas/SPIKE-004-academic-contribution-bar.md) |
| 1 | `DOC-001-research-questions-and-constructs` | Freeze RQs; operationalize drift, governance, context, memory, portability | Construct table with measure + instrument + proxy weakness |
| 2 | `DOC-002-related-work-map` | Position vs Fowler SPDD, SDLC Agents, Spec Kit, OpenSpec, BMAD, coding agents, process-modeling | One-sentence novelty claim + matrix |
| 3 | `TEST-001-evaluation-protocol` | Comparative protocol (unstructured vs canvas-only vs full method) | Protocol maps every RQ; no study data required yet |

## P1 — make "governed" observable

| # | Work ID | Task | Done when |
|---|---------|------|-----------|
| 4 | `FEAT-014-semantic-canvas-validation` | Stop treating `##` headings and `/ready for coding/i` as the contract | Headings-only canvas fails; readiness is a structured field |
| 5 | `FEAT-015-first-class-metrics` | Restore FEAT-004 intent: metrics queryable, not session-body prose | CLI query per construct; round-trip tests |
| 6 | `FEAT-016-intent-code-traceability` | Enforce or relabel `code_maps_to_ops` / safeguards; empty review ≠ pass | `phases.py` and `gate_check` agree; empty review fails |
| 7 | `DOC-003-replication-package` | Threats to validity + freeze versions | Referee can replay commands and gold tasks |

## P2 — evidence and method integrity

| # | Work ID | Task | Done when |
|---|---------|------|-----------|
| 8 | `FEAT-017-retrieval-ir-eval` | Retrieval as IR, or drop DICE-as-contribution language | Algorithm written; precision@k fixture; DICE claims conditional |
| 9 | `TEST-002-assistant-behavior-eval` | One gold task, method vs unstructured, ≥1 assistant run recorded | Example has real source; n and model version written beside numbers |
| 10 | `CHORE-003-dogfood-ledger` | Archive must not leave `lessons.jsonl` empty | Policy + non-empty dogfood ledger or documented exception + CI |
| 11 | `REF-001-engine-single-source` | One gate semantics (shell default vs Python) | Named system-under-test for Milestone 2 eval |

## Referee findings → Work IDs

| Reviewer comment | Work ID |
|------------------|---------|
| M1 Problem not operationalized; "fixes drift" over-claimed | DOC-001 |
| M2 Related work is parent citations, not a position | DOC-002 |
| M3 Evaluation tests the tool, not the method | TEST-001, TEST-002 |
| M4 Governance is heading/regex/file-existence | FEAT-014, FEAT-016 |
| M5 Dual engine confounds "the method" | REF-001 |
| M6 Retrieve is exact keyword filter; DICE unmeasured | FEAT-017 |
| M7 Stale ROADMAP/design-decisions; empty dogfood ledger | CHORE-003 (+ hygiene in each ID) |
| Metrics kind dropped; `spdd --metrics` deferred | FEAT-015 |
| No threats to validity / replication pack | DOC-003 |

## First next action

P0 desk-reject items are **Complete** (DOC-001, DOC-002, TEST-001). FEAT-014 is the first P1 item (semantic canvas / C-COMPLY for `code`). After FEAT-014 merges, next is FEAT-016 (traceability) then FEAT-015 (metrics) per Milestone 2 order.
