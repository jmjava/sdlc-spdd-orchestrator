# Vision: Uberorchbot gets work done *through* SDLC-SPDD

**Kind:** product / integration vision on the planning branch (not a paper, not an implementation)  
**Date:** 2026-09-10  
**Sibling plan:** [Kasana Agent Harness 2.0](kasana-agent-harness-2-0.md) (I0–I3)  
**Platform:** **Cursor Cloud Agents + Cloud Environments** are the runtime for all of this.  
**Decision:** Uberorchbot is a **dispatcher onto that platform**. SDLC-SPDD is the **process inside the environment**. `/sdlc-spdd-code` is the **inner loop** (Kasana I1). None of those three replaces the others.

## Source access

Intended repo: <https://github.com/jmjava/Uberorchbot>

This environment cannot read it (`gh` + clone → repository not found / 404). The vision below is inferred from the name, this orchestrator’s CLI, Cursor Cloud Agent/Environment mechanics, and the Kasana overlay. **Correct it against the real README when the repo is readable.**

Assumption: Uberorchbot decides *what* work to run and *which Cloud Agent to start*. It does not implement T## operations and it does not provision VMs of its own.

## The platform (this is the point)

Cursor already gives isolated machines that can claim a repo, install a toolchain, run an agent, and open a PR. **That is the platform.** We do not build a second agent farm.

| Cursor piece | Role in this system |
|--------------|---------------------|
| **Environment** | The machine image for a target (or this orchestrator): OS, `install`/`start`, secrets, egress, MCP allowlist, optional Guide/Neo4j, prebuilt **builds** so the next agent boots warm |
| **Environment build / snapshot** | Reproducible “SDLC-SPDD ready” baseline. `install` once per build; `start` per boot for daemons |
| **Cloud Agent** | One worker: one Work ID, **one SDLC phase** (or one T## in code), prompt = Resume Prompt from `sdlc.sh start` |
| **PR + branch** | How work leaves the pod (`cursor/…` branches, `ManagePullRequest` / GitHub) |
| **Automations** (optional) | Event hooks (issue labeled, PR comment) that tell Uberorchbot to enqueue a spawn |
| **Follow-up queue** | Human steers an in-flight phase without a new lifecycle |

This planning run is already that pattern: a Cloud Agent on `github.com/jmjava/sdlc-spdd-orchestrator`, booted from an environment build, writing on `cursor/kasana-harness-research-e0e2`.

```
Human / ticket / goal
        │
        ▼
┌──────────────────────────┐
│ Uberorchbot              │  enqueue · claim Work ID · pick env
│ (dispatcher only)       │  start Cloud Agent · watch · shelf
└────────────┬─────────────┘
             │  Cloud Agent API / dashboard spawn
             │  repo + environment + prompt = Resume Prompt
             ▼
┌──────────────────────────┐
│ Cursor Environment        │  snapshot/build: sdlc-engine, gh, tests
│ (platform machine)      │  secrets: GitHub, Jira, Guide (not in git)
└────────────┬─────────────┘
             │  checkout target revision
             ▼
┌──────────────────────────┐
│ SDLC-SPDD in that repo   │  canvas, gate_check, ledger, registry
│                          │  sdlc.sh next | gate | capture
└────────────┬─────────────┘
             │  Cloud Agent runs exactly one /sdlc-spdd-* command
             ▼
┌──────────────────────────┐
│ Code phase only          │  Kasana I1: verify, failing rule,
│ /sdlc-spdd-code overlay  │  repeat-stop, Files: vs git diff
└──────────────────────────┘
```

**Uberorchbot does not SSH, does not own Kubernetes workers for coding, and does not call the model to write product code.** It starts Cloud Agents against Environments that already know how to run SDLC-SPDD.

## Three layers (unchanged ownership)

| Layer | Owner | Job |
|-------|--------|-----|
| **What / who / when** | Uberorchbot | Queue, pick repo + Work ID, **start a Cloud Agent on the right Environment**, watch, escalate |
| **Where it runs** | Cursor Environment | Toolchain, secrets, builds; same env for every phase of that target |
| **How work is governed** | SDLC-SPDD in the **target** repo | Work ID, requirement, canvas, `gate_check`, ledger, registry |
| **How one code session behaves** | That Cloud Agent + `/sdlc-spdd-code` | Kasana overlay (I1) |

## What one cycle looks like on the platform

1. **Pick work.** `sdlc.sh list-work` / registry in the target clone (or a read-only status from the last agent). Claim `sdlc.sh claim <WORK-ID>`. Do not invent a FEAT from chat.
2. **Gate.** `sdlc.sh gate <phase> --work-id <ID>`. Fail → do not start a **code** Cloud Agent. Start analysis/plan/architect instead, or stop for a human.
3. **Start a Cloud Agent** on the target’s Environment (or this orchestrator’s env for framework work). Prompt is the **Resume Prompt** from `sdlc.sh start` — Work ID, phase, `/sdlc-spdd-*` command. One agent = one phase (code = one T##).
4. **The agent works in the pod.** Grounding files + retrieve + canvas. Code phase uses Kasana I1 once that overlay exists. It commits, pushes, opens/updates a PR — that is the Cloud Agent contract, not a custom Uberorchbot deployer.
5. **Capture.** `sdlc.sh capture` in-repo. Uberorchbot does not mark T## complete.
6. **Watch.** When the agent is idle / PR opened, Uberorchbot reads `next` again (new agent or follow-up). Same verify error twice → shelf, do not spawn a third code agent for that T##.
7. **Sunset.** A later Cloud Agent runs `/sdlc-spdd-sunset` when the Work ID is actually finished.

## Environment as the SDLC-SPDD platform

Per **target** application (and a separate env for this orchestrator):

| Concern | Put it in |
|---------|-----------|
| Python, `sdlc_engine`, git, gh, language toolchain, test runners | Environment **build** / `install` |
| Guide + Neo4j, app servers | `start` or `terminals` (processes; not `install`) |
| Jira / GitHub / Guide tokens | Environment **secrets**, never `environment.json` |
| Extra repos (e.g. framework + app) | `repositoryDependencies` / environment `repos` |
| MCP (`spdd_*` only if Guide is live) | `mcpServerAllowlist` |
| Network | egress policy on the environment |

Prefer a **repo-managed** `.cursor/environment.json` on each target so branches and PRs get the same platform. Dashboard personal envs are fine for experiments; they are not the team platform.

This orchestrator today: personal/DB-managed env, no committed `environment.json`. A later U-step can add a repo-managed env so Cloud Agents always boot “SDLC-SPDD ready.”

## Contract Uberorchbot must speak

**Cursor:** start Cloud Agent (repo URL, environment, branch or base, prompt). Watch status, PR, follow-up queue. Do not reimplement the pod.

**SDLC (inside the agent):** `sdlc.sh` — `next`, `status --json`, `list-work`, `claim`, `shelf`, `resume`, `gate`, `start`, `capture`, `accept`. `--force` on gate is human-only.

Do **not**:

- Call a model from Uberorchbot to write application code.
- Reimplement `gate_check` or the canvas.
- Skip phases because “the bot is sure.”
- Open PRs against `embabel/guide`.
- Treat mocked Guide HTTP as the graph.
- Stand up a parallel “agent runtime” that duplicates Cloud Agents.

## Fit with Kasana I0–I3

| Kasana | On this platform |
|--------|------------------|
| I0 overlay rule | Inner loop is `/sdlc-spdd-code` **inside the Cloud Agent**, not a Python class in Uberorchbot |
| I1 verify / Files: / stop | The **code-phase Cloud Agent** obeys the command. Uberorchbot refuses to start another code agent after stop/shelf |
| I2 review Files: vs diff | Uberorchbot starts a **review-phase** Cloud Agent |
| I3 optional hooks | Target Environment `install`/`start` or target CI — still not Uberorchbot |

## Suggested work (planning only)

| ID | What | Where |
|----|------|--------|
| **U0** | This vision: Cloud Agents + Environments are the platform | this file |
| **U1** | Read Uberorchbot when accessible; map real modules; strike wrong assumptions | Uberorchbot + amendment here |
| **U2** | **Platform env:** repo-managed environment (or documented dashboard env) per target + this orchestrator: `install` has `sdlc-engine`; builds enabled so spawns are cheap | `.cursor/environment.json` / dashboard; not application source |
| **U3** | Uberorchbot **only** starts Cloud Agents: prompt = Resume Prompt, env = U2, one phase per agent | Uberorchbot |
| **U4** | Dispatcher uses `gate` before starting a code agent; maps agent idle/PR → `next` | Uberorchbot |
| **U5** | After Kasana I1: code-agent prompts include the four I1 bullets (or the regenerated `/sdlc-spdd-code` spec is enough) | this repo I1, then U3 |

U2 is the first *platform* work in *this* repo if we want dogfood: a committed environment so Cloud Agents always have the CLI. U3–U4 live in Uberorchbot.

## Claims allowed

- We **plan** to run SDLC-SPDD and the Kasana code overlay **on Cursor Cloud Agents/Environments**, with Uberorchbot as the dispatcher.
- Uberorchbot source was not readable here; module names inside that repo are not claimed.
- No change to DOC-001/002, `gate_check`, or command specs in this step.

## See also

- [Kasana integration plan (I0–I3)](kasana-agent-harness-2-0.md)
- [Workflow sequence](../workflow.md)
- [Session prompt standard](../session-prompt-standard.md) — Resume Prompt is the Cloud Agent prompt
- [Issue sync and branching](../issue-sync-and-branching.md)
- [Design decisions](../design-decisions.md)
- Cursor: [Cloud Agent setup](https://cursor.com/docs/cloud-agent/setup), [environment schema](https://cursor.com/schemas/environment.schema.json)
