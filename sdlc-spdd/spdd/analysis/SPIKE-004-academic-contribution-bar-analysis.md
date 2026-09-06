# Analysis: SPIKE-004 — Academic contribution bar

**Work ID:** SPIKE-004-academic-contribution-bar  
**Date:** 2026-09-06  
**Phase:** analysis (journal-style review of the research project, not a code-area scan)  
**Inferred from:** no active Work ID; local session `LOCAL-001-academic-hardening-review`  
**Scope lock:** Review `sdlc-spdd-orchestrator` as a *research project* a journal referee would assess. Produce a hardening task list. Do not change application/engine behavior in this spike.

---

## Scope Lock-In

### In scope

- Treat the orchestrator itself (process model, engine, adapters, tests, docs, examples) as the submitted artifact.
- Judge it the way TSE / TOSEM / Empirical Software Engineering / ICSE SEIP referees judge a methods-or-tools paper: problem, related work, novelty, construct validity, evaluation, reproducibility, threats to validity, claims vs evidence.
- Ground every major comment in files that exist in this checkout.
- Turn reviewer demands into a Milestone 2 Work ID list the project can iterate.

### Not in scope

- Implementing any hardening Work ID in this spike.
- Writing the paper.
- Reviewing `jmjava/guide` or other sibling repos except as related context.
- Product work already in flight (ADF templates, Vue3 console) except where it confounds the research claim.

### Deferred

- Per-Work-ID canvases for follow-on items (`/sdlc-spdd-plan` after this analysis).
- Running a user study or ablation in this session.

---

## Recommendation (as a referee)

**Major revision as a research contribution. Acceptable as an open-source engineering artifact.**

This repository is a serious, dogfooded operating model for AI-assisted delivery. It is **not yet an academic contribution**, because it does not state research questions, does not position itself against the literature, and evaluates the *tool* (CLI, adapters, install, gates-as-files) rather than the *method* (does governed SPDD+SDLC change what agents and humans actually do?).

A journal would not reject for lack of ambition. It would reject for **claims that outrun evidence**.

| Venue | Likely outcome today | What would move it |
|-------|----------------------|--------------------|
| TSE / TOSEM / EMSE | Reject or major revision | Operationalized constructs + comparative evaluation + threats to validity |
| ICSE/FSE Technical Track | Reject | Same, plus a crisp novelty claim vs Fowler SPDD and SDLC Agents |
| ICSE SEIP / Industry | Possible with case studies | Independent projects, protocol, measured outcomes — not only self-dogfood |
| ICSE NIER / AIware / LLM4Code workshop | Closest fit | Explicit RQs, related-work map, honest limitations, one small empirical slice |

Beck posture of this spike: **make it right** for the *research argument* (specify constructs, measurement, and evaluation). It is not prompt optimization ("make it fast") and not a new product capability ("make it work").

---

## What the artifact claims

The public claim (README) is that unstructured assistant chat produces **drift**, and SDLC-SPDD **fixes that** with three durable layers: Planning, SPDD (REASONS Canvas), SDLC (phases, briefs, memory). Assistants are not to invent a parallel process.

Implied scientific claims, reconstructed from docs (the project never writes them as RQs):

1. A version-controlled REASONS Canvas **governs** execution better than chat-only or prompt-file-only workflows.
2. A hybrid of Fowler SPDD + SDLC Agents is a **distinct, replicable method**, not just an installer for two existing ideas.
3. Progressive disclosure (fixed-size Tier 1 grounding + retrieved Tier 2) **scales** context as a repo grows.
4. File-backed gates make AI-assisted delivery **reviewable and non-bypassable** in the same sense as human process gates.
5. A lesson ledger is **decision memory** that improves later work (Fowler's cross-iteration asset accumulation).
6. Multi-assistant adapters with CI parity mean the **same method** runs on Cursor, Copilot, and Claude Code.

A referee's first job is: *which of these are defined, operationalized, and tested?* Today: **defined in prose, weakly operationalized, tested as engineering.**

---

## Strengths (what a referee should not dismiss)

1. **A real problem, stated in practitioner language.** Drift, lost decisions, and session-amnesia are widely reported in AI-assisted coding. The three-layer split (why / what / who-acts-when) is a clear conceptual model (`docs/three-part-operating-path.md`).

2. **Method is inspectable.** Contracts are Markdown in git. That is a reproducibility asset most agent runtimes lack. MIT license, install scripts, and CI validators exist.

3. **Some process is actually machine-checked**, not only documented. `WorkflowEngine.gate_check` refuses `plan` without analysis (unless skipped), refuses `code` unless the canvas text matches `ready for coding`, refuses `review`/`api-test` without ledger evidence, refuses `sync` without a retro-kind lesson (`engine/src/sdlc_engine/workflow.py`). Unit tests exist (`engine/tests_unit/test_workflow_gates.py`).

4. **Honest about nondeterminism.** `TESTING.md` calls slash-command runtime a "confidence stack," not 100% automation. That is the right epistemic stance; the paper would need to *design around* it, not hide it.

5. **Storage v3 is a coherent systems design.** Ledger-first persist, stage-then-accept, projections (SQLite, Guide) with a parity check is a clean architecture for "memory as a reviewed artifact."

6. **Engineering test mass is non-trivial.** ~63 engine modules, ~55 test modules, unit/integration/e2e split, live-consumer matrix, command-adapter parity CI. For a tools paper's *artifact appendix*, this is above hobby grade.

7. **The project dogfoods its own lifecycle** and archived Milestone 1 as complete. That is evidence of *use*, which SEIP cares about — it is not yet evidence of *effect*.

---

## Major comments (must fix to be a research contribution)

### M1. The problem is not operationalized; the solution is over-claimed

"Drift" is never given a measurable definition (scope expansion vs canvas, silent requirement change, forgotten decision, token-bloat, rework cycles, defect escape). README says the method "fixes that." No protocol, metric, or baseline is attached to that sentence.

**Referee ask:** Write 3–5 research questions and a construct table (name, definition, measure, instrument, failure mode). Do not claim "governs" or "fixes" until those measures exist.

### M2. Related work is citations of parents, not a literature position

The compliance story is: Fowler [SPDD](https://martinfowler.com/articles/structured-prompt-driven/) + [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents). That is provenance, not novelty.

A 2026 referee will ask what is new versus:

| Cluster | Examples a related-work section must handle |
|---------|-----------------------------------------------|
| Spec-driven / prompt-as-artifact | GitHub Spec Kit, OpenSpec, OpenSPDD, BMAD, Cursor skills/rules, Copilot custom instructions |
| Coding agents | SWE-agent, OpenHands, Aider, Devin, Claude Code memory, AutoGen, CrewAI, LangGraph |
| Process & method | Scrum/XP, ISO/IEC 12207, SPEM, process mining, CMMI, design rationale (gIBIS, QOC) |
| Knowledge / memory | organizational memory, PROV, RAG/GraphRAG, "memory for agents" papers |
| Empirical AI-SE | studies of Copilot/ChatGPT on quality, trust, review, and process deviation |

Without that map, the contribution collapses to: *we implemented Fowler+SDLC Agents as git templates plus a Python CLI.* That can be a good tool. It is not yet a paper.

**Referee ask:** One related-work matrix: claim × prior system × delta. State the delta in one sentence the authors would defend in rebuttal.

### M3. Evaluation tests the implementation, not the method

`TESTING.md` is an engineering confidence stack (adapter drift, side-effect scripts, optional manual chat smoke). That does **not** answer: *does using this method change outcomes vs unstructured chat?*

Observed evaluation gaps:

- No research questions, hypotheses, or analysis plan.
- No baseline (unstructured chat / canvas-only / lifecycle-only / this hybrid).
- No user study, no inter-rater protocol for canvas or review quality.
- Live consumer matrix is Cursor-oriented; Copilot/Claude "parity" is **text adapter** parity (`validate-command-adapters.sh`), not behavioral.
- The Spring Boot example has a canvas and a seven-line review; **no Java sources** in `examples/spring-boot-order-api/`. It cannot be a case study of intent-to-code alignment.
- FEAT-004/005 built capture flags; `LEDGER_KINDS` has no `metric`; ROADMAP still lists `spdd --metrics` as deferred. Measurement was started and then not treated as data.
- After Milestone 1 archive, this repo has **no committed `lessons.jsonl`**. The method's own decision memory is empty in the working tree — a dogfood hole a referee will notice.

**Referee ask:** A written evaluation protocol (even a small one): tasks, gold artifacts, independent raters, pre-registered metrics, threats to validity. Then one executed slice.

### M4. "Governance" has weak construct validity

The method's scientific object is *governed* AI delivery. In code, several gates are **existence and substring checks**, which do not measure governance:

| Claimed gate | What the code actually checks | File |
|--------------|-------------------------------|------|
| Canvas is a REASONS contract | `grep -Fq "## ${section}"` for required headings | `scripts/validate-reasons-canvas.sh` |
| Ready For Coding | `re.search(r"ready\s+for\s+coding", text, re.I)` anywhere in the canvas | `workflow.py` `gate_check` |
| Architect / operations task-sized / code maps to ops / tests / safeguards | Listed in `GATE_LABELS` and `gates_for_phase()`; **not enforced** in `gate_check` | `phases.py` vs `workflow.py` |
| Safeguards checked | `sync()` sets `safeguards_checked=passed` if a review **file exists** | `workflow.py` `sync()` |
| Retrieval of past lessons | Filter on `work_id` / `area` / `kind` / **exact keyword-list membership**; no rank, no body FTS in `records()` | `lessons_ledger.py` |
| Quality gates | Markdown checklist | `harness/quality-gates.md` |

Bypasses that a methods paper must treat as part of the method, not footnotes:

- `advance --force` ("a human decision, never the agent's") — unenforceable in chat.
- `skip <phase> --reason`.
- `LOCAL-*` IDs skip all `gate_check`s.
- Slash commands are prompts. An agent can ignore them; only `sdlc.sh advance` is a hard stop, and only if someone runs it.

**Referee ask:** Either (a) harden validation until "governed" is an observable property of artifacts and traces, or (b) rewrite claims to "advised process with optional CLI gates."

### M5. Dual implementations threaten internal validity

Shell is the default (`SDLC_ENGINE` defaults to `shell` in `scripts/sdlc.sh`). Python is the "v2 reusable core." A study that says "the method does X" must say **which implementation**. Two stacks that can diverge are a confound: any measured effect might be "the Python gates" or "the shell path" or "the prompt the model followed."

**Referee ask:** Single source of truth for gate semantics, or an explicit compatibility test that the two engines implement the same method (not only the same files).

### M6. Retrieval and "DICE" are not yet an IR/context-engineering result

Docs describe Guide DICE as a hybrid lexical + embedding + typed graph working store. In this checkout:

- Baseline retrieve is ledger filter (`ContextStore.retrieve` → `LessonsLedger.records`).
- Keyword match is `kw not in rec.keywords` (exact, casefolded), not search over title/body.
- SQLite FTS exists on `db query --search` — a different surface than the mandated `context retrieve`.
- SPIKE-001/002 (Guide RAG, local embeddings) are **shelved**.
- There is no precision@k, recall, or ablation vs bulk-read / grep / embedding retrieval.

Progressive disclosure (Tier 1 ~2.5–2.9 KB) is an architectural assertion. Token cost, relevance, and task success are unmeasured.

**Referee ask:** Treat retrieval as an IR component: queries, qrels, baselines, metrics — or drop DICE language from the contribution claim.

### M7. Stale method artifacts are a validity signal

The method's own planning layer disagrees with itself:

- ROADMAP narrative: FEAT-004/005/006 complete; generated summary table still says Draft / In Progress (timestamp 2026-07-30).
- `docs/design-decisions.md` still describes duplicate canvas copies and `agent-context/extensions/`; later docs say those were removed in storage v3.
- `GATE_LABELS` / `gates_for_phase` describe a richer gate set than `gate_check` implements.

A process-research artifact that cannot keep its contracts aligned is evidence that **sync is optional in practice**, which undercuts the central claim.

---

## Minor comments

1. Alpha (`2.0.0a6`) plus an experimental ops console and a Vue3 replacement in flight: fine for a tool, awkward as a frozen evaluation artifact.
2. `docs/research/` is Jira ADF payload research, not a research program. Rename or add a real `docs/research/` index so referees are not misled.
3. Example review (`examples/spring-boot-order-api/spdd/reviews/FEAT-001-order-status-api-review.md`) is seven lines. If this is the pedagogical gold standard, it teaches that reviews may be ceremonial.
4. Command specs are a genuine method contribution (one spec → three adapters). That is replicable **documentation generation**, not evidence that three assistants *behave* the same.
5. Capture metrics stuffed into session **body** text (after dropping `kind=metric`) makes later analysis brittle. FEAT-004's intent and storage v3's kind set are misaligned.

---

## Threats to validity (if a study were run on the system as-is)

| Threat | Why it applies now |
|--------|---------------------|
| **Construct** | "Ready," "review," "safeguards," "retrieval" are file/regex/exact-keyword proxies. |
| **Internal** | Dual engine; `--force`/skip; chat can ignore prompts; Hawthorne effect in self-dogfood. |
| **External** | n=1 (this repo); Cursor-heavy live tests; toy example without source; Guide optional. |
| **Conclusion** | No inferential statistics, no pre-registration, no multiple LLM runs despite acknowledged nondeterminism. |
| **Reliability** | No inter-rater protocol for canvas quality or review quality. |

These are not optional "limitations" paragraphs. They are why the current artifact cannot support the README's causal language ("fixes that").

---

## What *would* constitute a contribution (success criteria for Milestone 2)

A defensible paper-shaped contribution, given this codebase, is **not** "we built another agent." It is closer to:

> A **repository-native process model** for AI-assisted delivery that makes (a) intent, (b) process compliance, and (c) context load **observable and comparable**, with evidence that the hybrid reduces a defined drift measure versus unstructured chat and versus parent methods used in isolation.

That requires, in order:

1. **Positioning** — RQs + constructs + related-work delta (DOC-001, DOC-002).
2. **Observability** — semantic canvas checks, intent↔code traceability, first-class metrics, retrieval as IR (FEAT-014–017).
3. **Evaluation** — protocol, then one multi-assistant behavioral slice, then a replication pack (TEST-001, TEST-002, DOC-003).
4. **Integrity of the method-in-use** — dogfood ledger survives archive; one engine semantics (CHORE-003, REF-001).

Until (1)–(3) exist, keep public language at: *operating model; engineering evaluation; research program in progress.*

---

## Proposed research questions (draft for DOC-001)

- **RQ1 (drift):** Does a versioned REASONS Canvas plus phase gates reduce *scope deviations* (operations implemented that are not on the canvas; canvas requirements unimplemented) vs unstructured assistant chat on the same tasks?
- **RQ2 (compliance):** What fraction of sessions are *process-compliant* (required artifacts present **and** semantically adequate), and can compliance be measured without trusting the agent?
- **RQ3 (context):** Do per-phase retrieval budgets reduce tokens loaded and increase relevance of loaded files vs bulk-read, without lowering task success?
- **RQ4 (memory):** Does ledger retrieval change subsequent-session defect/rework rates vs no memory and vs dumping the whole ledger?
- **RQ5 (portability):** Do Cursor, Copilot, and Claude Code produce comparable compliance and outcome profiles when adapters are held in spec parity?

---

## Code areas (for later implementation Work IDs)

| Area | Why it matters to the research object |
|------|----------------------------------------|
| `engine/src/sdlc_engine/workflow.py` | Actual gate semantics vs claimed lifecycle |
| `engine/src/sdlc_engine/phases.py` | Gate catalog that is not fully enforced |
| `engine/src/sdlc_engine/lessons_ledger.py` | Retrieval = filter, not IR; no metric kind |
| `engine/src/sdlc_engine/canvas.py` | Status/operation inference from markdown conventions |
| `scripts/validate-reasons-canvas.sh` | Heading-only contract check |
| `TESTING.md`, `tests/live-consumer/` | Engineering eval vs method eval |
| `spec/commands/` | The replicable method description |
| `examples/spring-boot-order-api/` | Insufficient as an empirical case |

---

## Assumptions

- Target contribution is empirical software engineering / AI-assisted development process, not a new LLM architecture.
- The authors want journal-or-ICSE-grade claims, not only a better README.
- Product tracks (ADF, Vue3) continue; this milestone does not block them, but research claims must not ride on unfinished product surface.
- Follow-on Work IDs are planned here; canvases are created per ID at plan time.

---

## Next

1. Treat this file as the analysis artifact for **SPIKE-004-academic-contribution-bar**.
2. Iterate Milestone 2 in priority order (P0 docs → P1 observability → P2 evaluation execution).
3. Do not implement FEAT-014+ until DOC-001/002 freeze the claims those features are supposed to make testable.
