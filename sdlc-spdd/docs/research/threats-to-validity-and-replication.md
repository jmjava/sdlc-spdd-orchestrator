# Threats to validity and replication notes

**Work ID:** DOC-003-replication-package  
**Status:** Replication pack — this Work ID does **not collect study data**  
**Date:** 2026-09-06  
**Construct spec:** [DOC-001](research-questions-and-constructs.md)  
**Protocol:** [TEST-001](evaluation-protocol.md)  
**Parent plan:** [SPIKE-004 canvas](../../spdd/canvas/SPIKE-004-academic-contribution-bar.md)

This is the referee appendix SPIKE-004 called for: threats updated against **instruments that exist today** (FEAT-014/015/016 plus TEST-001), a freeze checklist, and an explicit statement of what the live-consumer harness does **not** prove.

Guide is **fork-only**. This pack does not depend on an Embabel upstream merge.

---

## 1. Construct validity

Each DOC-001 construct is only as valid as its current instrument. Do not treat a CLI pass as the construct.

| Construct | What is observable today | Remaining threat |
|-----------|--------------------------|------------------|
| **C-DRIFT** | FEAT-016 requires `- Files:` on each `### T##`. That is a named-path contract, not a hunk map. | Extra behavior in an allowed file, and unimplemented ops with a listed path, still need a human remainder ([code-maps-to-ops.md](code-maps-to-ops.md)). |
| **C-COMPLY** | FEAT-014 semantic minima on `gate_check(code)`; FEAT-016 review Result + safeguards; existence vs semantic rates must still be published as a pair. | `--force` / ignoring chat still bypasses the method. Empty headings no longer count, but phrase quality beyond the minima is rater-only. |
| **C-CONTEXT** | FEAT-015 `record.metrics.context_files` via `sdlc-engine context metrics --construct C-CONTEXT`. | Self-reported load. Does not prove attention. Relevance is rater/qrel until FEAT-017. |
| **C-MEMORY** | FEAT-015 `context metrics --construct C-MEMORY` (C-REWORK fields on a follow-on). Retrieve `--keyword` is exact list membership; `--query` ranks title/body (**FEAT-017**). CHORE-003 seeded the dogfood ledger; archive never truncates it. | Usefulness is C-REWORK on session 2 (TEST-001 RQ4), not retrieve-call counts. Guide DICE embeddings are unmeasured. |
| **C-RETRIEVE** | **TEST-003** persist→same id (`tests.research.test_cretrieve`; [cretrieve-suite.md](cretrieve-suite.md)). Ledger retrieve, SQLite parity, mocked Guide `by-label` in default CI. | Mocked Guide is HTTP parity, not DICE. Unreachable Guide is skip, not a pass. Live Neo4j e2e is extra. |
| **C-PORT** | `validate-command-adapters.sh` is **text** parity. | Adapter markdown equality is not behavioral equality. Live-consumer is Cursor-oriented. If only one assistant ran, C-PORT is not a result. |

SPIKE-004’s earlier “file/regex/exact-keyword proxies” row is **partially retired** for C-COMPLY (code + retro/sync minima exist) and **not retired** for C-DRIFT hunks or C-CONTEXT relevance.

---

## 2. Internal validity

| Threat | Status after P2 |
|--------|-----------------|
| Dual engine (shell `sdlc.sh` vs Python `gate_check`) | Retired as a default confound (REF-001). The research SUT is Python `gate_check` (`SDLC_ENGINE=auto` or `python`). `SDLC_GATE_ENGINE=shell` is not an evaluation condition. |
| `--force` / skip | Still lets an operator complete a session that is not process-compliant. Log `--force` as invalid for C-COMPLY scoring. |
| Chat can ignore the canvas | The method is advised process + optional CLI gates, not a causal sandbox. |
| Operator is often the author | Hawthorne / demand characteristics. TEST-002 must say if the operator wrote the method. |
| Condition leakage | Canvas presence reveals the “full method” / “canvas-only” arm. TEST-001 already records this as a rater-blinding threat, not a license to skip dual rating. |

---

## 3. External validity

| Threat | What a replicator must write beside numbers |
|--------|-----------------------------------------------|
| n = this repository | One lab, one orchestrator. Do not generalize to “AI-assisted delivery.” |
| Gold task | First TEST-002 slice gold is a copy of `tests/live-consumer/seed/src/hello.py` frozen at `tests/eval/test-002-hello/src/hello.py`, not a production service. |
| Intended journal gold blocked | `examples/spring-boot-order-api/` still has **no Java** sources — TEST-001 stop rule. |
| Assistant mix | Live-consumer matrix is Cursor-oriented. Copilot/Claude adapter-text jobs are not an equivalent behavioral harness. |
| Guide / Neo4j | Optional projection. Replication must not require Guide. Fork-only; never an Embabel PR. |

---

## 4. Conclusion validity

TEST-001 **does not collect study data**. A green CLI suite proves the *tool*, not the method.

TEST-002’s first slice, if run, uses **n ≥ 3** independent runs per collected condition. If budget allows only n=1, the log must say **protocol incomplete**, not “result.” Do not pool runs across model versions. Do not report p-values or “we showed” on n-small.

Passing `gate_check` or `context metrics` during a slice is instrumentation, not evidence that SDLC-SPDD reduces C-DRIFT.

---

## 5. Reliability

TEST-001 specifies two independent raters for C-DRIFT hunk mapping and semantic C-COMPLY, with a third rater for ties, and simple percent agreement. That protocol has **not been executed**. Capture flags (`--rework`, `--context-files`) are self-reported; omitted flags leave the measure undefined (FEAT-015).

Do not dress an unexecuted rater sheet as a reliability study.

---

## 6. Chat nondeterminism (how TEST-001 handles it)

Assistant sampling **cannot be automated away**. TEST-001 §6 (Nondeterminism plan) is the freeze rule this pack inherits:

| Held fixed | Allowed to vary | Record beside every number |
|------------|-----------------|----------------------------|
| Gold task + canvas commit SHA | Assistant sampling | Assistant name |
| Model id / version string the vendor exposes | Temperature if the product exposes it; else “UI default” | Model id |
| Operator instruction sheet per condition | Natural language in the thread | Date, n sessions |
| `SDLC_ENGINE=auto` or `python` when gates are used (`SDLC_GATE_ENGINE=shell` forbidden) | Network / product drift | Engine SHA |

**n ≥ 3** per collected condition, or the slice is **protocol incomplete**. Do not pool across model versions. This Work ID does not run those sessions.

---

## 7. Replication checklist

Freeze these **before** any TEST-002 session. Copy the filled row into the slice log.

| Item | Freeze how | Location / command |
|------|------------|--------------------|
| Engine commit | `git rev-parse HEAD` | this repo |
| Engine version | `python3 -c "import sdlc_engine; print(sdlc_engine.__version__)"` | currently `2.0.0a6` at DOC-003 write time; re-print at run time |
| Gate SUT | default `SDLC_ENGINE=auto` (or `python`); never `SDLC_GATE_ENGINE=shell` | [engine-sut.md](engine-sut.md); `sdlc-engine gate --phase code --work-id <WID>` |
| Capture metrics | structured fields, not body grep | `sdlc-engine context metrics --construct C-REWORK` ([capture-metrics-queries.md](capture-metrics-queries.md)) |
| Construct spec | file SHA | `sdlc-spdd/docs/research/research-questions-and-constructs.md` |
| Evaluation protocol | file SHA | `sdlc-spdd/docs/research/evaluation-protocol.md` |
| First-slice gold source | file SHA | `tests/live-consumer/seed/src/hello.py` |
| First-slice gold canvas | file SHA | `tests/live-consumer/seed/sdlc-spdd/spdd/canvas/FEAT-001-hello-live.md` |
| Adapter text parity (not C-PORT) | script exit code | `./scripts/validate-command-adapters.sh` |
| Model | vendor model id string | record beside every number |
| Assistant | product name | Cursor / Copilot / Claude Code |
| P0/P1 proof | checker | `./sdlc-spdd/docs/research/prove-p0.sh all` then `python3 -m unittest tests.research.test_p0_artifacts -v` |
| C-RETRIEVE suite | unittest exit 0 | `PYTHONPATH=engine/src python3 -m unittest tests.research.test_cretrieve -v` |

Rater sheet path for TEST-002 (when collected): store next to the slice artifacts as `session_id | condition | hunk_or_op | label | notes` (TEST-001 §5). This pack does not invent a filled sheet.

---

## 8. What the live-consumer harness does and does not prove

**Does prove (engineering):** seed install, capture-session-memory flags, slash-command side effects, and populate/flush on a Cursor-oriented matrix (`tests/live-consumer/`, `TESTING.md`). Those jobs are tool tests.

**Does not prove (method):** C-DRIFT versus unstructured chat, semantic C-COMPLY versus existence-only, C-CONTEXT relevance, C-MEMORY usefulness, or C-PORT across assistants. Do not cite a green `test-live-consumer-shell` job as a TEST-002 result.

---

## 9. What cannot be automated

- Hunk-level C-DRIFT mapping (FEAT-016 remainder)
- Semantic C-COMPLY beyond Result/safeguards/Files/readiness minima
- Assistant sampling / chat nondeterminism
- Inter-rater agreement (requires two humans)
- Guide/Neo4j as a required replicator dependency (must stay optional)

Human-subject / IRB packaging is out of scope (requirement non-goal).

---

## 10. Claims this pack still forbids

Until TEST-002 records a comparison under TEST-001 stop rules: do not say the method **fixes drift**, do not report C-PORT from one assistant, do not treat DICE/Guide retrieval as a result, and do not treat engine unit tests as method evaluation. TEST-003 is the engineering retrievability gate, not RQ4 usefulness. See DOC-001 claims-allowed table.
