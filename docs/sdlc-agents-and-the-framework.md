# SDLC Agents and the SDLC-SPDD Framework

How [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents) core capabilities map to this orchestrator — and where we implement, partially implement, or defer each one.

This is complementary to [context loading and scaling](context-loading-and-scaling.md), [Chelsea Troy and the framework](chelsea-troy-and-the-framework.md), and [hybrid model](hybrid-model.md). SDLC Agents supplies the **lifecycle and loading discipline**; SPDD supplies the **governed artifact contract**; this orchestrator wires both into Cursor, Copilot, and Claude Code.

## Core capabilities map

SDLC Agents advertises six capabilities that distinguish it from undifferentiated AI coding assistants. Here is how each maps to this orchestrator:

| SDLC Agents capability | What it means | Token / process impact | Status here | SDLC-SPDD mechanism |
|------------------------|---------------|------------------------|-------------|---------------------|
| **Progressive disclosure** | Agents load only contextually relevant knowledge — no bloated prompts | ↓ 60–80% fewer tokens vs. full-context (upstream claim) | **Adopted** | Tier 1 fixed grounding + Tier 2 on-demand; per-phase budgets; index retrieval instead of directory scans |
| **Self-learning** | Retro agent captures lessons; knowledge accumulates across tasks | Reuses learnings without re-explaining | **Adopted** | `/sdlc-spdd-retro`, `capture-session-memory.sh`, durable memory files, growing indexes |
| **Extension support** | Add custom skills without modifying core agent files | Load extensions only when relevant | **Adopted** | `agent-context/extensions/` + `resolve-agent-context.sh` + session brief **Resolved Context** |
| **Dynamic skill selection** | `#SkillName` to include, `!SkillName` to exclude | On-demand loading saves tokens | **Adopted** | `resolve-agent-context.sh --text`; example skills in `extensions/skills/` |
| **Architecture-first** | Structure validated before implementation | Prevents costly rework iterations | **Adopted** | `/sdlc-spdd-architect` → **Ready For Coding** gate before `/sdlc-spdd-code` |
| **Multi-agent orchestration** | Specialized agents with clear handoffs | Each agent loads minimal context | **Adopted** (prompt-based) | One `/sdlc-spdd-*` command per phase; `start-agent-session.sh` Resume Prompt handoffs |

We do **not** ship SDLC Agents' compiled multi-agent runtime. Skill and extension paths are resolved by `resolve-agent-context.sh` and embedded in session briefs — not injected silently on every chat request.

## Core claim (SDLC Agents)

LLMs write code fast, but naive prompt stuffing wastes tokens and dilutes attention. SDLC Agents addresses this with specialized phases, progressive disclosure, and accumulated project memory — not one undifferentiated "fix it" chat.

Key upstream capabilities (detail sections below):

| SDLC Agents capability | What it means |
|------------------------|---------------|
| **Progressive disclosure** | Agents load only what the current task needs |
| **Self-learning** | Retro + curator patterns; lessons persist across tasks |
| **Extension support** | Project-local rules in `agent-context/extensions/` |
| **Dynamic skill selection** | `#SkillName` to include, `!SkillName` to exclude |
| **Architecture-first** | Structure validated before implementation |
| **Multi-agent orchestration** | Initializer, Planning, Architect, Coding, Review, Retro, Curator with handoffs |

## Progressive disclosure → two-tier context

| SDLC Agents principle | SDLC-SPDD mechanism |
|-----------------------|---------------------|
| Do not bloat every prompt | **Tier 1** grounding (~fixed size, auto-injected once per assistant) |
| Load artifacts on demand | **Tier 2** on-demand only — `@`-mention, session brief, or index lookup |
| Each phase loads minimal context | Per-phase context budget in grounding files and [context-loading-and-scaling.md](context-loading-and-scaling.md#per-phase-context-budget) |
| Avoid whole-repo scans | Index-driven retrieval: `domain-index.md`, `context-index.md`, `session-index.md`, `phase-index.md` |
| Specialized agents, clear handoffs | `/sdlc-spdd-*` command per phase; `start-agent-session.sh` Resume Prompt |

See [Two tiers of context](context-loading-and-scaling.md#two-tiers-of-context).

## Dynamic skill selection → `resolve-agent-context.sh`

SDLC Agents lets users request skills inline (for example `#TDD`, `#java`, `!Kafka`). This orchestrator resolves them with:

    ./scripts/sdlc-spdd/resolve-agent-context.sh --text "Implement auth #TDD #java !Kafka"
    ./scripts/sdlc-spdd/resolve-agent-context.sh --phase code --text "#TDD"

Search order for `#SkillName`:

1. `agent-context/extensions/skills/<SkillName>.md`
2. `agent-context/playbooks/<skillname>-playbook.md`
3. `agent-context/playbooks/<skillname>.md`

`!SkillName` tokens exclude a skill even if also requested with `#`.

`start-agent-session.sh` embeds phase-resolved paths under **Resolved Context** in `current-session.md`.

List discoverable skills:

    ./scripts/sdlc-spdd/resolve-agent-context.sh --list-skills

## Extensions → `agent-context/extensions/`

SDLC Agents supports custom rules without modifying core agent files. After `init-project.sh`, projects include SDLC Agents-aligned agent folders:

    agent-context/extensions/
    ├── _all-agents/        # every phase
    ├── initializer-agent/
    ├── planning-agent/     # analysis, plan, prompt-update
    ├── architect-agent/
    ├── coding-agent/       # code, api-test
    ├── codereview-agent/
    ├── retro-agent/
    ├── curator-agent/      # sync
    ├── skills/             # #SkillName targets
    └── README.md

Phase resolution (via `resolve-agent-context.sh --phase <phase>`):

- Loads `_all-agents/*.md` + the matching `*-agent/*.md` folder
- Adds phase static playbooks from `phase-index.md` (for example code → bugfix/java/refactor playbooks)

Drop a `.md` file into the appropriate folder; `start-agent-session.sh` lists resolved paths in the session brief — agents load those files, not the whole tree.

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

SDLC Agents validates structure before coding. This orchestrator enforces an explicit readiness gate:

| SDLC Agents | SDLC-SPDD |
|-------------|-----------|
| Architect agent reviews plan against rules | `/sdlc-spdd-architect` reads analysis + canvas, scoped code areas |
| Blocks coding until design is sound | Canvas must reach **Ready For Coding** before `/sdlc-spdd-code` |
| Entities, Approach, Structure, Safeguards checked | REASONS Canvas sections + `agent-context/harness/` quality gates |

Analysis (`/sdlc-spdd-analysis`) narrows scope **before** the architect runs — so architecture review reads relevant modules, not the whole repo.

Grounding files and session anti-patterns explicitly forbid coding before architect.

## Self-learning → retro, capture, and indexes

SDLC Agents Retro and Curator agents accumulate knowledge so future tasks do not re-explain the same lessons.

| SDLC Agents | SDLC-SPDD |
|-------------|-----------|
| Retro agent | `/sdlc-spdd-retro` — writes `retro.md`, updates memory files |
| Curator agent | `/sdlc-spdd-sync` + `summarize-session-notes.sh` — reconcile drift, import narrative notes |
| Knowledge persists across tasks | `architecture-decisions.md`, `known-pitfalls.md`, `reusable-patterns.md` |
| Retrieve without re-explaining | `resolve-agent-context.sh --work-id` filters `context-index.md` by Code Areas; area-scoped runs skip whole memory logs and resolve **Entry** paths + **Source** anchors |

**Capture loop** (every session end):

    capture-session-memory.sh → session-index + context-index + code-areas grow
    index-spdd-analysis.sh     → domain-index + analysis rows after Fowler Step 3

Next session: bootstrap → indexes → load only matched artifacts. You do not paste prior retro prose into every prompt.

## Multi-agent orchestration → phase commands + session handoffs

SDLC Agents runs specialized agents with clear responsibilities. This orchestrator does not compile a runtime; it **simulates** the same separation through command packs and handoff artifacts:

| SDLC Agents agent | SDLC-SPDD command | Handoff artifact |
|-------------------|-------------------|------------------|
| Initializer | `/sdlc-spdd-init` | `project-memory.md`, stack detection |
| Planning | `/sdlc-spdd-plan` | REASONS Canvas under `spdd/canvas/` |
| Architect | `/sdlc-spdd-architect` | Readiness decision on canvas |
| Coding | `/sdlc-spdd-code` | One Operation + progress log |
| Code Review | `/sdlc-spdd-review` | Review report under `spdd/reviews/` |
| Retro | `/sdlc-spdd-retro` | Memory files + feature `retro.md` |
| Curator (maintenance) | `/sdlc-spdd-sync` | Updated canvas + `spdd/sync/` log |

**Analysis** and **API test** are Fowler SPDD additions inserted without breaking handoffs:

    Analysis → Plan → Architect → Code → API Test → Review → Retro → Sync

**Session glue:** `start-agent-session.sh` writes `current-session.md` with Framework Orientation + Resume Prompt — the paste-this handoff between chats. Re-run with `--phase` when the phase changes.

Each command pack states **do not** do the next agent's job (for example plan does not code; architect does not implement).

## What we adopt vs. what we defer

| SDLC Agents feature | Status in this orchestrator |
|---------------------|----------------------------|
| Progressive disclosure by phase | **Adopted** — Tier 1/2 model, indexes, per-phase budgets |
| Self-learning across tasks | **Adopted** — retro, capture, indexed memory retrieval |
| Architecture-first gate | **Adopted** — architect readiness before code |
| Multi-agent orchestration | **Adopted** (prompt-based) — phase commands + session handoffs |
| Dynamic `#SkillName` / `!SkillName` | **Adopted** — `resolve-agent-context.sh` |
| Extensions folder + phase agent dirs | **Adopted** — install scaffold + session brief resolution |
| Compiled multi-agent runtime | **Deferred** — Markdown command adapters instead |
| Automatic skill loader (no script) | **Deferred** — run resolve script or read session brief |
| Automatic extension injection (no script) | **Deferred** — `start-agent-session.sh` + resolve script |
| Curator as separate always-on agent | **Partial** — `/sdlc-spdd-sync` + memory hygiene scripts; no dedicated curator command |
| Token savings measurement | **Not measured** — upstream 60–80% claim applies to their runtime; our model reduces load by design but is not benchmarked |

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
| Self-learning | `/sdlc-spdd-retro`, `capture-session-memory.sh`, memory + indexes |
| Extensions | `agent-context/extensions/` + `resolve-agent-context.sh` |
| `#SkillName` | `resolve-agent-context.sh --text`; [hybrid model — Skills](hybrid-model.md#skills-and-extensions) |
| Skill/extension resolver | `scripts/resolve-agent-context.sh` → `scripts/sdlc-spdd/` at install |
| Architecture-first | `/sdlc-spdd-architect`, readiness gate, harness |
| Multi-agent orchestration | Phase command packs; `start-agent-session.sh` handoffs |
| Phase agents | `templates/cursor/sdlc-spdd-*.md`, Copilot/Claude command packs |
| Index retrieval | `agent-context/memory/*-index.md` |
| Session handoff | `start-agent-session.sh` → `current-session.md` |
| Curator-like sync | `/sdlc-spdd-sync`, `summarize-session-notes.sh` |

## Read next

- [Context loading and scaling](context-loading-and-scaling.md) — mechanics and bootstrap
- [Hybrid SDLC Agents + SPDD model](hybrid-model.md) — full command mapping
- [What SDLC brings](what-sdlc-brings.md) — lifecycle value summary
- [Session prompt standard](session-prompt-standard.md) — copy-paste prompts that preserve context without over-loading
