# Chelsea Troy and the SDLC-SPDD Framework

How [Chelsea Troy's writing on LLMs as software engineers](https://chelseatroy.com/2025/07/14/what-can-we-expect-of-llms-as-software-engineers/) informs this orchestrator — and where the framework implements her recommendations.

This is complementary to [Fowler SPDD compliance](spdd-compliance.md) and [context loading and scaling](context-loading-and-scaling.md). Fowler gives the **workflow and artifacts**; Troy gives the **cognitive and context limits** that make that workflow necessary.

## Core claim (Troy)

LLMs generate plausible language sequences; they are **not** a substitute for engineering judgment. They work best as **aides to a rigorous process** — not as a way to produce more unreviewed output.

Subject matter expertise, scoped context, and explicit evaluation still matter — especially as problems grow beyond small, greenfield functions.

## “Lost in the Middle” → index-driven loading

Troy cites the [Lost in the Middle](https://arxiv.org/abs/2307.03172) finding: **larger context windows reduce retrieval accuracy**, and facts in the **middle** of a long prompt are easiest to miss.

**Framework response:**

| Troy recommendation | SDLC-SPDD mechanism |
|---------------------|-------------------|
| Narrow context to the relevant section | Tier 1 grounding (~fixed size) + Tier 2 on-demand only |
| Do not dump whole directories | `context-index.md`, `domain-index.md`, `session-index.md` — filter by area or keyword |
| Put critical facts where they are findable | Session brief + Framework Orientation at start; indexes newest-first |
| Bound growing history | `session-history.md` rotation; immutable per-session entries |

See [Bootstrap and index-based loading](context-loading-and-scaling.md#bootstrap-and-index-based-loading).

## Scoped, cohesive slices → analysis + code areas

Troy observes that LLM help fails when students paste entire codebases; effective use requires **cohesive code** and entering **only the slice that needs help**.

**Framework response:**

| Troy observation | SDLC-SPDD mechanism |
|------------------|---------------------|
| Isolate the relevant module | `/sdlc-spdd-analysis` — domain keywords → scoped file reads |
| Record scoped areas | `## Code Areas` in analysis artifact; `code-areas.md` registry |
| Reuse scope in later phases | Plan/architect/code load analysis Code Areas, not whole repo |
| Cross-session reuse | `index-spdd-analysis.sh` → `domain-index.md` + `context-index.md` (Kind: `analysis`) |

Fowler Step 3 (`/spdd-analysis`) and our `/sdlc-spdd-analysis` implement the same idea Troy describes informally.

## Specific, testable problems → REASONS + operations

Troy: LLMs do best when problems are **specific**, **limited in scope**, and have **clear success criteria**.

**Framework response:**

| Troy criterion | SDLC-SPDD mechanism |
|----------------|---------------------|
| Specific success criteria | REASONS **Requirements** (AC, DoD) |
| Limited scope | **Operations** — one approved step per `/sdlc-spdd-code` pass |
| Verifiable behavior | `/sdlc-spdd-api-test` (Fowler Step 5); review against canvas |
| Non-negotiable bounds | **Safeguards** and **Norms** sections |

## Three skill sets → lifecycle phases

Troy names three skills that matter *more* in an LLM-enabled world:

### 1. Investigative skills

Scope the problem; compare assumptions to ground truth.

| Framework support |
|-------------------|
| `/sdlc-spdd-analysis` — strategic scan before design |
| `/sdlc-spdd-resync-agent-session.sh` — canvas drift checks |
| Indexes — find prior work by area/keyword without linear history scan |
| Session briefs — explicit Work ID, phase, artifact status |

Investigation is **delivery work**, not overhead before “real” coding.

### 2. Evaluative skills

Choose among options using criteria for **this** situation; document trade-offs.

| Framework support |
|-------------------|
| `/sdlc-spdd-architect` — readiness gate (Ready For Coding / Needs Clarification / …) |
| `/sdlc-spdd-review` — compare implementation to all REASONS sections |
| REASONS **Approach** — strategy and accepted trade-offs recorded in the canvas |
| [On Code Coverage Tools](https://chelseatroy.com/2023/02/07/on-code-coverage-tools/) — treat metrics as **satisficing sentinels**, not optimizing scores → `quality-gates.md`, harness |

Engineers should record **optimizing vs satisficing** criteria in the canvas or progress log when choosing between options.

### 3. Innovation skills

Find where the status quo fails; solutions the “internet average” cannot produce.

| Framework support |
|-------------------|
| Human-led `/sdlc-spdd-retro` and `/sdlc-spdd-prompt-update` |
| Canvas captures **why**, not just **what** — durable for the next iteration |
| **Not automated** — the framework does not claim to replace judgment or invent novel architecture |

## Judgment stays human → confidence stack

Troy: models suggest **options**; they do not replace **judgment**. Verify outputs; you remain accountable.

**Framework response:**

| Troy principle | SDLC-SPDD mechanism |
|----------------|---------------------|
| Do not trust plausible text | Review + sync loops; behavior changes → prompt first |
| Chat is nondeterministic | [TESTING.md](../TESTING.md) confidence stack: CI for adapters/scripts, manual chat smoke for invocation |
| Expertise in when to trust LLMs | Grounding files + phase commands encode when **not** to code (plan, architect, analysis) |

## “Don't generate slop” → governed artifacts

Troy closes: use AI for a **more rigorous, compassionate, thoughtful** process — not to flood GitHub with unreviewed code.

**Framework response:**

- Versioned REASONS Canvas, analysis docs, reviews, sync logs (Fowler + SPDD)
- Prompt-first on behavior change; sync after accepted refactors
- Memory and indexes compound **decisions**, not chat transcripts

## What Troy does *not* provide

| Topic | Note |
|-------|------|
| REASONS Canvas / Fowler workflow | Use [SPDD compliance](spdd-compliance.md) for command mapping |
| Adapter install paths | Use [Cursor](cursor-usage.md), [Copilot](copilot-usage.md), [Claude](claude-usage.md) usage guides |
| UI hyperparameters (temperature, top_p) | Outside repo control; relevant for humans, not framework scripts |

## Quick reference map

```text
Troy concern                          → Primary framework doc / mechanism
─────────────────────────────────────────────────────────────────────────
Context too large / lost in middle    → context-loading-and-scaling.md, indexes
Need cohesive scoped slice            → /sdlc-spdd-analysis, code-areas.md
Need clear success criteria           → REASONS Canvas, /sdlc-spdd-api-test
Investigation undervalued             → analysis phase, session scripts
Evaluation / trade-offs               → /sdlc-spdd-architect, /sdlc-spdd-review
Innovation / judgment                 → human retro, prompt-update (not automated)
Verify don't trust                    → TESTING.md confidence stack, review/sync
Avoid slop                            → Fowler governed artifacts + capture/index loop
```

## Related reading

- [What can we expect of LLMs as Software Engineers?](https://chelseatroy.com/2025/07/14/what-can-we-expect-of-llms-as-software-engineers/) — Chelsea Troy (2025)
- [The Homework is the Cheat Code](https://chelseatroy.com/2025/05/14/the-homework-is-the-cheat-code-genai-policy-in-my-computer-science-graduate-classroom/) — scope/import/tradeoff failure modes when LLMs do all the work
- [On Code Coverage Tools](https://chelseatroy.com/2023/02/07/on-code-coverage-tools/) — satisficing vs optimizing metrics
- [Structured Prompt-Driven Development (Fowler)](https://martinfowler.com/articles/structured-prompt-driven/) — workflow this orchestrator implements
- [Context loading and scaling](context-loading-and-scaling.md#fowler-spdd-alignment)
- [SPDD compliance — Fowler mapping](spdd-compliance.md#fowler--openspdd-command-mapping)
