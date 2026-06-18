# SDLC Agents and the SDLC-SPDD Framework

How [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents) progressive disclosure and context-engineering principles map to this orchestrator — and where we implement them today.

This is complementary to [context loading and scaling](context-loading-and-scaling.md), [Chelsea Troy and the framework](chelsea-troy-and-the-framework.md), and [hybrid model](hybrid-model.md). SDLC Agents supplies the **lifecycle and loading discipline**; SPDD supplies the **governed artifact contract**; this orchestrator wires both into Cursor, Copilot, and Claude Code.

## Core claim (SDLC Agents)

LLMs write code fast, but naive prompt stuffing wastes tokens and dilutes attention. SDLC Agents addresses this with **progressive disclosure**: each specialized phase loads **only contextually relevant knowledge** — not whole directories, not unrelated history, not every skill at once.

Key upstream capabilities:

| SDLC Agents capability | What it means |
|------------------------|---------------|
| **Progressive disclosure** | Agents load only what the current task needs |
| **Dynamic skill selection** | `#SkillName` to include, `!SkillName` to exclude |
| **Extension support** | Project-local rules in `agent-context/extensions/` |
| **Phase-specialized agents** | Initializer, Planning, Architect, Coding, Review, Retro, Curator |
| **Architecture-first** | Structure validated before implementation |

## Progressive disclosure → two-tier context

| SDLC Agents principle | SDLC-SPDD mechanism |
|-----------------------|---------------------|
| Do not bloat every prompt | **Tier 1** grounding (~fixed size, auto-injected once per assistant) |
| Load artifacts on demand | **Tier 2** on-demand only — `@`-mention, session brief, or index lookup |
| Each phase loads minimal context | Per-phase context budget in grounding files and [context-loading-and-scaling.md](context-loading-and-scaling.md#per-phase-context-budget) |
| Avoid whole-repo scans | Index-driven retrieval: `domain-index.md`, `context-index.md`, `session-index.md`, `phase-index.md` |
| Specialized agents, clear handoffs | `/sdlc-spdd-*` command per phase; `start-agent-session.sh` Resume Prompt |

See [Two tiers of context](context-loading-and-scaling.md#two-tiers-of-context).

## Dynamic skill selection → `#SkillName` / `!SkillName`

SDLC Agents lets users request skills inline (for example `#TDD`, `#java`, `!Kafka`). This orchestrator documents the same pattern in assistant-neutral form:

    /sdlc-spdd-analysis Add order processing API #java #TDD !Kafka

Expected behavior:

1. Load matching guidance from `agent-context/playbooks/` or `agent-context/extensions/skills/` when present.
2. Exclude skills marked with `!`.
3. Record selected skills in the analysis artifact, canvas Metadata, or progress log.

The orchestrator does **not** ship an automatic skill loader runtime (same boundary as upstream — see [design decisions](design-decisions.md)). Teams reference skills explicitly in prompts; agents load the named files when they exist.

## Extensions → `agent-context/extensions/`

SDLC Agents supports custom rules without modifying core agent files. After `init-project.sh`, projects include:

    agent-context/extensions/
    ├── _all-agents/     # Rules for every phase
    ├── skills/          # Custom skill markdown (referenced via #SkillName)
    └── README.md

Drop a `.md` file into the appropriate folder; agents should read extensions **only when** the active phase or `#SkillName` directive calls for them — not on every request.

Playbooks under `agent-context/playbooks/` remain the shipped, framework-owned workflows. Extensions are project-owned overrides and additions.

## Phase-specialized context → per-phase budget

SDLC Agents assigns each agent a narrow loading scope. This orchestrator enforces the same contract through command packs and grounding rules:

| Phase | Load (progressive) | Avoid |
|-------|-------------------|-------|
| init | repo layout, stack markers, memory seeds | full codebase |
| analysis | requirement, indexes, scoped code areas from keywords | unrelated modules |
| plan | analysis artifact, requirement, roadmap, active milestone | whole repo |
| architect | analysis + canvas, architecture decisions, harness | implementation detail not needed for design |
| code | canvas, one operation, relevant files + tests | other operations, unrelated modules |
| api-test | canvas Requirements/Operations, implemented endpoints for this Work ID | unrelated features |
| review | canvas, diff, quality gates | new feature ideation |
| retro / sync | canvas, progress log, memory file being updated | new implementation |

Fowler Step 3 **analysis** and Step 5 **api-test** extend the SDLC Agents lifecycle without breaking progressive disclosure — they narrow scope *before* planning and verify *after* coding.

## Architecture-first → `/sdlc-spdd-architect`

SDLC Agents validates structure before coding. This orchestrator requires **Ready For Coding** from `/sdlc-spdd-architect` before `/sdlc-spdd-code` implements an operation.

## Continual learning → indexes + capture

SDLC Agents Retro and Curator agents accumulate knowledge. This orchestrator captures learnings into durable memory and grows retrieval indexes:

- `capture-session-memory.sh` → `session-index.md`, `context-index.md`, `code-areas.md`
- `index-spdd-analysis.sh` → `domain-index.md`, analysis rows in `context-index.md`
- Retro writes `architecture-decisions.md`, `known-pitfalls.md`, `reusable-patterns.md`

Future sessions retrieve by **area or keyword**, not by reading all history.

## What we adopt vs. what we defer

| SDLC Agents feature | Status in this orchestrator |
|---------------------|----------------------------|
| Progressive disclosure by phase | **Adopted** — Tier 1/2 model, indexes, per-phase budgets |
| Dynamic `#SkillName` / `!SkillName` | **Adopted** — documented in grounding and hybrid model |
| Extensions folder | **Adopted** — scaffolded at install; manual reference in prompts |
| Compiled multi-agent runtime | **Deferred** — Markdown command adapters instead |
| Automatic skill loader | **Deferred** — explicit `#SkillName` + file reference |
| Automatic extension injection | **Deferred** — load when phase or prompt names them |

## Anti-patterns (violates progressive disclosure)

| Anti-pattern | Why it fails | Do instead |
|--------------|--------------|------------|
| Read `session-history.md` top-to-bottom | Unrelated sessions interleaved; context bloat | Filter `context-index.md` or `session-index.md` by Area |
| List or read whole `agent-context/` or `spdd/` | Token waste; Lost in the Middle | Start at `current-session.md`; follow index pointers |
| `@`-mention five artifacts when one suffices | Over-loads working context | Use session brief + one Work ID canvas |
| Plan before analysis | Unscoped file reads | `/sdlc-spdd-analysis` → index → `/sdlc-spdd-plan` |
| Load all playbooks/extensions every session | Defeats progressive disclosure | Load `#SkillName` or phase-relevant extension only |

## Quick reference map

| SDLC Agents concept | Where in this repo |
|---------------------|-------------------|
| Progressive disclosure | Tier 1 grounding + [context loading](context-loading-and-scaling.md) |
| Phase agents | `templates/cursor/sdlc-spdd-*.md`, Copilot/Claude command packs |
| `#SkillName` | Grounding Work Rules; [hybrid model — Skills](hybrid-model.md#skills-and-extensions) |
| Extensions | `agent-context/extensions/` (installed by `init-project.sh`) |
| Index retrieval | `agent-context/memory/*-index.md` |
| Session handoff | `start-agent-session.sh` → `current-session.md` |
| Capture learning | `capture-session-memory.sh`, `/sdlc-spdd-retro` |

## Read next

- [Context loading and scaling](context-loading-and-scaling.md) — mechanics and bootstrap
- [Hybrid SDLC Agents + SPDD model](hybrid-model.md) — full command mapping
- [What SDLC brings](what-sdlc-brings.md) — lifecycle value summary
- [Session prompt standard](session-prompt-standard.md) — copy-paste prompts that preserve context without over-loading
