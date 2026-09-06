# Analysis: DOC-002 — Related-work and novelty matrix

## Metadata

- Work ID: DOC-002-related-work-map
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/DOC-002-related-work-map.md`
- Date: 2026-09-06
- Parent plan: `sdlc-spdd/spdd/canvas/SPIKE-004-academic-contribution-bar.md`
- Frozen constructs: `sdlc-spdd/docs/research/research-questions-and-constructs.md` (DOC-001)
- Source analysis: `sdlc-spdd/spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md` (M2)

## Scope Lock

### In Scope for This Work

- One related-work matrix: claim × system × delta, covering Spec Kit, OpenSpec, OpenSPDD, BMAD, Fowler SPDD, SDLC Agents, Aider, SWE-agent, OpenHands, AutoGen/CrewAI, Cursor/Copilot/Claude native memory, gIBIS/QOC, ISO 12207/SPEM/CMMI
- One-sentence novelty claim consistent with DOC-001 (tighten wording; do not contradict; do not treat “with evidence” as a finding)
- Explicit not-claiming list (new LLM, new RAG theory, compiled multi-agent runtime)
- Guide remains fork-only; no Embabel-upstream framing

### NOT in Scope (Deferred)

- Complete literature review of all AI-SE papers
- Running TEST-001/TEST-002
- Engine/runtime features (FEAT-014+)
- Upstream PRs to embabel/guide

### Reference Materials (Context Only, Not Deliverables)

- DOC-001 contribution sentence and claims-allowed table
- SPIKE-004 M2 cluster table
- Fowler SPDD essay; SDLC Agents repo; public Spec Kit / OpenSpec / BMAD write-ups
- SWE-agent / OpenHands / Aider as coding-agent research objects

## Domain Keywords

- related work, novelty, REASONS, spec-driven, process model, construct, C-DRIFT, C-COMPLY, C-CONTEXT
- OpenSPDD, Spec Kit, OpenSpec, BMAD, SWE-bench, gIBIS, QOC, ISO 12207, SPEM, CMMI

## Code Areas

- `sdlc-spdd/docs/research/related-work-and-novelty.md` (deliverable)
- `sdlc-spdd/docs/research/check_p0_artifacts.py` (structured checker)
- `tests/research/` (negative fixtures + live checks)
- `docs/research/README.md` (index)

## Existing Concepts

- Parents cited as provenance (Fowler + SDLC Agents) without a delta matrix
- DOC-001 freeze: repository-native process model; intent / compliance / context load observable and comparable
- Guide fork-only rule

## New Concepts

- Claim × system matrix with DOC-001 construct columns
- Novelty sentence that drops the “with evidence” clause (remains an aim until TEST-002)
- Structured checker that rejects token-only stubs

## Risks

- Treating OpenSPDD and Fowler SPDD as unrelated (they are method vs CLI)
- Claiming superiority instead of object-difference
- Accidental Embabel-upstream language
- Grep-only proof that a stub would pass

## Recommendation

Write the matrix at `sdlc-spdd/docs/research/related-work-and-novelty.md`. Tests parse the table; they must fail on token stubs. Index from `docs/research/README.md`.
