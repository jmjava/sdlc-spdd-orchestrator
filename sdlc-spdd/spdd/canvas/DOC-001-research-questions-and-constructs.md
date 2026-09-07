# REASONS Canvas: DOC-001-research-questions-and-constructs — RQs and constructs

## Metadata

- Work ID: DOC-001-research-questions-and-constructs
- Work Type: Documentation
- Status: Complete
- Readiness: Reviewed
- Created: 2026-09-06
- Updated: 2026-09-07
- Prompt-update: T05 three storage modes (2026-09-07); T04 Python 3-only replication first-class (2026-09-07, superseded); T03 academic-review-goal freeze (2026-09-06)
- Milestone: milestone-2
- Depends on: SPIKE-004-academic-contribution-bar
- Blocks: TEST-001, FEAT-014, FEAT-015
- Related: DOC-002
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/DOC-001-research-questions-and-constructs.md`
- Analysis: `sdlc-spdd/spdd/analysis/DOC-001-research-questions-and-constructs-analysis.md`
- Parent plan: `sdlc-spdd/spdd/canvas/SPIKE-004-academic-contribution-bar.md`
- Beck stage: make it right (research argument)

## R - Requirements

### User Goal

Freeze research questions and operationalized constructs so later Milestone 2 work implements **instruments**, not new vibes. **T03:** freeze what “academic review” of *this* repo actually is.

### Business / Product Goal

Make public claims allow-listed. Stop README causal language until evidence exists.

Academic review of `sdlc-spdd-orchestrator` is a **methods/tools artifact review**: git-backed **intent** (REASONS canvas) and **advice** in **three storage modes** (committed `lessons.jsonl` ledger, **SQLite** index, **Guide/Neo4j** graph), with a **retrievability** bar — stored records can be read back from all three. Live Guide+Neo4j is **required evidence** for the graph mode; mocked HTTP is not the graph-store proof. This review's **scope removed** reduced-**drift** (RQ1) and retrieve-**usefulness** (RQ4). Deterministic Intent Folding (`jmjava/embabel-dif`) is **out of scope** here and **later / other-repo**; this freeze is foundational to that attach and does not require it.

### Acceptance Criteria

- [x] RQs numbered; each names independent and dependent constructs
- [x] Every construct has: definition, measure, instrument, known proxy weakness
- [x] Claims-allowed-today vs after Milestone 2 table is committed
- [x] Rewrite guidance for README/compliance is in the same document (T01); applying README edits is T02
- [x] T03: spec §1 names the review object (stores), the retrievability bar (ledger + SQLite + Guide), pass/fail, venue band, and that reduced-drift + `embabel-dif` are not this review
- [x] T04: Python 3-only replication is a first-class freeze claim; live Guide+Neo4j stays optional
- [x] T05: three storage modes (ledger, SQLite, live Guide/Neo4j graph) all proven; live graph is required evidence

### Non-Goals

- Running the study
- Implementing validators
- Related-work matrix (DOC-002) as a new Work ID (T03 may sync DOC-002 novelty so it cannot contradict this freeze)
- Implementing or evaluating Deterministic Intent Folding / Embabel GOAP / a JVM fold
- Opening a new SPIKE for leftover eval; remaining empirical work stays on TEST-002

### Assumptions

- Five RQs from SPIKE-004 analysis, refined not replaced
- Construct IDs are stable names for FEAT-014–017 canvases to cite

## E - Entities

- Research question (RQ1–RQ5)
- Construct (C-DRIFT, C-COMPLY, C-CONTEXT, C-MEMORY, C-PORT)
- Instrument (current proxy vs target Work ID)
- Claim allow-list row
- Academic review goal (object, retrievability bar, later DIF pointer)
- C-RETRIEVE (supporting measure: stored record readable from ledger / SQLite / Guide)

### Files likely affected

- `sdlc-spdd/docs/research/research-questions-and-constructs.md` (add; T03 freeze)
- `docs/research/README.md` (index)
- `README.md` (T02 only)
- T03 consistency: `sdlc-spdd/docs/research/related-work-and-novelty.md`, `sdlc-spdd/docs/research/check_p0_artifacts.py`

## A - Approach

Write one canonical markdown spec. Machine proxies must be things this repo already has or P1 will add. Human remainders are explicit so TEST-001 can assign raters.

Do not expand to a sixth RQ. Do not implement FEAT-014 “to make the table look better.”

T03 does not add RQ6. It restates the contribution so academic review cannot be read as “prove we reduce drift” or “this is the DIF paper.” The in-scope empirical claim is **retrievability**: a stored lesson can be found again from the git ledger (`context retrieve`) and, when enabled, from the SQLite local index and the Guide working-store projection (`context parity`). That is not RQ4 usefulness. Sync DOC-002’s novelty preamble if it still treats “with evidence” as this review’s aim.

### Alternatives

- Put RQs only in the SPIKE canvas — rejected; children need a citable spec.
- Wait for DOC-002 — rejected; instruments would stay undefined.

### Risks

- Over-precise formulas that TEST-002 cannot collect
- Under-precise constructs that FEAT-014 can satisfy with more grep

## S - Structure

### Files to add

- `sdlc-spdd/docs/research/research-questions-and-constructs.md`

### Files to modify

- `docs/research/README.md`
- T02: `README.md`, maybe `sdlc-spdd/docs/spdd-compliance.md`
- T03: `sdlc-spdd/docs/research/related-work-and-novelty.md`, checker, CHANGELOG, milestone pointer

### Test structure

- Document completeness checklist in T01 (all RQ/construct/claim sections present)
- No pytest

## O - Operations

### T01 — Freeze RQ, construct, and claims-allowed spec

- Status: Complete
- Description: Commit `sdlc-spdd/docs/research/research-questions-and-constructs.md` with RQ1–RQ5 (IV/DV), construct table (definition, measure, current instrument, target instrument, proxy weakness), claims-allowed table, README rewrite guidance. Link from `docs/research/README.md`.
- Files: `sdlc-spdd/docs/research/research-questions-and-constructs.md`, `docs/research/README.md`
- Tests: section completeness vs this canvas ACs
- Validation: every construct has four fields; every RQ cites construct IDs

### T02 — Apply public-language hedges

- Status: Complete
- Description: Apply T01 rewrite guidance to README (and compliance if it repeats causal claims). Do not invent new product claims.
- Files: `README.md`, possibly `sdlc-spdd/docs/spdd-compliance.md`
- Tests: grep for “fixes that” should not remain as an unqualified causal claim
- Validation: claims-allowed table still matches README

### T03 — Freeze academic-review goal (stores, not drift; DIF later)

- Status: Complete
- Description: Prompt-update then edit the construct spec so academic review of this repo is the git-backed intent/advice stores (ledger + SQLite index + Guide projection) and a retrievability bar. Reduced-drift evidence is not the success criterion (RQ1 stays defined, not the pass bar). RQ4 usefulness stays unmeasured. Name `embabel-dif` as later/other-repo and out of scope, while stating this freeze is foundational to that attach. Tighten the claims-allowed table so “fixes drift” stays forbidden for this review even after a TEST-002 slice. Sync DOC-002 novelty/not-claiming so “with evidence” is not this review’s aim.
- Files: `sdlc-spdd/docs/research/research-questions-and-constructs.md`, `sdlc-spdd/docs/research/related-work-and-novelty.md`, `sdlc-spdd/docs/research/check_p0_artifacts.py`, `tests/research/test_p0_artifacts.py`, `docs/research/README.md`, CHANGELOG, milestone pointer
- Tests: `python3 -m unittest tests.research.test_p0_artifacts -v`; `./sdlc-spdd/docs/research/prove-p0.sh DOC-001`; `prove-p0.sh DOC-002`
- Validation: spec §1 present; contribution omits reduced-drift evidence; claims table keeps “fixes drift” as No after P2; retrievability named for ledger + SQLite + Guide; `embabel-dif` named as later/out of scope

### T04 — Python 3-only replication is first-class (live Guide optional)

- Status: Complete
- Description: Prompt-update then elevate “Python 3 only; live Guide+Neo4j stays optional” from a replication footnote into DOC-001 §1 (in-scope replication claim, pass bar item 5, contribution sentence, claims-allowed Yes/No rows). Sync DOC-002 novelty/not-claiming and DOC-003 §0. Lock with P0 checkers + TEST-003 assertions so dropping the claim fails CI.
- Files: `sdlc-spdd/docs/research/research-questions-and-constructs.md`, `sdlc-spdd/docs/research/related-work-and-novelty.md`, `sdlc-spdd/docs/research/threats-to-validity-and-replication.md`, `sdlc-spdd/docs/research/check_p0_artifacts.py`, `tests/research/test_p0_artifacts.py`, `tests/research/test_cretrieve.py`
- Tests: `python3 -m unittest tests.research.test_p0_artifacts tests.research.test_cretrieve -v`; `./sdlc-spdd/docs/research/prove-academic-review.sh`
- Validation: spec §1 names Python 3-only replication; claims table says live Guide+Neo4j is not required; checker fails if those tokens are stripped

### T05 — Three storage modes proven (live graph required)

- Status: Complete
- Description: Prompt-update then reverse T04’s “live Guide optional / requiring JVM fails the bar.” The freeze is **three storage modes**: git ledger, SQLite, Guide/Neo4j graph. Mocked HTTP is the Guide client, not the graph. Live `test_guide_projection_roundtrip` + `test_context_store_guide_live` are required evidence. Hermetic `prove-academic-review.sh` remains modes 1–2 + client.
- Files: DOC-001 spec, DOC-002, DOC-003, `check_p0_artifacts.py`, TEST-003 suite/docs, `test_context_store_guide_live.py`, `test-guide-stack-experimental.yml`
- Tests: `python3 -m unittest tests.research.test_p0_artifacts tests.research.test_cretrieve -v`; live graph via `SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh`
- Validation: spec §1 names three storage modes; claims table says live Guide+Neo4j is required for the graph mode; checker fails if live graph is framed as optional

## N - Norms

- Cite construct IDs (`C-DRIFT`, …) in later canvases
- Prompt-update this canvas if RQs, the contribution sentence, or the academic-review object change
- One operation per session

## S - Safeguards

- Do not modify engine code
- Do not add RQ6
- Do not restore “fixes drift” as a result or as this review’s pass bar
- Do not treat `embabel-dif` / Deterministic Intent Folding as a Milestone 2 finding
- No Embabel upstream framing (`embabel/guide` and `embabel-dif` are not upstream PRs from this freeze)
- T01 must not edit README (that is T02)
- T03 must not implement a fold, start a JVM, or open a new SPIKE

## Review Checklist

- [x] T01 document exists
- [x] Five RQs with construct IDs
- [x] Five constructs with four fields each
- [x] Claims table
- [x] Rewrite guidance present
- [x] T02 not mixed into T01
- [x] T03 spec §1 freeze landed; DOC-002 novelty does not contradict it
- [x] T04 Python 3-only replication is first-class; live Guide+Neo4j optional
- [x] T05 three storage modes; live Guide+Neo4j required for the graph mode

## Sync Notes

Created 2026-09-06 from SPIKE-004 T04 handoff.

2026-09-06 — T03 prompt-update: academic review of this repo is the stores (intent + advice ledger + SQLite index + Guide projection) with a retrievability bar. Source: stakeholder (firm the review goal; DIF out of scope; stored info should be retrievable; ledger + Guide store; do not forget SQLite).

2026-09-07 — Stakeholder: **Python 3 only** replication is a first-class claim; live Guide+Neo4j stays optional (not the pass bar).

2026-09-07 — Stakeholder correction (T05): the graph store is the point; **three storage modes** must be proven. Live Guide+Neo4j is required evidence. T04 optional-graph language is superseded.

## Final Status

- Readiness: Reviewed
- Status: Complete

## Architecture Notes

- Readiness: Reviewed
- T01–T03 documentation only (no engine)
- Risk: `docs/three-part-operating-path.md` still says “governs execution” (out of T02 file list)
- Decision: contribution omits “with evidence that the hybrid reduces drift”; this review's **scope removed** drift and usefulness
- Decision: in-scope empirical claim is retrievability (ledger `context retrieve` + SQLite and Guide `context parity` when enabled)
- Decision: `embabel-dif` is later/other-repo; optional present-or-skip attach is not this review’s object
- Decision (T04, superseded by T05): hermetic Python 3 suite is ledger+SQLite+client, not the whole freeze
- Decision (T05): **three storage modes** (ledger, SQLite, Guide/Neo4j) must each persist→read; live graph is required evidence; mocked HTTP is not the graph
- Next: none for DOC-001. Drift and usefulness stay removed from this review.
