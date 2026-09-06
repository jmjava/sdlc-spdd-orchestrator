# Comparative evaluation protocol

**Work ID:** TEST-001-evaluation-protocol  
**Status:** Protocol only — this Work ID does **not collect study data**  
**Date:** 2026-09-06  
**Construct spec:** [DOC-001](research-questions-and-constructs.md)  
**Related-work baselines:** [DOC-002](related-work-and-novelty.md)  
**Parent plan:** [SPIKE-004 canvas](../../spdd/canvas/SPIKE-004-academic-contribution-bar.md)

This document tells TEST-002 (and later slices) **how** to evaluate the method. It is not a results paper. Do not paste n, p-values, or “we found” claims here.

Guide is **fork-only**. This protocol does not depend on an Embabel upstream merge.

---

## 1. Object of evaluation

**Method (SUT until REF-001 names it otherwise):** Planning artifacts + REASONS Canvas + phase commands/gates + ledger retrieval, as implemented by the Python `gate_check` path plus spec-generated assistant adapters.

**Not the object:** CLI unit tests, adapter-text parity, or SWE-bench agent competence. Those stay in `TESTING.md`.

Until REF-001, treat **shell `sdlc.sh` without `SDLC_ENGINE=python` as a confound**, not a second condition.

---

## 2. Baselines (DOC-002 made these the comparison)

Every RQ that compares “the method” uses these four process conditions on the **same gold task**:

| Condition | Operator instruction | Intent artifact | Lifecycle |
|-----------|----------------------|-----------------|-----------|
| **unstructured chat** | Solve the gold task in one assistant thread. No canvas, no phase commands, no ledger retrieve. | None (chat only) | None |
| **canvas-only** | Write/follow a REASONS canvas (Fowler-like). Do not run SDLC phase commands or `gate_check`. | Canvas file | None |
| **lifecycle-only** | Use analysis→…→sync commands / briefs (SDLC Agents-like). No REASONS canvas. | Planning files / briefs | Phases |
| **full SDLC-SPDD** | Canvas + phase commands + optional `SDLC_ENGINE=python ./scripts/sdlc.sh gate --phase …` + `context retrieve` when the task is a follow-on | Canvas + phase artifacts | Phases + gates + retrieve |

Do not invent a fifth “prompt file dump” condition in TEST-002’s first slice.

---

## 3. Gold task

### 3.1 Intended journal gold (blocked)

**Task:** implement `GET /api/orders?email=` as specified by:

- Requirement: `examples/spring-boot-order-api/requirements/add-order-status-api.md`
- Canvas: `examples/spring-boot-order-api/spdd/canvas/FEAT-001-order-status-api.md`
- Review fixture: `examples/spring-boot-order-api/spdd/reviews/FEAT-001-order-status-api-review.md`

**Stop rule for using this gold:** do **not** start TEST-002 on this example until it contains real Java sources (`*.java` under `examples/spring-boot-order-api/`). Today it has **no Java** sources — only requirement, canvas, and a seven-line review. Scoring C-DRIFT against a missing implementation is undefined.

**Owner:** TEST-002 (restore or replace the example with a compiling service + tests).

### 3.2 First TEST-002 slice gold (has source today)

**Task:** extend the live-consumer seed hello app so a documented canvas operation is implemented in source, with a test.

- Source: `tests/live-consumer/seed/src/hello.py`
- Seed README: `tests/live-consumer/seed/README.md`
- Seed canvas: `tests/live-consumer/seed/sdlc-spdd/spdd/canvas/FEAT-001-hello-live.md`
- Seed requirement: `tests/live-consumer/seed/sdlc-spdd/requirements/milestones/FEAT-001-hello-live.md`

TEST-002 must freeze a **single new acceptance criterion** on that canvas before runs (prompt-update the seed canvas or copy it into a dated eval fixture). The gold is the pair (canvas operation, expected source/test change), not “make hello.py nicer.”

**Executed freeze location:** `tests/eval/test-002-hello/` is the dated eval fixture copied from this seed. Do not mutate `tests/live-consumer/seed/`. Slice logs and scores live next to that fixture, not in this protocol.

### 3.3 Gold-task completeness checklist (raters)

A gold is usable only if all are true:

1. Source files exist and compile/run.
2. Canvas lists numbered operations; the eval operation is one of them.
3. Non-goals are explicit (used when scoring extra hunks as C-DRIFT).
4. A failing test or observable behavior defines success independently of the assistant’s self-report.

---

## 4. Procedures per research question

### RQ1 procedure — C-DRIFT vs unstructured chat

**IV:** process condition (unstructured chat vs full SDLC-SPDD; canvas-only is allowed as a third arm).  
**DV:** `ScopeDeviationRate` (DOC-001).  
**Steps:**

1. Freeze the gold (3.2 for the first slice).
2. For each condition, run n independent sessions (see §6).
3. After each session, a rater maps every diff hunk to a canvas operation or to “unmapped,” and every canvas operation to “implemented” or “unimplemented.”
4. Compute `ScopeDeviationRate = (N_unmapped_hunks + N_unimplemented_ops) / (N_hunks + N_ops)`. Publish numerators separately.
5. Until FEAT-016 exists, mapping is **human**; do not pretend `gate_check` measured C-DRIFT.

**H1 scoring:** directional comparison of rates; n=1 task is a protocol slice, not a significance test. TEST-002 **must not** claim the method fixes drift.

### RQ2 procedure — existence vs semantic C-COMPLY

**IV:** measurement method (file-existence proxies vs semantic instrument).  
**DV:** `ProcessComplianceRate` pair.  
**Steps:**

1. On the same sessions as RQ1 (full SDLC-SPDD and, if collected, canvas-only / lifecycle-only).
2. **Existence-only:** required files present; canvas matches `/ready for coding/i` anywhere; review file exists (`gate_check` / `validate-reasons-canvas.sh` today).
3. **Semantic:** required REASONS sections non-empty; readiness is a structured field; review states result + safeguards explicitly (FEAT-014/016; until then, **raters** apply the semantic minima from DOC-001 C-COMPLY).
4. Publish both rates. H2: existence-only is expected to be higher.

### RQ3 procedure — C-CONTEXT load and relevance

**IV:** context policy (bulk-read listed files vs per-phase `context retrieve`).  
**DV:** `ContextLoad`, `ContextRelevance`; task success as **guardrail**.  
**Steps:**

1. Two arms on the gold: (a) operator pastes/opens the whole `sdlc-spdd/` tree relevant to the task; (b) operator follows per-phase retrieve only.
2. Record distinct files listed as loaded (capture `--context-files` or a rater log of `@` attachments). That is ContextLoad.
3. Relevance: two raters mark each loaded file used / unused for the gold operation (qrels). Precision is secondary until FEAT-017.
4. Guardrail: if (b) fails the gold acceptance criterion where (a) succeeds, report that; do not hide it.

Record ContextLoad on `record.metrics.context_files` (`sdlc-engine context metrics --construct C-CONTEXT`) and still copy it into the TEST-002 log table.

### RQ4 procedure — C-MEMORY via follow-on rework

**IV:** memory policy (none vs full-ledger dump vs `context retrieve`).  
**DV:** C-REWORK on session 2; secondary C-DRIFT on session 2.  
**Steps:**

1. Session 1: complete the gold under full SDLC-SPDD; capture at least one `pitfall` or `decision` lesson (`sdlc.sh capture` / accept).
2. Session 2 (new chat): a **follow-on** that requires the session-1 decision (define the follow-on in the TEST-002 fixture).
3. Arms: no memory; paste entire `lessons.jsonl`; retrieve by work-id/kind.
4. Score ReworkCount (repair cycles to reach the follow-on AC).

**First TEST-002 slice:** RQ4 is **out of scope** unless the fixture includes this two-session task. CHORE-003 (empty committed ledger) is a precondition for dogfood retrieve; eval runs may use a fixture ledger.

### RQ5 procedure — C-PORT across assistants

**IV:** assistant (Cursor / Copilot / Claude Code) with adapters held in spec parity.  
**DV:** `PortabilityGap` on C-COMPLY and C-DRIFT.  
**Steps:**

1. Repeat RQ1+RQ2 on at least two assistants if APIs allow.
2. If only one assistant API is available, **do not report C-PORT as a result**; write the single-assistant limitation beside the slice (DOC-001).
3. Adapter-text parity (`validate-command-adapters.sh`) is **not** C-PORT.

**Current limitation:** the live-consumer matrix (`tests/live-consumer/`) is **Cursor-oriented**. Copilot/Claude jobs are not an equivalent behavioral harness today. Owner: TEST-002 + live-consumer maintainers.

---

## 5. Rater protocol

- **Two independent raters** for C-DRIFT hunk mapping and for semantic C-COMPLY. A third rater breaks ties.
- Raters see diffs and canvases; they do **not** see the condition label if a third party can anonymize logs. If anonymization is impossible (canvas presence gives it away), say so in the TEST-002 log — that is a threat to validity, not a license to skip dual rating.
- Report simple percent agreement. Cohen’s κ is optional at n-small; do not dress a slice up as a reliability study.
- A rater sheet is a table: `session_id | condition | hunk_or_op | label | notes`. Store it next to the TEST-002 artifacts (DOC-003 will list the path).

---

## 6. Nondeterminism plan

| Held fixed | Allowed to vary | Record beside every number |
|------------|-----------------|----------------------------|
| Gold task + canvas commit SHA | Assistant sampling | Assistant name |
| Model id / version string the vendor exposes | Temperature if the product exposes it; else note “UI default” | Model id |
| Operator instruction sheet per condition | Natural language in the thread | Date, n sessions |
| `SDLC_ENGINE=python` when gates are used | Network / product drift | Engine SHA |

**n:** first TEST-002 slice uses **n ≥ 3** independent runs per condition that is actually collected (not n=1 dressed as a study). If budget allows only n=1, the log must say **protocol incomplete**, not “result.”

Do not pool runs across model versions.

---

## 7. Stop rules

1. **Stop a session** after two repair cycles on the same gold acceptance criterion, or 90 minutes wall-clock, whichever first. Count further work as C-REWORK overflow, not silent extra tries.
2. **Stop TEST-002** from using `examples/spring-boot-order-api/` until Java sources exist.
3. **Stop reporting C-PORT** if only one assistant ran.
4. **Stop reporting RQ4** if session 2 was not run.
5. **Stop causal README language** until a comparison is recorded (already DOC-001).
6. **Stop the slice** if the operator violates the condition (e.g. pastes a canvas into “unstructured chat”). That run is invalid, not a low C-DRIFT score.

---

## 8. Metrics table (what TEST-002 must log)

| ID | When | Instrument now | Instrument after P1 |
|----|------|----------------|---------------------|
| C-DRIFT | every condition | Human hunk↔op map | FEAT-016 remainder |
| C-COMPLY existence | full method (+ others if collected) | `gate_check` / heading grep | still published as the weak rate |
| C-COMPLY semantic | same | Raters using DOC-001 minima | FEAT-014/016 |
| C-CONTEXT load | RQ3 arms | File list / `--context-files` | FEAT-015 fields |
| C-REWORK | RQ4 session 2 only | Repair-cycle count | FEAT-015 `--rework` |
| C-PORT | ≥2 assistants | Difference of C-DRIFT and C-COMPLY | same, recorded |

---

## 9. Current blockers (with owners)

| Blocker | Why it matters | Owner |
|---------|----------------|-------|
| `examples/spring-boot-order-api/` has **no Java** sources | Intended gold cannot score C-DRIFT vs implementation | TEST-002 |
| Live consumer matrix is **Cursor-oriented** | RQ5/C-PORT cannot be claimed from that harness | TEST-002 / live-consumer |
| Dual engine (shell vs Python `gate_check`) | Confound for “the method” | REF-001 |
| Committed `lessons.jsonl` empty after Milestone 1 archive | RQ4 dogfood retrieve is vacuous in this repo | CHORE-003 |
| Existence-only gates | RQ2 semantic arm needs raters until FEAT-014/016 | FEAT-014, FEAT-016 |
| Retrieve is exact keyword-list filter | RQ3 relevance is rater-only until FEAT-017 | FEAT-017 (lexical title-body vs keyword-list; DICE still unmeasured) |

---

## 10. Threats-to-validity draft (DOC-003 completes)

- **Construct:** today’s gates are not C-COMPLY; human C-DRIFT maps can disagree.
- **Internal:** condition leakage (canvas visible); operator is often the author.
- **External:** one gold, one lab, Cursor-heavy tooling.
- **Conclusion:** a passing TEST-002 slice shows the protocol *runs*; it does not show the method *works* at journal n.

DOC-003 must expand this list after instruments exist. That pack is `threats-to-validity-and-replication.md`. This Work ID does **not collect study data**.
