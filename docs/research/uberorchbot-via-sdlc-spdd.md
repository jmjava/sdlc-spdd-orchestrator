# Vision: Uberorchbot gets work done *through* SDLC-SPDD

**Kind:** product / integration vision on the planning branch (not a paper, not an implementation)  
**Date:** 2026-09-10  
**Sibling plan:** [Kasana Agent Harness 2.0](kasana-agent-harness-2-0.md) (I0–I3)  
**Decision:** Uberorchbot is a **client of SDLC-SPDD**, not a second lifecycle and not a Python `AgentHarness`.

## Source access

Intended repo: <https://github.com/jmjava/Uberorchbot>

This environment cannot read it (`gh` + clone → repository not found / 404). The vision below is inferred from the name, this orchestrator’s CLI, and the Kasana overlay. **Correct it against the real README when the repo is readable.** Do not treat guessed Uberorchbot internals as facts.

Assumption used here: Uberorchbot is a **meta-orchestrator** — it decides *what* work to run, *where* (which repo), and *which agent* to spawn. It does not itself implement T## operations.

## Decision (integrate, not replace)

Same rule as Kasana, one layer up:

| Layer | Owner | Job |
|-------|--------|-----|
| **What / who / when** | Uberorchbot | Queue, decompose goals, pick repo + Work ID, spawn one agent, watch, escalate |
| **How work is governed** | SDLC-SPDD in the **target** repo | Work ID, requirement, canvas, `gate_check`, ledger, registry |
| **How one code session behaves** | Host coding agent + `/sdlc-spdd-code` | Kasana overlay (I1): verify-before-done, show failing rule, stop on repeat, `Files:` vs diff |

Uberorchbot **gets work done via SDLC-SPDD** means: every unit of coding work is a Work ID that already exists in the target; the bot only drives `sdlc.sh` / `sdlc-engine` and one `/sdlc-spdd-*` command per spawn. It does not invent a parallel SPARC/ReAct workflow.

```
Human / ticket / goal
        │
        ▼
┌─────────────────────┐
│    Uberorchbot      │  queue · claim · spawn · watch · shelf
│    (dispatcher)     │  never writes product code
└──────────┬──────────┘
           │  sdlc.sh next | claim | gate | start | capture
           ▼
┌─────────────────────┐
│  Target repo        │  requirement + canvas + ledger
│  SDLC-SPDD install  │
└──────────┬──────────┘
           │  one phase per spawn
           ▼
┌─────────────────────┐
│  Cloud / IDE agent  │  /sdlc-spdd-<phase>
│  (Kasana inner loop │  only inside /sdlc-spdd-code
│   on code phase)    │
└─────────────────────┘
```

## What “done via SDLC-SPDD” looks like in one cycle

1. **Pick work.** Uberorchbot reads `sdlc.sh list-work` / registry. It claims an existing Work ID (`sdlc.sh claim <WORK-ID>`). It does not invent a FEAT from chat.
2. **Ask what’s next.** `sdlc.sh next` (and `gate <phase>`) is the scheduler. If `gate` fails, **do not spawn `/sdlc-spdd-code`**. Spawn analysis / plan / architect instead, or stop and tell a human.
3. **Open a session.** `sdlc.sh start` → paste the Resume Prompt into the spawned agent. That prompt already names the Work ID, phase, and command.
4. **One spawn = one phase (or one T## in code).**  
   - analysis / plan / architect / api-test / review / retro / sync → the matching `/sdlc-spdd-*` command.  
   - code → `/sdlc-spdd-code` + Kasana I1 once that overlay exists.
5. **Collect evidence.** Agent runs `sdlc.sh capture`. PR exists if code changed. Uberorchbot does not mark the T## complete; the code command’s exit rules do (I1).
6. **Re-read `next`.** Loop. Same error twice on the same verify → shelf + escalate (Kasana I1.3), not a third spawn of the same T##.
7. **Close.** `/sdlc-spdd-sunset` / `sdlc.sh sunset` when the Work ID is actually finished — Uberorchbot may *invoke* that command; it does not invent a sunset format of its own.

That is the whole vision: **Uberorchbot is the outer loop; SDLC-SPDD is the process; the coding agent is the inner loop.**

## Contract Uberorchbot must speak

Stable CLI (target install: `./sdlc-spdd/scripts/sdlc.sh`; this repo: `./scripts/sdlc.sh`):

| Uberorchbot needs | Command |
|-------------------|---------|
| What’s in flight | `next`, `status --json`, `list-work`, `team` |
| Take / pause work | `claim`, `shelf`, `resume` |
| May I enter this phase? | `gate <phase> --work-id <ID>` — **hard stop on fail** (`--force` is human-only) |
| Session brief | `start` (Resume Prompt) |
| Memory | `capture` after each spawn; `accept` at retro/sync |
| Issues | `issues` / existing Jira-GitHub link — do not bypass the requirement doc |

Do **not** have Uberorchbot:

- Call a model to write application code.
- Reimplement `gate_check` or the REASONS canvas.
- Skip phases because “the bot is sure.”
- Open PRs against `embabel/guide`.
- Treat mocked Guide HTTP as the graph.

## Fit with Kasana I0–I3

| Kasana step | Who runs it when Uberorchbot is in front |
|-------------|------------------------------|
| I0 overlay rule | Already: inner loop is `/sdlc-spdd-code`, not a new class |
| I1 verify / Files: / stop | The **spawned code agent** obeys the code command. Uberorchbot only refuses to re-spawn the same T## after a stop/shelf |
| I2 review Files: vs diff | Uberorchbot may spawn `/sdlc-spdd-review` as the next phase; it does not parse diffs itself |
| I3 optional hooks | Still a target-repo concern, not the bot |

## Suggested work after this vision (still planning)

Not scheduled as Work IDs until promoted. Order:

| ID | What | Where |
|----|------|--------|
| **U0** | This vision + access note | this file (done on the planning branch) |
| **U1** | When Uberorchbot is readable: map its real modules onto the table above; strike wrong assumptions | Uberorchbot repo + a short amendment here |
| **U2** | Thin client: Uberorchbot shells `sdlc.sh next/gate/claim/start` against an installed target | Uberorchbot; **no** copy of `WorkflowEngine` |
| **U3** | Spawn policy: one Cursor Cloud (or IDE) agent per phase, prompt = Resume Prompt only | Uberorchbot + [session prompt standard](../session-prompt-standard.md) |
| **U4** | After I1 lands: code spawns must include the four I1 bullets (verify, failing rule, repeat-stop, `Files:`) | depends on Kasana I1 |

U2–U4 belong in Uberorchbot (or a small glue repo). This orchestrator keeps owning canvas, gates, and adapters.

## Claims allowed

- We **plan** for Uberorchbot to finish work by driving SDLC-SPDD, not by replacing it.
- This file is a vision. The Uberorchbot source was not readable here, so module names inside that repo are not claimed.
- No change to DOC-001/002, `gate_check`, or command specs in this step.

## See also

- [Kasana integration plan (I0–I3)](kasana-agent-harness-2-0.md)
- [Workflow sequence](../workflow.md)
- [Session prompt standard](../session-prompt-standard.md)
- [Issue sync and branching](../issue-sync-and-branching.md)
- [Design decisions](../design-decisions.md) — adapters, not a compiled agent runtime
