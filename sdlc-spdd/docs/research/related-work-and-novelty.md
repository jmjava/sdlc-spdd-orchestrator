# Related-work and novelty matrix

**Work ID:** DOC-002-related-work-map  
**Status:** Frozen for Milestone 2 unless `/sdlc-spdd-prompt-update` on the DOC-002 canvas  
**Date:** 2026-09-06  
**Construct spec:** [DOC-001](research-questions-and-constructs.md)  
**Parent plan:** [SPIKE-004 canvas](../../spdd/canvas/SPIKE-004-academic-contribution-bar.md)  
**Referee source:** [SPIKE-004 analysis](../../spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md) (M2)

This is a **positioning document**, not a complete literature review and not an evaluation result.

---

## How to read this

Each row is a system a 2026 referee will ask about. Columns are DOC-001 constructs, not marketing adjectives:

| Column | Meaning |
|--------|---------|
| Intent observability (C-DRIFT) | Is there a versioned intent artifact against which scope deviation can be scored? |
| Process compliance (C-COMPLY) | Are required process artifacts checkable as existence *and* (if claimed) semantic adequacy? |
| Context load (C-CONTEXT) | Is what the process caused to be loaded measurable, or is context an unbounded chat/agent window? |
| Evidence / eval | What has actually been measured: the *tool*, a coding-agent *benchmark*, or the *delivery method*? |
| Delta vs SDLC-SPDD | The difference we would defend in rebuttal — not “we are better,” but “we are not the same object.” |

`jmjava/guide` is **fork-only**. This matrix does not propose, imply, or depend on an Embabel upstream merge.

---

## Novelty

DOC-001’s provisional contribution sentence may be tightened here. It must not be contradicted.

The academic-review novelty is **observability of stores plus retrievability** (intent canvas; advice ledger as system of record; SQLite local index and Guide working-store as regenerable projections). This review's **scope removed** reduced-drift (RQ1) and retrieve-usefulness (RQ4). `embabel-dif` is **later / other-repo**; this matrix does not treat DIF attach as a finding. Optional present-or-skip attach is not a result of this review.

> SDLC-SPDD is a **repository-native process model** for AI-assisted delivery that hybridizes a versioned REASONS intent contract with assistant-lifecycle governance so that intent (C-DRIFT), process compliance (C-COMPLY), and context load (C-CONTEXT) are **observable and comparable** across process conditions.

That sentence is the claim we would defend in rebuttal. It does **not** assert that the hybrid has already reduced drift. Do **not** append “with evidence that…” as this review’s aim.

Parents (Fowler SPDD / OpenSPDD, SDLC Agents) supply the canvas and the phase lifecycle. Spec-driven kits (Spec Kit, OpenSpec, BMAD) supply neighboring “spec as artifact” practice. Coding agents and multi-agent runtimes supply a different research object (agent competence, not process observability). Native assistant memory and classical process/rationale methods supply further neighbors. The delta is the **hybrid + named constructs + retrievable stores** (ledger + SQLite index + optional Guide projection), not a new model family and not a fold.

What **is** claimed today: the hybrid is **implemented** and **observable** (FEAT-014 canvas semantics, FEAT-016 review minima, FEAT-015 metrics, FEAT-017 lexical retrieve as IR, REF-001 Python `gate_check` as named SUT, CHORE-003 seeded ledger). See DOC-001 §1 and §5.

## Claim × system matrix

| System | Intent observability (C-DRIFT) | Process compliance (C-COMPLY) | Context load (C-CONTEXT) | Evidence / eval | Delta vs SDLC-SPDD |
|--------|--------------------------------|-------------------------------|--------------------------|-----------------|---------------------|
| GitHub Spec Kit | Constitution + specify/plan/tasks files; drift vs spec is informal unless a team adds review | Slash-command phases; presence of spec artifacts, not semantic REASONS minima or existence-vs-semantic rates | No per-phase retrieval budget or lesson ledger; context is whatever the agent opened | Tooling adoption and workflow write-ups; not a method vs unstructured-chat C-DRIFT study | Spec-as-artifact without a REASONS contract, SDLC-SPDD phase gates, construct IDs, or a claims-allowed freeze |
| OpenSpec | Brownfield *delta* specs in git; intent is the change, archived into a growing source of truth | `openspec` validate traces tasks to specs; still spec/task alignment, not canvas-section semantics | No ledger retrieve or phase context budget; caller-supplied context | Tooling; change-management metaphor | Delta-spec change control, not a hybrid SPDD+SDLC lifecycle with C-COMPLY existence vs semantic split |
| OpenSPDD | Implements Fowler’s REASONS canvas via `/spdd-*` CLI (analysis → canvas → generate → sync) | Command workflow around the canvas; machine checks are the OpenSPDD CLI, not this repo’s `gate_check` + adapters | Unspecified as a measurable load/relevance construct | Method essay + CLI; example apps, not RQ-keyed comparison | Direct parent *implementation* of SPDD; missing SDLC Agents phases, multi-assistant adapters, and C-* instruments |
| BMAD | PRD / architecture / story artifacts produced by named personas | Simulated agile team and adversarial review; process is agent orchestration, not file-backed canvas gates | Large always-on persona briefs; load is not a first-class C-CONTEXT measure | Method/framework; persona pipeline quality, not C-DRIFT vs chat | Agents-as-roles orchestration rather than a versioned REASONS contract plus optional CLI gates |
| Fowler SPDD | REASONS canvas *is* the intent contract (Requirements…Safeguards) | Human-reviewed structured prompt; essay does not define existence-vs-semantic ProcessComplianceRate | Context is “load the canvas,” not a retrieval budget with relevance | Method essay (Fowler / Thoughtworks) | Parent of the canvas; no SDLC phase machine, no assistant adapters, no frozen C-DRIFT/C-COMPLY instruments |
| SDLC Agents | Planning artifacts and phase briefs as intent-adjacent files | Slash-command lifecycle (analysis→…→sync); progressive disclosure as process, not C-COMPLY rates | Progressive disclosure / hot brief is the context idea; not precision@k | GitHub method + command files | Parent of the phase lifecycle; no REASONS canvas, no construct table, no claims-allowed freeze |
| Aider | Chat / issue text plus git diffs; no durable REASONS-style contract | Git-native agent loop; no delivery-process compliance rate | Repo map as retrieval heuristic, not per-phase budget | Product use and coding-agent reports | A coding agent that edits git, not a governed delivery method with comparable C-* constructs |
| SWE-agent | GitHub issue as the task spec | Agent-computer interface actions; not process-artifact gates | ACI observes tools/files; load is agent infrastructure, not C-CONTEXT policy | SWE-bench (agent solves issues) | Benchmarked coding agent; research object is issue-to-PR competence, not process observability |
| OpenHands | Task prompt / issue into an agent runtime | Runtime event logs; not REASONS + phase-file compliance | Workspace/runtime context | SWE-bench and product evals | Agent *platform*, not a repository-native process model with frozen RQs |
| AutoGen/CrewAI | Goals and roles in an agent graph | Runtime orchestration and message passing | Token windows / conversation state | Framework papers and demos | Compiled/runtime multi-agent systems; opposite of git-Markdown process contracts |
| Cursor/Copilot/Claude native memory | Rules, memories, `CLAUDE.md` / custom instructions as local intent | Product-enforced, not method-level C-COMPLY with existence vs semantic rates | Memories + open tabs; not a comparable ContextLoad instrument | Product behavior | Assistant product features, not a comparative method with C-DRIFT vs unstructured chat |
| gIBIS/QOC | Design rationale (issues, positions, arguments / questions-options-criteria) | Argumentation structure, not AI-session phase gates | IBIS graphs as memory of *design questions*, not assistant context load | Classics (1980s–1990s) | Rationale capture without AI-SE session gates, adapters, or a chat baseline |
| ISO 12207/SPEM/CMMI | Organizational lifecycle and process models | Auditable process capability / defined processes | Not an assistant-session context construct | Standards and appraisals | Heavyweight org process; not assistant-session native and not C-DRIFT vs chat |

---

## Cluster notes (why the rows are not duplicates)

**Spec-driven kits (Spec Kit, OpenSpec, BMAD).** These treat specification files as first-class input to coding agents. They are the closest *product* neighbors. None freeze C-DRIFT / C-COMPLY / C-CONTEXT as research constructs or compare full method vs unstructured chat vs parent-method isolation. BMAD is an orchestration of personas; Spec Kit is a constitution-plus-phases toolkit; OpenSpec is brownfield delta-spec change control. SDLC-SPDD’s spec object is the REASONS canvas plus SDLC phase artifacts, with optional CLI `gate_check`.

**Parents (Fowler SPDD, OpenSPDD, SDLC Agents).** Provenance, not novelty by themselves. OpenSPDD is the CLI that operationalizes Fowler’s essay. SDLC Agents is the lifecycle/progressive-disclosure parent. Claiming “we implemented both” without a delta vs each parent used *in isolation* is what DOC-001 RQ1 and TEST-001 must later test — it is not shown here.

**Coding agents (Aider, SWE-agent, OpenHands).** Evaluate whether an agent can finish a coding task. SDLC-SPDD evaluates whether a *process* makes intent, compliance, and context load observable. SWE-bench numbers are not C-DRIFT.

**Multi-agent runtimes (AutoGen/CrewAI).** Programmable agent graphs. SDLC-SPDD is not a compiled multi-agent runtime.

**Native assistant memory.** Useful operator practice. It is not a versioned REASONS contract and does not yield PortabilityGap under adapter-spec parity (DOC-001 H5).

**Classics (gIBIS/QOC, ISO 12207/SPEM/CMMI).** Design rationale and process modeling are ancestors of “make the process inspectable.” They are not AI-assistant session methods and do not define the C-* instruments.

---

## What we are not claiming

- A new **LLM** or decoding algorithm.
- A new **RAG** or GraphRAG theory (retrieve today is an exact keyword-list filter; DICE remains conditional on FEAT-017).
- A compiled **multi-agent** runtime (AutoGen/CrewAI class).
- Reduced-**drift** (RQ1) — this review's **scope removed** it. Do not say the hybrid **fixes drift**.
- Retrieve-**usefulness** (RQ4) — this review's **scope removed** it. Retrievability of stored records (C-RETRIEVE) is the in-scope claim.
- Deterministic Intent Folding / `embabel-dif` as a result of this orchestrator review. Optional attach is present-or-skip. That pairing is later / other-repo; this work is foundational to it.
- An upstream contribution to Embabel. Guide remains **fork-only**.

---

## Use in TEST-001

TEST-001 must pick baselines that make this matrix falsifiable: unstructured chat; canvas-only (Fowler-like); lifecycle-only (SDLC Agents-like); full SDLC-SPDD. That is how “versus parent methods used in isolation” becomes a procedure rather than a slogan.
