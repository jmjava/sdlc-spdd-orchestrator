# Vision: SDLC-SPDD on Cursor Cloud Agents, with Uberorchbot as plugin policy

**Kind:** product / integration vision (not a paper, not a finished product)  
**Date:** 2026-09-10  
**Amended:** 2026-09-10 (U1 — read `jmjava/Uberorchbot` `main`; plugin-only since 2026-08-02)  
**Sibling plan:** [Kasana Agent Harness 2.0](kasana-agent-harness-2-0.md) (I0–I3)  
**Platform:** **Cursor** is the runtime — **local Agent chat** and **Cloud Agents / Environments**.  
**Decision:** Local chat is the interactive path. Cursor Automations are the unattended event-triggered loop. Uberorchbot is an **opt-in plugin** (skills, rules, commands) for **both**. SDLC-SPDD in the **target repo** is the process and state authority. `/sdlc-spdd-code` is the **inner loop** (Kasana I1). None of those replaces the others.

## Source access (U1)

Repo: <https://github.com/jmjava/Uberorchbot> — **readable.** Active product is documented in `SWITCH.md`, `README.md`, and `docs/SETUP.md`.

`main` is **plugin-only**. It ships `cursor-plugin/` (`jmjava-lab-automations`): rules (`cloud-agent-contract`, `pr-quality-bar`), finder skills, and a few commands. There is **no** dispatcher service, Cloud Agent spawner, run database, or `@cursor/sdk` worker on `main`.

The Spring control plane, dashboard, and local worktrees live only on `archive/main-lab-control-plane`. Do not revive that stack.

The 2026-09-10 draft assumed Uberorchbot was a service that claims work, picks an Environment, starts Cloud Agents, watches them, and shelves failures. **That assumption is false on current `main`.** This note replaces it.

## The platform (this is the point)

Cursor already runs the same agent loop **locally** (Agent chat on your checkout) and **in the cloud** (isolated VM, Environment, optional Automation). **That is the platform.** We do not build a second agent farm. Prove a skill in local chat before scheduling it. Cloud Environments still matter for unattended runs; they are not required for a local SDLC session.

| Cursor piece | Role in this system |
|--------------|---------------------|
| **Environment** | The machine image for a target (or this orchestrator): OS, `install`/`start`, secrets, egress, MCP allowlist, optional Guide/Neo4j, prebuilt **builds** so the next agent boots warm |
| **Environment build / snapshot** | Reproducible “SDLC-SPDD ready” baseline. `install` once per build; `start` per boot for daemons |
| **Local Agent chat** | Interactive worker on the operator’s checkout. Same Work ID, one phase, same `sdlc.sh` / `/sdlc-spdd-*` contract. First place to prove a skill |
| **Cloud Agent** | Isolated worker: one Work ID, **one SDLC phase** (or one T## in code). Prompt is the Resume Prompt from `sdlc.sh start` plus the Uberorchbot `sdlc-session` skill when that skill is installed |
| **PR + branch** | How work leaves the pod (`cursor/…` branches, GitHub) |
| **Automations** | The **loop**: schedule, PR, CI, label, webhook, or other supported events start a **configured** Cloud Agent. Prompt, repo, model, and Environment are fixed at Automation save time |
| **Subscriptions** | Same-agent follow-up on matching CI/review events. They keep conversation context. They do **not** spawn a new phase agent |
| **Follow-up queue** | Human steers an in-flight phase without a new lifecycle |

```
Human / ticket / goal
        │
        ├──────────────────────────────┐
        ▼                              ▼
┌──────────────────┐         ┌──────────────────────────┐
│ Local Agent chat │         │ Cursor Automations       │
│ (interactive)    │         │ (unattended cloud loop)  │
└────────┬─────────┘         └────────────┬─────────────┘
         │                                │ Cloud Agent + Environment
         └────────────┬───────────────────┘
                      ▼
┌──────────────────────────┐
│ Uberorchbot plugin        │  same opt-in sdlc-session skill on both paths
│                          │  finders still work on repos without SDLC
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ SDLC-SPDD in that repo   │  canvas, gate_check, ledger, registry
│                          │  sdlc.sh next | gate | start | capture
└────────────┬─────────────┘
             │  exactly one /sdlc-spdd-* command
             ▼
┌──────────────────────────┐
│ Code phase only          │  Kasana I1: verify, failing rule,
│ /sdlc-spdd-code overlay  │  repeat-stop, Files: vs git diff
└──────────────────────────┘
```

**Uberorchbot does not SSH, does not own Kubernetes workers, does not call a model to write product code, and does not start agents from application code.** A human in local chat, or a Cursor Automation in the cloud, starts a run. The plugin shapes what the agent does *after* it starts. Local chat does not need a Cloud Environment.

## Four layers (corrected ownership)

| Layer | Owner | Job |
|-------|--------|-----|
| **When a run starts** | Local Agent chat, or Cursor Automations | Interactive prompt, or a configured event with a fixed cloud prompt / repo / Environment |
| **Where it runs** | Local checkout, or a Cursor Environment | Local uses the operator machine. Cloud uses toolchain, secrets, builds |
| **How the agent behaves** | Uberorchbot plugin (opt-in SDLC skill) | Gate-before-code, one phase, capture, no invented FEAT |
| **How work is governed** | SDLC-SPDD in the **target** repo | Work ID, requirement, canvas, `gate_check`, ledger, registry |
| **How one code session exits** | Local or cloud agent + `/sdlc-spdd-code` | Kasana overlay (I1) |

## What one cycle looks like on the platform

1. **Pick work.** An existing Work ID — from the canvas, issue, or Automation prompt. Claim with `sdlc.sh claim <WORK-ID>` inside the agent. Do not invent a FEAT from chat.
2. **Gate.** `sdlc.sh gate <phase> --work-id <ID>`. Fail → stop or run the recommended earlier phase. Do not write product code. `--force` is human-only.
3. **Start** is `sdlc.sh start` **inside** the agent (local chat or cloud). Follow the Resume Prompt. One agent = one phase (code = one T##).
4. **The agent works.** Grounding files + retrieve + canvas. Code phase uses Kasana I1 once that overlay exists. Local may leave a branch for the human to push; a Cloud Agent typically commits, pushes, and opens a PR.
5. **Capture.** `sdlc.sh capture` in-repo. The plugin does not mark T## complete.
6. **Next phase.** A **separate** configured Automation (PR merge, label, CI, push, schedule, webhook) or a **human** launch. Every new run re-checks `gate`. Same verify error twice → `sdlc.sh shelf`; do not configure a third automatic code retry for that T##.
7. **Sunset.** A later local or cloud agent runs `/sdlc-spdd-sunset` when the Work ID is actually finished.

Cursor Automations do **not** dynamically pick a new prompt or Environment at runtime, and they do **not** spawn a follow-on Cloud Agent from inside a run. A future Cloud Agents API controller would be a **separate** initiative with its own Work ID. It is out of scope here.

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

Prefer a **repo-managed** `.cursor/environment.json` on each target so branches and PRs get the same platform. Dashboard Environments remain the place to attach **multiple** repos to an Automation fleet. Those are different objects: committed JSON is one repo’s bootstrap; the dashboard list is Automation scope.

U2 in this orchestrator is done: `.cursor/environment.json` runs `.cursor/install.sh` so Cloud Agents boot “SDLC-SPDD ready.” `agentCanUpdateSnapshot` means “Whether the agent can update the snapshot” (Cursor schema); public Setup/Builds docs do not say it enables Builds.

## Contract the plugin and Automations must speak

**Cursor Automations:** configured trigger + prompt + Environment. Watch status and PRs in Cursor / GitHub. Do not reimplement the pod.

**SDLC (inside the agent):** `sdlc.sh` — `next`, `status --json`, `list-work`, `claim`, `shelf`, `resume`, `gate`, `start`, `capture`, `accept`. `--force` on gate is human-only.

Do **not**:

- Call a model from Uberorchbot application code (there is no such runtime on `main`).
- Reimplement `gate_check` or the canvas in the plugin.
- Skip phases because “the bot is sure.”
- Open PRs against `embabel/guide`.
- Treat mocked Guide HTTP as the graph.
- Stand up a parallel agent runtime that duplicates Cloud Agents.
- Revive `archive/main-lab-control-plane`.
- Claim native Automation self-chaining.

## Fit with Kasana I0–I3

| Kasana | On this platform |
|--------|------------------|
| I0 overlay rule | Inner loop is `/sdlc-spdd-code` **inside the Cloud Agent**, not a Python class in Uberorchbot |
| I1 verify / Files: / stop | The **code-phase Cloud Agent** obeys the command. Automations / humans refuse a third code run after shelf |
| I2 review Files: vs diff | A **review-phase** Automation or human launch, not Uberorchbot starting an agent from Java |
| I3 optional hooks | Target Environment `install`/`start` or target CI — still not Uberorchbot |

## Suggested work

| ID | What | Where |
|----|------|--------|
| **U0** | Cloud Agents + Environments are the platform | this file (done) |
| **U1** | Read Uberorchbot; correct dispatcher assumptions | this file (done in the U1 amendment) |
| **U2** | Repo-managed `.cursor/environment.json`: `install` has `sdlc-engine` | this orchestrator (done) |
| **U3** | Opt-in `sdlc-session` skill: existing Work ID, gate, Resume Prompt, one phase, capture | Uberorchbot plugin (done — [Uberorchbot #16](https://github.com/jmjava/Uberorchbot/pull/16)) |
| **U4** | Document and configure **separate** event-triggered Automations; re-check `gate` every run; shelf after repeat failure | Uberorchbot docs + Cursor Automations UI (not started) |
| **U5** | Reuse regenerated `/sdlc-spdd-code` (I1); do not duplicate the four bullets in the plugin | this repo I1, then U3 |

U2 is done in this repo (committed `.cursor/environment.json` + `.cursor/install.sh`). U3 is done in Uberorchbot (#16). U4 is live Automation save — not started. Do not invent a DOC/FEAT.

## Claims allowed

- We **plan** to run SDLC-SPDD and the Kasana code overlay **on Cursor Cloud Agents/Environments**.
- Uberorchbot **as of `main`** is a plugin pack. The loop is Cursor Automations.
- Native dynamic spawn / prompt routing is **not** a shipping claim.
- No change to DOC-001/002 or `gate_check` enter-phase semantics in this note.

## See also

- [Kasana integration plan (I0–I3)](kasana-agent-harness-2-0.md)
- [Workflow sequence](../workflow.md)
- [Session prompt standard](../session-prompt-standard.md) — Resume Prompt is the in-agent session contract
- [Issue sync and branching](../issue-sync-and-branching.md)
- [Design decisions](../design-decisions.md)
- Cursor: [Cloud Agent setup](https://cursor.com/docs/cloud-agent/setup), [Automations](https://cursor.com/docs/cloud-agent/automations), [environment schema](https://cursor.com/schemas/environment.schema.json)
