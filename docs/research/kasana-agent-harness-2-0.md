# Related research: Kasana Agent Harness 2.0

**Kind:** product / integration research **and integration plan** (not a paper, not an evaluation result)  
**Date:** 2026-09-10  
**Decision:** **Integrate.** Overlay Kasana’s loop onto `/sdlc-spdd-code`. Do **not** replace this repo with a Python `AgentHarness`.  
**Local session:** `LOCAL-001-kasana-harness-research` (plan is in this file; promote to a DOC/FEAT when implementation starts)  
**Does not change yet:** DOC-001 / DOC-002 freeze, `gate_check` semantics, command specs, or application source — those move in the plan below, not in this note’s first commit

## Source

Sachin Kasana, *How to Build an AI Agent Harness 2.0 and Engineer Better Than 99% of Developers*, CodeToDeploy / Medium, 5 Sep 2026 (~9 min).

- Canonical: <https://medium.com/codetodeploy/how-to-build-an-ai-agent-harness-2-0-and-engineer-better-than-99-of-developers-028e4fc01b50>
- Author friend-link (full text): <https://medium.com/codetodeploy/how-to-build-an-ai-agent-harness-2-0-and-engineer-better-than-99-of-developers-028e4fc01b50?sk=e074eeb6c9326fff585809c4986ecef4>

This note **summarizes** the argument and maps it onto SDLC-SPDD. It is not a reprint of the article.

## What the article claims

A coding agent can compile, pass tests, open a clean PR, and still be wrong: it bypasses the persistence layer, edits a file it should not touch, skips a test, introduces a security issue, or ignores an architecture decision. Nothing crashed. The agent did what it thought was correct.

Kasana’s diagnosis: the usual upgrades (smarter model, bigger prompt, bigger window) do not fix that. The missing piece is the **environment around the model**. He calls that environment an **agent harness**.

Weak loop:

```
Prompt → Model → Code
```

Harness loop:

```
Task → Context → Agent → Tools → Code → Verification → Feedback ↺
```

Six layers around the agent: **context, tools, constraints, memory, execution, verification**. The model reasons; the harness supplies discipline. The question to optimize is not “how smart is this agent?” but “what happens when it is wrong?”

The article then walks 18 engineering steps from `AGENTS.md` through tools, retrieval, memory files, verification as a gate, a retry loop with a cap, git-diff allowlists, plan-before-write, multi-layer checks, and a small `AgentHarness` class.

## Object difference (read this first)

Kasana and SDLC-SPDD are **not the same object**. Mixing them in DOC-002’s novelty matrix would be a category error. Leave the freeze alone.

| | Kasana Harness 2.0 | SDLC-SPDD |
|--|---------------------|-----------|
| Research / product object | A **coding-agent execution runtime**: tool loop, verify, recover, stop | A **repository-native process model**: REASONS canvas + SDLC phases + retrievable stores |
| “Harness” means | Code that wraps one model session (`decide → execute → verify`) | Playbooks, phase gates, retrieval budgets, adapters over Cursor / Copilot / Claude |
| Success | The agent’s patch is independently verified and bounded | Intent, compliance, and context load are **observable** (C-DRIFT / C-COMPLY / C-CONTEXT) |
| Already decided here | — | Not a compiled agent runtime ([design decisions](../design-decisions.md)) |

They **compose**. Kasana is what a well-behaved **code-phase** agent would do *inside* one `/sdlc-spdd-code` operation. SDLC-SPDD is the lifecycle *around* that operation (analysis → plan → architect → code → api-test → review → retro → sync).

```
Developer
    ↓
SDLC-SPDD process harness (phases, canvas, retrieve, gate_check)
    ↓
Code-phase agent (Cursor / Copilot / Claude)  ← Kasana’s loop would live here
    ↓
Repo + tests + review artifacts
```

**Adopt the ideas that tighten code-phase discipline. Do not replace SDLC-SPDD with a Python `AgentHarness` class.**

## What “inside `/sdlc-spdd-code`” means

That sentence is the integration rule. Two halves:

1. **His loop lives inside `/sdlc-spdd-code`.** Kasana’s `Task → Context → Act → Verify → Feedback ↺` is one coding session for **one approved T##**. The host assistant (Cursor / Copilot / Claude) already is the model loop. We do not reimplement `agent.decide()` in Python. We specify **when that session may start, what it may touch, what “done” means, and when it must stop.**
2. **We do not add `class AgentHarness`.** `sdlc_engine` is a process SUT (`gate_check`, retrieve, capture). A first-party loop that calls the model would duplicate the host, break the three-assistant adapter model, and change the research object from process observability to agent competence. That is already rejected in [design decisions](../design-decisions.md) (“templates and scripts, not a compiled CLI or agent runtime”).

Who owns which layer:

| Kasana layer | Who owns it here | Where it is today | Not |
|--------------|------------------|-------------------|-----|
| Task | Canvas Operations | One T## selected in `/sdlc-spdd-code` | A free-form “build the feature” prompt |
| Context | Command + retrieve | Gate → read canvas → `context retrieve --kind pitfall` | Dumping the repo into the window |
| Tools | Host IDE | Cursor/Claude tools; we constrain *scope* (`Files:`, one op), not the tool vocabulary | A Python tool registry in `sdlc_engine` |
| Constraints | Canvas + command | Norms/Safeguards as instructions; `Files:` must be named; readiness gate | An in-engine allowlist that the model cannot see |
| Memory | Ledger | Pitfall retrieve at start; `sdlc.sh capture` at end | `agent-memory/failures.md` beside the engine |
| Execution | Host agent | Steps 6–12 of the code command (implement, no extras) | `WorkflowEngine.run_agent()` |
| Verification | Split | **Enter** code: `gate_check`. **Leave** code: command says “add tests” (instruction). Later phases (api-test, review) are other commands | `verify()` inside `gate_check` (wrong layer — gate is enter-phase) |
| Feedback / retry | Host agent | Same chat turn retries; next session sees pitfalls | `for attempt in range(3)` in Python |
| Stop | Missing | No repeated-error cap in the command | Engine-level `MAX_ATTEMPTS` |

Map onto the existing code command (`spec/commands/lifecycle-code.spec.md`):

```
gate_check(code)           → may this session start?
read canvas + retrieve     → context (not dump)
readiness + select T##    → task
implement + Norms/Safeguards → act  (host tools)
add tests + summarize      → verify  (today: instruction)
capture                    → memory
```

The overlay is **command required-behavior**, not a new package. If we adopt further, we add steps to that spec (then regenerate adapters): run the operation’s validation commands before marking the T## complete; on failure, return the output plus the Norm/Safeguard; stop after the same verify error twice; optionally assert `git diff --name-only` ⊆ `Files:` plus tests. The host still retries. The engine still does not call a model.

`gate_check` stays an **enter-phase** predicate. Putting Kasana’s `verify()` there would mean “you cannot *start* coding until the patch is green,” which is backwards. Verify-before-done belongs in the code command’s **exit** condition. Path allowlist vs `Files:` belongs in code-command exit or in `/sdlc-spdd-review`, not in a new runtime.

## Layer map: match, partial, gap

Status key: **match** = we already do this as designed · **partial** = same intent, still mostly prompt/advisory · **gap** = we do not have it · **reject** = do not copy.

| Kasana step | Article move | SDLC-SPDD today | Status | Adopt? |
|-------------|--------------|-----------------|--------|--------|
| 1. Context / `AGENTS.md` | Project rules as files the agent must read | REASONS **Norms + Safeguards**; Tier 1 grounding (`.cursor/rules/sdlc-spdd.mdc`, `CLAUDE.md`, Copilot instructions); stack playbooks | **match** | Keep canvas as the contract. Do not add a second `AGENTS.md` that can drift from Norms. |
| 2. Narrow tools | Allowlisted tools (`read_file`, `apply_patch`, `run_tests`, …) | Host IDE tools (Cursor/Claude) are broad. We constrain *what to do* (one T## operation, `Files:` lines), not the tool vocabulary | **partial** | Do not invent our own tool runtime. Optionally document “preferred tools” in the code command (search before write, run project tests). |
| 3. Retrieve, don’t dump | Task → keywords → relevant files + architecture + rules | [Context loading](../context-loading-and-scaling.md): contracts read directly; `sdlc-engine context retrieve`; per-phase budgets; never bulk-read the ledger | **match** | Already stronger than the article’s `rg` sketch (Work ID, kind, Guide `spdd_*`). |
| 4. Memory ≠ context | Persist `decisions.md` / `failures.md` | `sdlc.sh capture` → staged JSONL → `accept` into `lessons.jsonl`; kinds `decision` / `pitfall` / `pattern`; Guide + SQLite projections | **match** | Already the storage-v3 model. Kasana’s flat markdown files are a weaker store. |
| 5. Instruction vs constraint | “Write tests” vs “not done until tests pass” | Mix. **Enforced:** canvas exists, Ready For Coding, each T## has `Files:`, review minima, retro lesson before sync. **Advisory:** tests updated, architect review, canvas synced (`ADVISORY_GATES` in `engine/src/sdlc_engine/phases.py`) | **partial** | Highest-value adopt: promote selected advisories toward constraints *without* claiming C-DRIFT reduction. |
| 6. Agent loop | `for attempt in range(3): decide → execute → verify` | No in-engine retry loop. The host agent retries; `/sdlc-spdd-code` is one operation per session; `gate_check` is enter-phase, not “patch is green” | **gap** | Do not add a model loop to `sdlc_engine`. Strengthen the **code command** to refuse “done” until project verify commands the canvas names have been run. |
| 7. Show the failure | Return the violated rule, not “try again” | Review/api-test artifacts and ledger pitfalls; not an automatic architecture-check string fed back into the same turn | **partial** | Adopt as command text: when verification fails, paste the failing command output + the Safeguard/Norm it maps to. |
| 8. Hooks | Pre-commit lint / typecheck / test | CI + `validate-reasons-canvas.sh` + `gate_check`; target-app pre-commit is the *installed project’s* job, not the orchestrator’s | **partial** | Document as an install-time *optional* hook recipe. Do not force a hook into every target. |
| 9. Recovery | Feed error + attempt number back; don’t restart from zero | Retro + pitfall retrieve on the *next* session; same-session recovery is the host agent | **partial** | Match Kasana’s “next run can learn” via retrieve `--kind pitfall`. Same-turn recovery stays with the host. |
| 10. Cap retries | `MAX_ATTEMPTS`, stop on repeated error hash | No attempt counter in the engine. Unbounded Cursor retries are possible | **gap** | Adopt as **operator guidance** in the code/review commands (stop after N identical verify failures; shelf / prompt-update). Engine-level caps would be a later FEAT and a new runtime object — out of scope until promoted. |
| 11. Git awareness | `git diff`; rollback if forbidden paths (`.env`, `generated/`, `infrastructure/`) | Canvas `Files:` must be *named* (FEAT-016). Hunk-level “diff only touches those paths” is still a human/TEST-002 remainder | **gap** | Strong adopt candidate: optional `gate` or review check that `git diff --name-only` is a subset of the active operation’s `Files:` plus test paths. |
| 12. Plan before execute | Plan JSON of files/changes, reject before writes | **Architect phase** + Operations with files and validation steps; `/sdlc-spdd-code` implements one approved T## | **match** | Our plan is richer (REASONS). Do not add a parallel JSON planner. |
| 13. Multi-layer verification | Syntax / behavior / architecture | Phases: typecheck/lint in the *target* repo; api-test; review vs all REASONS sections; `safeguards_checked` is labeled enforced but is a review-minima *mention*, not a static architecture checker | **partial** | Keep layered *phases*. Adopt an optional **architecture check** only when a target encodes Norms as executable rules. |
| 14–15. Harness 2.0 / minimal class | One Python wrapper: context → action → verify → memory | `WorkflowEngine.gate_check` + adapters + retrieval. Explicitly not an LLM loop ([engine SUT](../../sdlc-spdd/docs/research/engine-sut.md)) | **reject that shape** | Integrate the *loop semantics* in `/sdlc-spdd-code`. Do not add `class AgentHarness`. |
| 16. Developer designs the environment | Developer writes the harness; agent writes code | Developer (and architect phase) writes the canvas; agent implements one operation | **match** | Same mindset, different artifact (canvas vs Python class). |
| 17. Prefer System B | Good model + focused context + tools + memory + verify + recovery + guardrails | Same bet: adapters + retrieve + gates over “just use a bigger model” | **match** | Already the operating model. |
| 18. Correctable agent | Detect, explain, recover, prevent repeat, roll back | Detect/explain: review + ledger. Prevent repeat: retrieve pitfalls. Rollback: git, not harness-owned | **partial** | Adopt rollback-on-forbidden-path (row 11) and “stop on repeated verify hash” (row 10) as the missing correctability pieces. |

## Where we already match (do not rebuild)

1. **Retrieve, don’t dump** — per-phase budgets, ledger retrieve, Guide `spdd_*`, no bulk `lessons.jsonl`.
2. **Memory as a store** — stage-then-accept, kinds, three storage modes. Stronger than `agent-memory/*.md`.
3. **Plan before code** — analysis → canvas → architect readiness → one T##.
4. **Layered verification as a lifecycle** — api-test, review, retro, sync, not a single `npm test`.
5. **Developer designs the environment** — canvas Norms/Safeguards are the project’s constraint language.

Kasana would call much of SDLC-SPDD a harness. We already built the *process* harness. The holes are in **turning remaining instructions into constraints during the code phase**.

## Where we differ (keep the difference)

| Difference | Why keep it |
|-----------|-------------|
| Process model vs agent runtime | DOC-001’s object is observability of stores, not SWE-bench agent competence. A Python decide/execute loop would change the SUT. |
| Canvas vs `AGENTS.md` | One versioned REASONS contract per Work ID. A repo-global `AGENTS.md` duplicates Norms and will drift. |
| Phase gates vs inner retry loop | `gate_check` validates *entering* a phase. It does not run the model. Host agents already retry. |
| Advisory gates | `tests_updated` and `canvas_synced` stay advisory until we have a machine check that is not token-grep theater. Promoting them without a real checker would fake C-COMPLY. |
| No forced pre-commit on targets | Targets bring their own CI. Orchestrator install must stay non-overwrite-by-default. |
| Guide is fork-only | Nothing in this note implies an Embabel upstream PR. |

## Decision (not a rejection)

**We are integrating Kasana.** The earlier “reject” language applied to **one shape** (a Python class that *is* the agent loop and replaces this repo). It did **not** mean “skip the article.”

| Verdict | What |
|---------|------|
| **Yes — integrate** | Verify-before-done, show the failing rule, cap repeated failures, path allowlist vs `Files:`, optional target hooks |
| **Already done — keep** | Retrieve, ledger memory, plan-before-code, phase-layered verification, canvas as contract |
| **No — only this shape** | `class AgentHarness` that calls the model; a second `AGENTS.md`; folding the whole SDLC into one ReAct loop; claiming reduced drift; Embabel upstream |

Rule of thumb once integrated: **instructions live in Norms; constraints are whatever `gate_check`, CI, or a named verify command can fail.** `gate_check` stays **enter-phase**. Kasana’s `verify()` is a **code-command exit** condition.

## Integration plan

This is the plan. Implementation is the next Work ID(s), not this research file’s first commit.

### I0 — Record the decision (this file)

- Index the article under `docs/research/`.
- Freeze the overlay rule: loop lives in `/sdlc-spdd-code`; engine does not call a model.
- **Status:** done in this PR.

### I1 — Code-command overlay (first implementation)

**Where:** `spec/commands/lifecycle-code.spec.md` → regenerate Cursor / Copilot / Claude adapters ([command-spec workflow](../contributing-command-specs.md)). Optionally mirror a short “instruction vs constraint” line in `harness/quality-gates.md` (and its template) so targets see the same rule.

**Add as required behavior of `/sdlc-spdd-code` (exit of one T##):**

1. Run the **validation steps named on that operation** (canvas Operations). If none, run the project’s documented test/lint/typecheck commands when they exist.
2. On failure: do **not** mark the T## complete. Return the command output **and** the Norm/Safeguard it violates. The host may retry in the same session.
3. If the **same** verify command fails twice with the same error, **stop**. Recommend `/sdlc-spdd-prompt-update` or shelf. Do not loop forever.
4. After edits: `git diff --name-only` should stay within the active T## `Files:` plus test paths. If it does not, do not mark complete; restore or drop the extra files (host `git checkout` / unstage — not a new engine API).

**Does not change:** `WorkflowEngine.gate_check` enter-phase semantics, DOC-001/002 freeze, no Python model loop.

**Done when:** `/sdlc-spdd-code` adapters include the four bullets; `generate-command-adapters.sh --check` and `validate-command-adapters.sh` pass.

### I2 — Review / Files: machine check (second implementation)

**Where:** `/sdlc-spdd-review` and/or a small helper used by review (not `gate_check` enter-code). Completes the human remainder of FEAT-016: the `Files:` line exists today; the **diff** is not yet checked.

**Add:** review reports fail (or a named warning that cannot be “Result: pass”) when the Work ID’s uncommitted or PR diff includes paths outside the coded operations’ `Files:` plus tests.

**Caution:** this is closer to C-COMPLY. Needs a promoted Work ID and canvas. Do **not** silently add it to `ENFORCED_GATES` / `gate_check(code)`.

**Done when:** a documented check compares diff paths to `Files:`; review command tells the agent to run it.

### I3 — Optional target hook recipe (docs)

**Where:** `docs/maintaining-your-project.md` (or a short subsection). A copy-paste pre-commit / CI snippet (lint, typecheck, tests). Install does **not** force the hook onto every target.

**Done when:** maintainers can opt in without an orchestrator-owned git hook.

### Order and what “done” looks like

```
I0 this note (done)
    → I1 code-command overlay     ← next coding work in *this* repo
    → I2 review Files: vs diff
    → I3 optional hook recipe

Uberorchbot does not replace I1–I3. Cursor Automations (or a human) start Cloud Agents that run them; the Uberorchbot plugin is opt-in behavior inside the VM: see [Uberorchbot via SDLC-SPDD](uberorchbot-via-sdlc-spdd.md) (U0–U5). The platform is Cursor Environments + Cloud Agents, not a second farm. Native Automation self-chaining is out of scope.
```

Promote `LOCAL-001-kasana-harness-research` (or a new DOC/FEAT) before I1 so command-spec edits have a Work ID. I1 is one operation if kept to the four command bullets; I2 is a second Work ID because it may touch review minima.

### Out of plan (still not doing)

- A first-party `class AgentHarness` that calls the model.
- Replacing REASONS or the 15-step workflow with one ReAct loop.
- Repo-global `AGENTS.md` as a second contract.
- Architecture AST checkers as a framework default (Prisma-in-controller). Encode in canvas Norms; run them only if the **target** already has ArchUnit / import-linter / equivalent.
- Claiming this article as academic novelty or as evidence of reduced drift.
- Any PR against `embabel/guide`.

## Claims allowed

- **Decision is integrate**, via `/sdlc-spdd-code` overlay (I1 → I2 → I3).
- Kasana’s article is a useful **coding-agent harness** checklist; SDLC-SPDD already has the process-level analogue.
- The **only** rejected shape is a Python `AgentHarness` / replacing the lifecycle — not the ideas.
- This note is **not** a DOC-002 matrix row, not a C-DRIFT result, and not a reason to open a PR against `embabel/guide`.

## See also

- [Uberorchbot via SDLC-SPDD](uberorchbot-via-sdlc-spdd.md) — Cloud Agents + Environments are the platform; Automations are the loop; Uberorchbot is plugin policy; this overlay is the code-phase inner loop inside those agents
- [Related-work and novelty (DOC-002)](../../sdlc-spdd/docs/research/related-work-and-novelty.md) — frozen positioning; coding agents are a different research object
- [Context loading and scaling](../context-loading-and-scaling.md)
- [Quality gates](../../sdlc-spdd/harness/quality-gates.md)
- [Design decisions](../design-decisions.md)
- [Engine SUT (REF-001)](../../sdlc-spdd/docs/research/engine-sut.md)
