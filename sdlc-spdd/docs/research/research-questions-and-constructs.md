# Research questions and operationalized constructs

**Work ID:** DOC-001-research-questions-and-constructs  
**Status:** Frozen for Milestone 2 unless `/sdlc-spdd-prompt-update` on the DOC-001 canvas  
**Date:** 2026-09-06  
**Parent plan:** [SPIKE-004 canvas](../../spdd/canvas/SPIKE-004-academic-contribution-bar.md)  
**Referee source:** [SPIKE-004 analysis](../../spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md) (M1)

This is the **construct spec** later Work IDs must implement. It is not a paper and not an evaluation result.

---

## 1. Academic review goal

**Object of review:** this repository (`sdlc-spdd-orchestrator`) as a methods/tools artifact — process + **stores** + **retrievability**. Not a completed causal study. Not a Deterministic Intent Folding paper. The **intent store** is the REASONS canvas. The **advice store** is storage v3’s three paths: the committed git **ledger** (`spdd/memory/lessons.jsonl`, system of record), the optional **SQLite** local index (`.sdlc/index.sqlite`, regenerable projection / FTS), and the optional **Guide** working-store projection (Neo4j via Guide DICE). Ledger writes; SQLite and Guide are projections. Parity is `sdlc-engine context parity`.

The method under review **stores**, then must be able to **read back**:

| Store | What it is | Where | Retrievability today |
|-------|------------|--------|----------------------|
| Intent | REASONS canvas — what ships and what does not | `spdd/canvas/<WORK-ID>.md` | Human + `gate_check` / canvas validator |
| Advice (ledger) | Reviewed lessons (`decision`, `pitfall`, `pattern`) | `spdd/memory/lessons.jsonl` | **TEST-003** persist→`context retrieve` same id; FEAT-017 lexical; CHORE-003 seeded dogfood |
| Advice (SQLite) | Regenerable local index of the same ledger ids | `.sdlc/index.sqlite` (schema v5) | **TEST-003** `context parity` missing/extra empty. Opt-in. `db query --search` is work_items FTS — a **different CLI**. |
| Advice (Guide) | Regenerable working-store projection of the same ledger ids | Guide DICE graph | **TEST-003** mocked `by-label` parity on default CI. Live Guide+Neo4j already in `test_guide_projection_roundtrip` / `test-guide-stack-experimental`. Unreachable Guide is skip, not a pass. |
| Process traces | Phase pointer, gates, claim/release | `.sdlc/` + `spdd/memory/registry.jsonl` | `sdlc.sh next` / registry |

**In-scope empirical claim:** stored advice is **retrievable** — persist/accept then find the same id on the ledger, and when each projection is enabled find the same ids in **SQLite** and **Guide**. Cite existing tests; do not invent a new SPIKE.

**In-scope replication claim (first-class):** this freeze is **Python 3 only**. A referee replicates with `./sdlc-spdd/docs/research/prove-academic-review.sh`. Live **Guide+Neo4j** is an **optional** projection (experimental e2e). Requiring a JVM graph store to accept the artifact **fails** this bar.

**This review's scope removed** reduced-**drift** (RQ1) and retrieve-**usefulness** (RQ4 / C-MEMORY follow-on rework). Those are not leftover holes in this freeze. RQ1 and RQ4 headings in §3 stay so a later, separate paper has measures; they are **not** this review.

**Also not this review:** Guide **embeddings** as an IR result; SQLite FTS (`db query --search`) as the same algorithm as `context retrieve`; Deterministic Intent Folding (`embabel-dif`, already removed — later / other-repo).

**Pass for this review bar:** a referee can find (1) what is stored, (2) that stored advice can be retrieved from the **ledger** and, when enabled, from the **SQLite index** and the **Guide store**, (3) what `gate_check` actually checks, (4) an allow-list of public sentences, and (5) that replication of (1)–(4) is **Python 3 only** — live Guide+Neo4j stays **optional**. Closest venue fit: ICSE NIER / AIware / LLM4Code, or SEIP with explicit limitations.

**Fail / out of scope for this bar:**

- “SDLC-SPDD reduces drift.” That sentence came from README marketing (`fixes that`). Drift was **removed from this review's scope**. It is **not** Fowler SPDD’s job and **not** the criterion for accepting this artifact. TEST-002 slices are **instrumentation demos**, not this review.
- Deterministic Intent Folding (`jmjava/embabel-dif`), Embabel GOAP, or a JVM fold as a result of *this* review. Optional present-or-skip CLI attach already exists when the sibling is present; absence is skip. That pairing is **later / other-repo**. This freeze is **foundational** to it (a versioned canvas and retrievable advice ledger a fold can read) and **does not require it**.

Do **not** open a new SPIKE to re-plan this. This file is the freeze. Retrievability’s named suite is **TEST-003** (`tests/research/test_cretrieve.py`; [cretrieve-suite.md](cretrieve-suite.md)).

---

## 2. Provisional contribution sentence

DOC-002 may tighten wording. It must not contradict this sentence:

> A **repository-native process model** for AI-assisted delivery that **stores intent** (REASONS canvas) and **stores agent/human advice** in a git ledger with regenerable **SQLite** and **Guide** projections, and makes stored records **retrievable** so that (a) intent, (b) process compliance, and (c) retrievable memory are **observable and comparable**. The evaluation of that claim is **Python 3 only**; live Guide+Neo4j is an **optional** projection, not a replicator requirement.

Do **not** append “with evidence that the hybrid reduces drift.” Drift and usefulness were **removed from this review's scope**. Do **not** treat RQ4 usefulness or Guide embeddings as this review’s pass bar.

---

## 3. Research questions

Each RQ names an independent variable (IV) and dependent construct(s). “SDLC-SPDD” means Planning artifacts + REASONS Canvas + phase commands/gates + ledger retrieval, as specified in this repo — **not** “any structured prompt.”

### RQ1 — Drift (C-DRIFT)

**Does a versioned REASONS Canvas plus phase gates reduce scope deviations versus unstructured assistant chat on the same gold tasks?**

This review's **scope removed** RQ1. The heading remains so a later paper has a measure. A slice that only shows the scorer can run is instrumentation, not an answer to RQ1. Academic review of this repo **fails** if the paper is framed as an RQ1 finding.

| | |
|--|--|
| **IV** | Process condition: unstructured chat vs full SDLC-SPDD (TEST-001 may also include canvas-only) |
| **DV** | C-DRIFT (`ScopeDeviationRate`) |
| **H1 (directional)** | `ScopeDeviationRate` is lower under full SDLC-SPDD than under unstructured chat |
| **Needed to answer** | TEST-001 protocol, FEAT-016 mapping, TEST-002 slice |

### RQ2 — Compliance (C-COMPLY)

**What fraction of sessions are process-compliant (required artifacts present *and* semantically adequate), and can that fraction be measured without trusting the agent’s self-report?**

| | |
|--|--|
| **IV** | Measurement method: file-existence proxies vs semantic instruments (FEAT-014/016) |
| **DV** | C-COMPLY (`ProcessComplianceRate`) |
| **H2** | Existence-only `ProcessComplianceRate` overestimates semantic compliance |
| **Needed to answer** | FEAT-014, FEAT-016, TEST-001 rater protocol |

### RQ3 — Context (C-CONTEXT)

**Do per-phase retrieval budgets reduce context load and increase relevance of loaded files versus bulk-read, without lowering task success?**

| | |
|--|--|
| **IV** | Context policy: bulk-read vs per-phase retrieve (ledger/filter today; IR later) |
| **DV** | C-CONTEXT (`ContextLoad`, `ContextRelevance`); task success as a **guardrail**, not the primary DV |
| **H3** | `ContextLoad` is lower and `ContextRelevance` is not worse under per-phase retrieve |
| **Needed to answer** | FEAT-015 (load), FEAT-017 (relevance), TEST-001/002 (success guardrail) |

### RQ4 — Memory (C-MEMORY)

**Does ledger retrieval change subsequent-session rework versus no memory and versus dumping the whole ledger?**

This review's **scope removed** RQ4 (retrieve usefulness). The heading remains so a later paper has a measure. It is **not** this review.

| | |
|--|--|
| **IV** | Memory policy: none vs full-ledger dump vs `context retrieve` |
| **DV** | C-MEMORY (`MemoryUsefulness`) via C-REWORK on a follow-on task |
| **H4** | Retrieve beats none and is not worse than dump on rework, at lower C-CONTEXT |
| **Needed to answer** | FEAT-015/017, TEST-001 two-session protocol — **not** in TEST-002’s first slice unless specified |

### RQ5 — Portability (C-PORT)

**Do Cursor, Copilot, and Claude Code produce comparable compliance and outcome profiles when adapters are held in spec parity?**

| | |
|--|--|
| **IV** | Assistant (Cursor / Copilot / Claude Code) with spec-generated adapters |
| **DV** | C-PORT (`PortabilityGap`) on C-COMPLY and C-DRIFT |
| **H5** | Adapter-text parity does **not** imply behavioral parity (`PortabilityGap` > 0 is expected) |
| **Needed to answer** | TEST-002 (at least two assistants if APIs allow; else document single-assistant limitation) |

**No RQ6.** Additions require prompt-update on DOC-001.

---

## 4. Constructs

Every row: **definition**, **measure**, **instrument** (what exists *today* vs **target Work ID**), **proxy weakness**.

### C-DRIFT — Scope deviation

| Field | Spec |
|-------|------|
| **Definition** | A **scope deviation** is either (a) an implemented change that does not map to an approved canvas operation, or (b) an approved operation with no corresponding implementation evidence in the diff. |
| **Measure** | `ScopeDeviationRate = (N_unmapped_hunks + N_unimplemented_ops) / (N_hunks + N_ops)` on a gold task. Report numerator parts separately. |
| **Instrument today** | None. Human can eyeball canvas vs diff. |
| **Target instrument** | **FEAT-016** (operation↔path mapping + automated remainder). TEST-002 records the rate on one gold task. |
| **Proxy weakness** | File-touch heuristics miss hunks in “allowed” files that implement extra behavior; humans miss silent non-goals. |

### C-COMPLY — Process compliance

| Field | Spec |
|-------|------|
| **Definition** | A session is **process-compliant** iff required artifacts for the claimed phase exist **and** meet semantic minima (non-empty required canvas sections; structured readiness for `code`; review states result + safeguards explicitly). |
| **Measure** | `ProcessComplianceRate = N_compliant_sessions / N_sessions`. Always publish **existence-only** and **semantic** rates as a pair (H2). |
| **Instrument today** | `gate_check(code)` uses Metadata/frontmatter readiness plus non-empty Requirements and a T## operation with Status (**FEAT-014**). Review minima (**FEAT-016**) apply at retro/sync. Capture `--readiness` / `--review-result` are queryable via `sdlc-engine context metrics --construct C-COMPLY` (**FEAT-015**). `validate-reasons-canvas.sh` fails headings-only canvases; `--strict-readiness` fails unrecognized tokens. |
| **Target instrument** | **FEAT-016** (review minima; no auto-pass safeguards). Canvas semantic minima for `code` are in place. |
| **Proxy weakness** | Empty review can still pass `review`/`sync`. Phrase-in-Sync-Notes no longer fools the **code** gate. |

### C-CONTEXT — Context load and relevance

| Field | Spec |
|-------|------|
| **Definition** | **Load:** how much context the process caused to be loaded (files or tokens). **Relevance:** whether loaded items were used for the gold task (qrels / rater). |
| **Measure** | `ContextLoad` = count of distinct files listed as loaded (or token estimate if available). `ContextRelevance@k` = precision of retrieved lesson ids vs a qrel set (FEAT-017). |
| **Instrument today** | Optional capture `--context-files` stored on `record.metrics.context_files` and queried with `sdlc-engine context metrics --construct C-CONTEXT` (**FEAT-015**). Body tags remain a human copy. `context retrieve --keyword` is still exact keyword-list membership. `context retrieve --query` ranks title/body lexically (**FEAT-017**). SQLite FTS is a *different* CLI (`db query --search`). Guide DICE embeddings are **unmeasured**. |
| **Target instrument** | **FEAT-015** (structured `context_files`) + **FEAT-017** (lexical title-body vs keyword-list; DICE still unmeasured). |
| **Proxy weakness** | `--context-files` is self-reported and optional; it does not prove what the model actually attended to. |

### C-MEMORY — Memory usefulness

| Field | Spec |
|-------|------|
| **Definition** | Whether retrieved lessons improve a **follow-on** task versus no memory / dump, after controlling for C-CONTEXT. |
| **Measure** | Primary: C-REWORK on session 2 (`ReworkCount` or cycles). Secondary: C-DRIFT on session 2. |
| **Instrument today** | Ledger kinds `decision|pitfall|pattern`; retrieve by work_id/area/kind/keyword and `--query` title-body (**FEAT-017**). Capture rework/cycles queryable via `context metrics --construct C-MEMORY` (**FEAT-015**). Committed dogfood ledger is **seeded** (CHORE-003); archive must not truncate it. |
| **Target instrument** | TEST-001 two-session protocol; FEAT-015 `context metrics --construct C-MEMORY`; CHORE-003 so memory exists to retrieve. |
| **Proxy weakness** | Counting retrieve *calls* is not usefulness. A seeded ledger makes retrieve non-vacuous. Usefulness was **removed from this review's scope**. Retrievability (C-RETRIEVE) is the in-scope claim. |

### C-PORT — Portability (assistant)

| Field | Spec |
|-------|------|
| **Definition** | Difference in C-COMPLY and C-DRIFT across assistants when **command specs are in parity**. |
| **Measure** | `PortabilityGap = max_a(rate_a) - min_a(rate_a)` for C-COMPLY and for C-DRIFT separately. |
| **Instrument today** | `validate-command-adapters.sh` — **text** parity, not behavior. Live consumer matrix is Cursor-oriented. |
| **Target instrument** | **TEST-002** recorded runs. If only one assistant API is available, C-PORT is **not reported as a result**; the limitation is written beside the slice. |
| **Proxy weakness** | Adapter markdown equality is not behavioral equality (H5). |

### Supporting measure (not a sixth RQ)

| ID | Definition | Measure | Today | Target | Weakness |
|----|------------|---------|-------|--------|----------|
| **C-REWORK** | Repeated repair on the same gold-task acceptance criterion | `--rework` count / `--review-cycles` / `--validate-cycles` | `record.metrics` via `context metrics --construct C-REWORK` (**FEAT-015**) | Same query in TEST-002 session 2 | Self-reported; undefined if flags omitted |
| **C-RETRIEVE** | A stored lesson can be found again | Ledger: persist/accept then `context retrieve` returns the id. SQLite (when enabled): `context parity` missing/extra empty. Guide (when enabled): parity missing empty. | **TEST-003** `tests.research.test_cretrieve` ([cretrieve-suite.md](cretrieve-suite.md)) for hermetic CI. Live Guide+Neo4j: `engine/tests_e2e/test_guide_projection_roundtrip.py` (`test-guide-stack-experimental`). FEAT-017 + CHORE-003 supporting. | Same; SQLite and Guide remain optional for replication | Drift and usefulness were **removed from this review's scope**. Guide **embeddings** are not this bar. Mocked Guide is HTTP parity, not DICE. `db query --search` is a different CLI. |

---

## 5. Claims allowed today vs after Milestone 2

Use this table when editing README, compliance, or talks. **If a cell says no, do not say it as a finding.**

| Claim | Today | After P0 (DOC-001/002, TEST-001) | After P1 (instruments) | After P2 (TEST-002 slice) |
|-------|-------|----------------------------------|------------------------|---------------------------|
| Unstructured chat often produces drift, lost decisions, session amnesia | **Allowed as motivation** (practitioner claim, unmeasured here) | Same | Same | Same unless you cite TEST-002 |
| This repo is an installable operating model (Planning + SPDD + SDLC) | **Yes** | Yes | Yes | Yes |
| Prompts/canvases are version-controlled artifacts | **Yes** | Yes | Yes | Yes |
| Intent and advice are **stored in git** and queryable | **Yes** — canvas + `lessons.jsonl` + FEAT-015 metrics. | Yes | Yes | Yes |
| Stored advice is **retrievable** from the ledger (`context retrieve`) | **Yes** — TEST-003 persist→same id. | Yes | Yes | Yes |
| SQLite local index holds the **same lesson ids** as the ledger when sqlite is enabled (`context parity`) | **Yes** — TEST-003. Opt-in. `db query --search` is a different CLI. | Same | Same | Same |
| Guide working store holds the **same lesson ids** as the ledger when Guide is enabled (`context parity`) | **Yes** — TEST-003 mocked HTTP on **Python 3** default CI. Live Guide+Neo4j is **optional**. Unreachable skip is **not** a pass. Embeddings are **out of this bar**. | Same | Same | Same |
| A referee can replicate this freeze with **Python 3 only** | **Yes** — `prove-academic-review.sh` | Yes | Yes | Yes |
| Live Guide+Neo4j is **required** to accept the artifact | **No** — optional projection | **No** | **No** | **No** |
| Some CLI gates exist (`gate_check`) | **Yes** (describe what they actually check) | Yes | Describe *semantic* gates after FEAT-014/016 | Yes |
| SDLC-SPDD **fixes** drift | **No** — drift **removed from this review's scope** | **No** | **No** | **No** |
| The canvas **governs** execution (causal, non-bypassable) | **No** — say *advised process + optional CLI gates* | Same | Stronger *observable* compliance (C-COMPLY) | Same; still bypassable via `--force`/ignoring chat |
| Three assistants run the **same method** | **Only adapter-text parity** | Same | Same | Behavioral C-PORT if ≥2 assistants recorded |
| Ledger retrieval improves later work | **No** — usefulness **removed from this review's scope** | **No** | **No** | **No** |
| DICE / hybrid graph retrieval is a result | **No** (SPIKE-001 shelved; retrieve was keyword-list filter) | **No** | **No** — FEAT-017 measured **lexical** title-body vs keyword-list only; Guide embeddings unmeasured | Still **non-claim** unless a later ID measures DICE |
| Deterministic Intent Folding / `embabel-dif` is a result of this review | **No** — later / other-repo. Optional present-or-skip attach is not a finding. | **No** | **No** | **No** |
| Engineering tests prove the method works | **No** — they prove the *tool* | TEST-001 says how we will test the method | Instruments exist | One slice exists; not a journal N |

---

## 6. README / compliance rewrite guidance (apply in T02)

Do **not** apply these edits in T01.

**README “Why it exists”** currently: “SDLC-SPDD **fixes that** with three durable layers…”

Replace the causal verb with design intent, for example:

- “SDLC-SPDD is **designed to make that drift reviewable** with three durable layers…”
- Keep the three-layer table.
- Change “The canvas **governs** execution” → “The canvas is the **contract** for execution; CLI gates can refuse some phase advances when artifacts are missing.”

**Compliance docs** (`sdlc-spdd/docs/spdd-compliance.md`): keep the mapping table (how the scaffold *attempts* to satisfy Fowler SPDD) but do not imply empirical satisfaction.

After T02, a grep for `fixes that` in `README.md` should not remain as an unqualified result.

---

## 7. Mapping to Milestone 2 Work IDs

| Construct / RQ | Must implement or measure |
|----------------|---------------------------|
| Freeze (this file) | DOC-001 |
| Novelty sentence vs literature | DOC-002 |
| Protocol procedures per RQ | TEST-001 |
| C-COMPLY semantic minima | FEAT-014 |
| C-REWORK / C-CONTEXT structured capture | FEAT-015 |
| C-DRIFT mapping; review minima | FEAT-016 |
| C-CONTEXT relevance; retrieve algorithm | FEAT-017 |
| C-RETRIEVE (ledger + SQLite + Guide projection round-trip) | **TEST-003** ([cretrieve-suite.md](cretrieve-suite.md)); FEAT-017, CHORE-003 supporting |
| RQ1/RQ2/RQ5 slice | TEST-002 |
| RQ4 precondition (memory exists) | CHORE-003 |
| Which engine is the SUT | REF-001 Complete ([engine-sut.md](engine-sut.md)) |
| Threats using these constructs | DOC-003 |

Child canvases for FEAT-014–017 **must cite construct IDs** in Requirements.

---

## 8. What TEST-002 should and should not claim

**Should:** one gold task with real source; unstructured vs full method; C-DRIFT and existence vs semantic C-COMPLY; assistant and model version written next to numbers.

**Should not:** significance tests on n=1; C-PORT if only one assistant ran; DICE results; “we fixed drift”; `embabel-dif` / fold results.

RQ4 is **out of the first TEST-002 slice** unless TEST-001 explicitly includes a two-session protocol.

A protocol-complete TEST-002 still does **not** change §1. It does not make reduced drift the academic-review object.

---

## 9. Freeze rule

Changing RQ text, adding RQ6, renaming construct IDs, or changing the academic-review object / contribution sentence is a **behavior change** of this spec: update the DOC-001 canvas with `/sdlc-spdd-prompt-update` before editing those parts. Clarifying examples and instrument paths may be synced after review.
