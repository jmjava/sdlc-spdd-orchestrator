# Analysis: DOC-001 — Research questions and operationalized constructs

## Metadata

- Work ID: DOC-001-research-questions-and-constructs
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/DOC-001-research-questions-and-constructs.md`
- Date: 2026-09-06
- Parent plan: `sdlc-spdd/spdd/canvas/SPIKE-004-academic-contribution-bar.md`
- Source analysis: `sdlc-spdd/spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md` (M1, proposed RQs)

## Scope Lock

### In Scope for This Work

- Freeze **3–5 numbered RQs**, each naming independent and dependent constructs
- A **construct table**: definition, measure, instrument (file/command today vs target Work ID), proxy weakness
- A **claims allowed today vs after Milestone 2** table
- **Rewrite guidance** for README/compliance causal language (“fixes”, unqualified “governs”)
- Place the document at `sdlc-spdd/docs/research/research-questions-and-constructs.md` and index it from `docs/research/README.md`

### NOT in Scope (Deferred)

- Running the study — TEST-001 (protocol), TEST-002 (slice)
- Implementing validators / metrics schema / IR eval — FEAT-014, FEAT-015, FEAT-016, FEAT-017
- Related-work matrix and novelty sentence — DOC-002
- Threats-to-validity appendix — DOC-003 (will cite this construct table)
- README wording change itself may be T02 if kept separate from T01 freeze

### Reference Materials (Context Only, Not Deliverables)

- README “Why it exists” (claim language)
- `engine/src/sdlc_engine/workflow.py` `gate_check` / `sync`
- `scripts/validate-reasons-canvas.sh`
- `engine/src/sdlc_engine/lessons_ledger.py` `LEDGER_KINDS` / `records()`
- `scripts/capture-session-memory.sh` optional metric flags
- `TESTING.md` confidence stack
- SPIKE-004 proposed RQ1–RQ5

## Domain Keywords

- drift, scope deviation, governance, process compliance, construct, instrument, research question
- context budget, retrieval, decision memory, portability, adapter parity
- readiness, rework, review-result, baseline, unstructured chat

## Code Areas

- `sdlc-spdd/docs/research/` (deliverable home)
- `docs/research/` (orchestrator index)
- `README.md` (claim language — rewrite *guidance* in T01; optional apply in T02)
- Context-only: `engine/src/sdlc_engine/workflow.py`, `lessons_ledger.py`, `scripts/validate-reasons-canvas.sh`, `scripts/capture-session-memory.sh`

## Existing Concepts

- Implied claims in README/compliance, never written as RQs
- Capture flags `--readiness`, `--review-result`, `--rework`, `--context-files`, `--validate-cycles`, `--review-cycles` stored in **session body text**, not a `metric` kind (`LEDGER_KINDS` has no metric)
- Gate proxies: heading grep, `/ready for coding/i`, review-file existence
- Retrieve: exact keyword-list filter
- Adapter parity CI as a stand-in for “same method on three assistants”

## New Concepts

- Construct IDs (C-DRIFT, C-COMPLY, C-CONTEXT, C-MEMORY, C-PORT) as the vocabulary later features must implement
- “Claims allowed today” as an explicit allow-list for public docs
- Instrument vs proxy: what we can collect *now* vs what P1 must build

## Strategic Direction

Start from SPIKE-004’s five draft RQs. Do not add a sixth RQ. Bind each RQ to constructs that **this repo can eventually instrument** (gates, diffs, capture, retrieve, adapter runs) — not to unmeasurable “developer delight.”

Provisional contribution sentence (DOC-002 may tighten, must not contradict):

> A repository-native process model for AI-assisted delivery that makes intent, process compliance, and context load observable and comparable, with evidence versus unstructured chat and versus parent methods used in isolation.

Trade-off: keep constructs coarse enough for a small TEST-002 slice, precise enough that FEAT-014–017 have acceptance criteria.

## Risks and Gaps

- If constructs require human raters only, P1 engine work has nothing to automate — mitigate by pairing each construct with **one machine proxy** and **one human remainder**.
- DOC-002 novelty sentence might want a different DV — mitigate: RQs are frozen for Milestone 2 unless `/sdlc-spdd-prompt-update` on DOC-001.
- README still says “fixes that” until T02; T01 must include rewrite guidance so the gap is explicit.

## Recommendation

Proceed to canvas. T01 = freeze the research document. T02 = apply README/compliance hedges from that document’s rewrite guidance. Do not implement FEAT-014 in this Work ID.
