# REASONS Canvas: SPIKE-004-academic-contribution-bar — Academic contribution bar

## Metadata

- Work ID: SPIKE-004-academic-contribution-bar
- Work Type: Spike
- Status: In Progress
- Readiness: Ready For Coding
- Created: 2026-09-06
- Updated: 2026-09-06
- Owner: Cursor Agent
- Milestone: milestone-2
- Target Project: sdlc-spdd-orchestrator
- Stack: Markdown contracts, Python engine, shell CLI, three assistant adapters
- Beck stage: make it right (research argument / observability)
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/SPIKE-004-academic-contribution-bar.md`
- Analysis: `sdlc-spdd/spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`
- Task list: `sdlc-spdd/spdd/tasks/milestone-2-academic-hardening.md`
- Related PR: https://github.com/jmjava/sdlc-spdd-orchestrator/pull/219
- Skills: (none requested)

## R - Requirements

### User Goal

Turn the journal-style review into a **governed program plan** (this canvas) and **start iterating** on that plan — first P0 work is DOC-001 (research questions and constructs) — without pretending engine hardening is in scope for this spike.

### Business / Product Goal

Raise sdlc-spdd-orchestrator from hobby/engineering research to a **claim-safe** empirical SE / AI-assisted-process contribution. Product tracks (ADF, Vue3) continue in parallel; they are not the research object.

### Problem (from analysis)

The artifact over-claims. README says unstructured chat produces drift and SDLC-SPDD “fixes that.” A referee would reject: no RQs, no related-work delta, evaluation of the CLI not the method, and “governance” implemented as heading/regex/file-existence proxies.

### Acceptance Criteria

- [x] Journal analysis exists at `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`
- [x] Milestone 2 definition, `_milestone.yml`, Linked Work, and per-ID requirements
- [x] Iteration task list at `spdd/tasks/milestone-2-academic-hardening.md`
- [x] ROADMAP names Milestone 2 and P0/P1/P2 Work IDs
- [x] This canvas is the program plan: contribution sentence, sequence, dependencies, per-ID deliverables, stop rules
- [x] Architect pass sets Readiness and records risks/tests
- [x] DOC-001 is unblocked (requirement ACs for this spike checked; pointer/claim handoff documented)

### Definition of done (this spike)

The spike is **complete** when the program plan is in this canvas, architect-ready, and DOC-001 can start without inventing sequence or claims. The spike is **not** complete when FEAT-014+ ship.

### Non-Goals

- Implementing P1/P2 engine features (FEAT-014–017, REF-001) under this Work ID
- Writing the paper
- Running a user study (TEST-002)
- Changing engine/runtime behavior
- Upstream PRs to `embabel/guide` (forbidden)

### Assumptions

- Target venues: TSE/TOSEM/EMSE (long), ICSE SEIP, ICSE NIER / AIware / LLM4Code (near-term).
- Contribution is a **process model + observability + evidence**, not a new LLM or compiled multi-agent runtime.
- Child Work IDs each get their own analysis → canvas → one-operation coding loop.
- SPIKE-004 may remain claimed until T04; then claim DOC-001.

### Open Questions (resolved in this plan)

| Question | Decision |
|----------|----------|
| Is the spike the whole milestone? | No. Spike = review + plan + unblock P0. Children own delivery. |
| Can P1 coding start in parallel with P0 docs? | **No.** Freeze RQs (DOC-001) and related work (DOC-002) first. |
| May DOC-002 overlap DOC-001? | Yes, after DOC-001 has a frozen RQ *draft* (even if canvas not Complete). |
| What is the system under test for later eval? | Named in REF-001; until then, **Python `gate_check` + prompt adapters** are the method description, shell is compatibility. |

## E - Entities

### Domain entities (research object)

| Entity | Meaning |
|--------|---------|
| **Claim** | A public sentence (README, compliance, paper) that must be either measured or hedged |
| **Research question (RQ)** | Numbered question with independent/dependent constructs |
| **Construct** | Named concept with definition, measure, instrument, proxy weakness |
| **Instrument** | File, command, or protocol step that produces a measure |
| **Baseline condition** | Unstructured chat / canvas-only / lifecycle-only / full SDLC-SPDD |
| **Gold task** | Task with source + canvas + expected operations for TEST-002 |
| **Process-compliant session** | Required artifacts present **and** semantically adequate (DOC-001 will define “adequate”) |
| **Scope deviation** | Operation implemented off-canvas, or canvas requirement unimplemented |

### Program entities (Work IDs)

| ID | Role |
|----|------|
| SPIKE-004 | This plan + review |
| DOC-001 | Freeze RQs + constructs |
| DOC-002 | Related-work / novelty matrix |
| TEST-001 | Evaluation protocol (no data collection) |
| FEAT-014 | Semantic canvas validation |
| FEAT-015 | First-class metrics |
| FEAT-016 | Intent↔code + review quality |
| DOC-003 | Threats to validity + replication |
| FEAT-017 | Retrieval as IR |
| TEST-002 | One behavioral eval slice |
| CHORE-003 | Dogfood ledger survives archive |
| REF-001 | Single gate semantics |

### Inputs

- SPIKE-004 analysis (referee comments M1–M7)
- Current code: `workflow.py` `gate_check`, `phases.py`, `lessons_ledger.py`, `validate-reasons-canvas.sh`, `TESTING.md`
- Public claims: README “fixes that” / canvas “governs”

### Outputs (this spike)

- This canvas
- Updated requirement ACs
- Handoff to DOC-001

### External systems

- GitHub PR #219 (this program)
- Optional Guide DICE — **not** required; not a contribution until FEAT-017
- Jira/GitHub issues — optional tracker, not the research object

## A - Approach

### Proposed approach

1. **Plan the program in this canvas** (sequence, dependencies, deliverables, stop rules) so later agents do not re-litigate the referee report.
2. **Iterate one child Work ID at a time**, P0 → P1 → P2.
3. **Change public language** as soon as DOC-001’s claims table exists (hedge “fixes/governs” until TEST-002 has numbers).
4. **Harden instruments only after constructs freeze** so FEAT-014–017 implement DOC-001 measures, not new proxies.

### Program sequence (do not skip)

```text
SPIKE-004 (review + this plan)
    → DOC-001 (RQs + constructs)     P0
    → DOC-002 (related work)         P0  [may start after DOC-001 RQ draft]
    → TEST-001 (eval protocol)       P0  [needs DOC-001 + DOC-002]
         → FEAT-014 (semantic canvas)     P1  [needs DOC-001]
         → FEAT-015 (metrics)             P1  [needs DOC-001]
              → FEAT-016 (traceability)   P1  [needs FEAT-014]
              → DOC-003 (replication)     P1  [needs TEST-001 + FEAT-015]
         → FEAT-017 (retrieval IR)        P2  [needs DOC-001]
         → TEST-002 (behavior slice)      P2  [needs TEST-001 + FEAT-016]
    CHORE-003, REF-001                  P2  [may parallel after P0 freeze]
```

### Per-ID deliverable (what “done” means)

| Work ID | Deliverable a referee can open |
|---------|--------------------------------|
| DOC-001 | `sdlc-spdd/docs/research/research-questions-and-constructs.md` — RQs, construct table, claims-allowed table, README rewrite guidance |
| DOC-002 | Related-work matrix + one-sentence novelty claim |
| TEST-001 | Protocol: tasks, gold files, raters, metrics, stop rules, nondeterminism plan |
| FEAT-014 | Validator + `gate_check(code)` use structured readiness; headings-only canvas fails |
| FEAT-015 | Queryable metrics (not only session.body prose) + one query per assigned construct |
| FEAT-016 | Empty review ≠ safeguards pass; advertised gates match enforced gates or are labeled advisory |
| DOC-003 | Threats-to-validity + replication checklist |
| FEAT-017 | Written retrieve algorithm + precision@k fixture; DICE language conditional |
| TEST-002 | Gold task with **real source**; method vs unstructured log; n and model version beside any number |
| CHORE-003 | Policy + non-empty dogfood ledger or documented exception + CI |
| REF-001 | Named SUT; one `gate_check` semantics |

### Alternatives considered

1. **Implement FEAT-014 first** (harden grep) — rejected. Hardening the wrong proxy does not answer M1.
2. **Write the paper now** — rejected. No constructs, no protocol, no evidence.
3. **One mega Work ID for all of Milestone 2** — rejected. Violates one-Work-ID / one-operation norms; unreviewable diffs.
4. **Workshop-only path (skip TSE-grade eval)** — deferred as a *venue* choice, not a license to skip DOC-001. Even NIER needs RQs and limitations.

### Trade-offs

- **Speed vs claim-safety:** P0 docs delay engine work; they prevent a year of measuring the wrong thing.
- **Python vs shell SUT:** Naming Python `gate_check` as the research semantics (REF-001) leaves shell as compatibility until proven equal.
- **Small n in TEST-002:** One gold task is not a journal result; it is a *slice* that proves the protocol runs. DOC-003 must say so.

### Risks

- Child IDs expand into product work (ADF/Vue3) and lose the research object.
- DOC-001 invents constructs that no instrument can ever collect.
- Dual-engine drift continues while REF-001 waits (confound for TEST-002).
- Empty `lessons.jsonl` remains (CHORE-003) and referees treat dogfood as theater.

### Failure modes

- Shipping FEAT-014 without DOC-001 → new grep rules, same over-claim.
- Marking SPIKE-004 Complete while this canvas is missing → plan lives only in chat.
- Claiming “Ready For Coding” on child IDs that change engine before P0 freeze.

### Stop rules

- **Stop P1 coding** if DOC-001 construct table is not merged.
- **Stop claiming causal language** in README until TEST-002 records a comparison (DOC-001 rewrite guidance).
- **Stop DICE-as-contribution** language until FEAT-017 or SPIKE-001 resumes with metrics.

## S - Structure

### Files (this spike)

| Path | Action |
|------|--------|
| `sdlc-spdd/spdd/canvas/SPIKE-004-academic-contribution-bar.md` | Add (this file) |
| `sdlc-spdd/requirements/milestones/milestone-2/SPIKE-004-academic-contribution-bar.md` | Update ACs / status |
| `sdlc-spdd/spdd/tasks/milestone-2-academic-hardening.md` | Point at this canvas as the plan |
| `sdlc-spdd/spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md` | No rewrite of referee findings; Next → canvas |

### Files (first iteration — DOC-001, separate Work ID)

| Path | Action |
|------|--------|
| `sdlc-spdd/spdd/analysis/DOC-001-research-questions-and-constructs-analysis.md` | Add |
| `sdlc-spdd/spdd/canvas/DOC-001-research-questions-and-constructs.md` | Add |
| `sdlc-spdd/docs/research/research-questions-and-constructs.md` | Add (T01 of DOC-001) |
| `docs/research/README.md` | Link the RQ doc |
| `sdlc-spdd/docs/research/` | Create if missing |

### Boundaries

- **This spike** writes planning contracts only (canvas, requirement, task-list pointer).
- **DOC-001** owns the RQ document. Do not write that file under SPIKE-004 operations except as a *handoff*.
- **Engine** (`engine/src/sdlc_engine/**`) is out of scope until P1 Work IDs.

### Test structure (this spike)

- `./scripts/validate-reasons-canvas.sh sdlc-spdd/spdd/canvas/SPIKE-004-academic-contribution-bar.md`
- `./scripts/validate-requirements-format.sh --target sdlc-spdd`
- No pytest: no runtime change

### Test structure (program)

- P1: unit tests for validators/gates/metrics (FEAT-014–016)
- P2: IR fixture (FEAT-017); recorded assistant run (TEST-002); ledger CI (CHORE-003)

## O - Operations

### T01 — Journal review and Milestone 2 backlog

- Status: Complete
- Description: Referee analysis, milestone-2 requirements, task list, ROADMAP pointer, PR #219
- Files: `spdd/analysis/SPIKE-004-…-analysis.md`, `requirements/milestones/milestone-2/**`, `spdd/tasks/milestone-2-academic-hardening.md`, `ROADMAP.md`
- Tests: `validate-requirements-format.sh --target sdlc-spdd`
- Validation: PR #219

### T02 — Write this REASONS canvas as the program plan

- Status: Complete
- Description: Encode contribution sentence, sequence, dependencies, per-ID deliverables, stop rules, spike vs child boundary
- Files: `spdd/canvas/SPIKE-004-academic-contribution-bar.md`
- Tests: `validate-reasons-canvas.sh` on this file
- Validation: all required REASONS sections present; program sequence matches milestone-2

### T03 — Architect harden

- Status: Complete
- Description: Confirm entities/approach/operations; set Readiness Ready For Coding; record architecture notes and risks
- Files: this canvas (Architecture Notes, Readiness)
- Tests: `sdlc.sh gate --phase architect` then `--phase code` (code gate requires Ready For Coding)
- Validation: no missing REASONS sections; child IDs not listed as this spike’s coding tasks

### T04 — Unblock DOC-001 and start iteration

- Status: Complete
- Description: Check remaining spike ACs; update requirement status; claim DOC-001; produce DOC-001 analysis + canvas; implement **DOC-001 T01 only** (RQ + constructs + claims table document). Do not implement DOC-001 T02+ or any P1 engine work.
- Files: SPIKE-004 requirement; DOC-001 analysis/canvas; `sdlc-spdd/docs/research/research-questions-and-constructs.md`
- Tests: validate both canvases; requirements format
- Validation: DOC-001 T01 file exists with numbered RQs, construct table (definition/measure/instrument/proxy weakness), claims-allowed table

## N - Norms

### General

- One Work ID in the pointer while coding; SPIKE-004 T04 explicitly includes a claim switch to DOC-001
- One approved operation per coding session **per Work ID** (DOC-001 T01 only in T04)
- Behavior/requirement changes update the canvas before “code”
- Never hand-edit `spdd/memory/lessons.jsonl`; use capture → accept
- Never PR to `embabel/guide`

### Research program

- Every new claim maps to a construct or is hedged
- Child canvases must cite DOC-001 construct IDs when they add instruments
- Beck stage stays **make it right** until TEST-002; prompt optimization is out of this milestone

### Documentation

- Academic notes live under `sdlc-spdd/docs/research/` and/or `docs/research/` with an index that does not confuse Jira ADF notes with the research program

## S - Safeguards

- Do not modify `engine/src/sdlc_engine/**` under SPIKE-004
- Do not start FEAT-014–017 coding before DOC-001 construct table is merged
- Do not restore causal README language (“fixes”, unqualified “governs”) without TEST-002 evidence
- Do not treat Guide/Neo4j unavailability as a failure of this spike
- Do not invent FEAT/SPIKE IDs beyond the Milestone 2 table
- `--force` / skip on gates is a human decision, never used to skip P0
- Fork-only Guide; no Embabel upstream framing in DOC-002 or elsewhere

## Review Checklist

- [x] Requirements for T01 captured in analysis + milestone
- [x] Entities cover claims, RQs, constructs, Work IDs
- [x] Approach sequences P0 → P1 → P2 with stop rules
- [x] Operations split spike work vs child Work IDs
- [x] Safeguards block premature engine work
- [x] T04 DOC-001 T01 delivered
- [x] Tests: canvas validator on this file

## Sync Notes

2026-09-06 — Canvas created from analysis; T01 already shipped on PR #219. T02/T03 completed in the same planning session as canvas authoring (plan + architect). T04 starts DOC-001.

## Final Status

- Status: Complete
- Completed Date: 2026-09-06
- PR: https://github.com/jmjava/sdlc-spdd-orchestrator/pull/219
- Follow-Up: DOC-001 T02 (README hedges), then DOC-002

## Architecture Notes

- Readiness: Ready For Coding (T04 is documentation/planning under DOC-001, not engine code)
- Required tests: canvas + requirements validators only for remaining spike work
- Quality gates: requirement, canvas, architect, Ready For Coding before T04’s DOC-001 implementation
- Risk: T04 spans two Work IDs by design (handoff). After claim DOC-001, do not implement SPIKE-004 engine-like work
- Decision: Python `WorkflowEngine.gate_check` is the *described* process semantics until REF-001; adapters are the *described* assistant method; shell is compatibility
- Decision: Contribution sentence (provisional, DOC-002 may tighten): *A repository-native process model for AI-assisted delivery that makes intent, process compliance, and context load observable and comparable, with evidence versus unstructured chat and versus parent methods used in isolation.*
