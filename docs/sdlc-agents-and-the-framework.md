# SDLC Agents and the SDLC-SPDD Framework

How [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents) core capabilities map to this orchestrator — and where we implement, partially implement, or defer each one.

This is complementary to [context loading and scaling](context-loading-and-scaling.md). SDLC Agents supplies the **lifecycle and loading discipline**; SPDD supplies the **governed artifact contract**; this orchestrator wires both into Cursor, Copilot, and Claude Code.

## Core capabilities map

| SDLC Agents capability | What it means | Status here | SDLC-SPDD mechanism |
|------------------------|---------------|-------------|---------------------|
| **Progressive disclosure** | Load only contextually relevant knowledge | **Adopted** | Tier 1 grounding + Tier 2 on-demand; per-phase budgets; ledger retrieval instead of directory scans |
| **Self-learning** | Lessons accumulate across tasks | **Adopted** | `/sdlc-spdd-retro`, capture → stage → `/sdlc-spdd-accept`, `spdd/memory/lessons.jsonl` |
| **Extension support** | Custom rules without modifying core commands | **Adopted** | `harness/phase-index.md` + `harness/skills/` + `resolve-agent-context.sh` |
| **Dynamic skill selection** | `#SkillName` / `!SkillName` | **Adopted** | `resolve-agent-context.sh --text`; skills in `harness/skills/` |
| **Architecture-first** | Structure validated before implementation | **Adopted** | `/sdlc-spdd-architect` → **Ready For Coding** gate before `/sdlc-spdd-code` |
| **Multi-agent orchestration** | Specialized agents with clear handoffs | **Adopted** (prompt-based) | One `/sdlc-spdd-*` command per phase; `sdlc.sh start` + Resume Prompt handoffs |

We do **not** ship SDLC Agents' compiled multi-agent runtime. Skills and phase
static files are resolved by `resolve-agent-context.sh` and embedded in session
briefs — not injected silently on every chat request.

## Progressive disclosure → two-tier context

| SDLC Agents principle | SDLC-SPDD mechanism |
|-----------------------|---------------------|
| Do not bloat every prompt | **Tier 1** grounding (~fixed size, auto-injected once per assistant) |
| Load artifacts on demand | **Tier 2** on-demand only — `@`-mention, session brief, or retrieval query |
| Each phase loads minimal context | Per-phase context budget in grounding files and [context-loading-and-scaling.md](context-loading-and-scaling.md#per-phase-context-budget) |
| Avoid whole-repo scans | `sdlc-engine context retrieve|show|digest`; `spdd_*` MCP tools over Guide |
| Specialized agents, clear handoffs | `/sdlc-spdd-*` command per phase; `start-agent-session.sh` Resume Prompt |

See [Two tiers of context](context-loading-and-scaling.md#two-tiers-of-context).

## Dynamic skill selection → `resolve-agent-context.sh`

SDLC Agents lets users request skills inline (for example `#TDD`, `#java-feature`, `!Kafka`). This orchestrator resolves them with:

    ./sdlc-spdd/scripts/resolve-agent-context.sh --text "Implement auth #TDD #java-feature"
    ./sdlc-spdd/scripts/resolve-agent-context.sh --phase code --text "#TDD"

Search order for `#SkillName`:

1. `harness/skills/<SkillName>.md` (case variants tried)
2. Phase-matching skills from skill frontmatter when `--phase` is set

`!SkillName` tokens exclude a skill even if also requested with `#`.

`start-agent-session.sh` embeds phase-resolved paths under **Resolved Context** in `current-session.md`.

List discoverable skills:

    ./sdlc-spdd/scripts/resolve-agent-context.sh --list-skills

## Instruction layer → `harness/`

Phase-scoped static context is declared in `harness/phase-index.md` and loaded
by `resolve-agent-context.sh --phase <phase>`. On-demand skills live in
`harness/skills/`. There is no separate extensions tree or manifest file.

Drop a skill file into `harness/skills/`; request it with `#SkillName` or set
`phases:` in frontmatter for automatic phase loading. `start-agent-session.sh`
lists resolved paths in the session brief — agents load those files, not the
whole tree.

## Phase-specialized context → per-phase budget

| Phase | Load (progressive) | Avoid |
|-------|-------------------|-------|
| init | repo layout, stack markers | full codebase |
| analysis | requirement, scoped code areas from keywords | unrelated modules |
| plan | analysis artifact, requirement, roadmap, active milestone | whole repo |
| architect | analysis + canvas, harness | implementation detail not needed for design |
| code | canvas, one operation, relevant files + tests | other operations, unrelated modules |
| api-test | canvas Requirements/Operations, implemented endpoints for this Work ID | unrelated features |
| review | canvas, diff, quality gates | new feature ideation |
| retro / sync | canvas, review/sync artifacts | new implementation |

Fowler Step 3 **analysis** and Step 5 **api-test** extend the SDLC Agents lifecycle without breaking progressive disclosure.

## Architecture-first → `/sdlc-spdd-architect`

| SDLC Agents | SDLC-SPDD |
|-------------|-----------|
| Architect agent reviews plan against rules | `/sdlc-spdd-architect` reads analysis + canvas, scoped code areas |
| Blocks coding until design is sound | Canvas must reach **Ready For Coding** before `/sdlc-spdd-code` |
| Entities, Approach, Structure, Safeguards checked | REASONS Canvas sections + `harness/` quality gates |

## Self-learning → retro, capture, accept

| SDLC Agents | SDLC-SPDD |
|-------------|-----------|
| Retro agent | `/sdlc-spdd-retro` — writes `retro.md`, stages lesson records |
| Curator agent | `/sdlc-spdd-accept` + `/sdlc-spdd-sync` — review staged records, promote keepers, reconcile drift |
| Knowledge persists across tasks | Ledger records: `decision`, `pitfall`, `pattern` kinds in `spdd/memory/lessons.jsonl` |
| Retrieve without re-explaining | `sdlc-engine context retrieve --area <A> --kind <K>`; `spdd_areaLessons` when Guide is live |

**Capture loop** (every session end):

    capture-session-memory.sh → lesson records staged in .sdlc/staged/lessons.jsonl
    index-spdd-analysis.sh    → analysis record staged after Fowler Step 3
    /sdlc-spdd-accept         → keepers promoted to the committed ledger at gates

Next session: bootstrap → digest → load only matched artifacts.

## Multi-agent orchestration → phase commands + session handoffs

| SDLC Agents agent | SDLC-SPDD command | Handoff artifact |
|-------------------|-------------------|------------------|
| Initializer | `/sdlc-spdd-init` | stack detection, orientation |
| Planning | `/sdlc-spdd-plan` | REASONS Canvas under `spdd/canvas/` |
| Architect | `/sdlc-spdd-architect` | Readiness decision on canvas |
| Coding | `/sdlc-spdd-code` | One Operation + progress in canvas/review |
| Code Review | `/sdlc-spdd-review` | Review report under `spdd/reviews/` |
| Retro | `/sdlc-spdd-retro` | Staged lesson records |
| Curator (maintenance) | `/sdlc-spdd-sync` | Updated canvas + `spdd/sync/` log |

**Analysis** and **API test** are Fowler SPDD additions:

    Analysis → Plan → Architect → Code → API Test → Review → Retro → Sync

**Session glue:** `./sdlc-spdd/scripts/sdlc.sh start` writes `current-session.md`
with Framework Orientation + Resume Prompt. Use `sdlc.sh advance` when the phase
changes, then re-run `start`.

## What we adopt vs. what we defer

| SDLC Agents feature | Status in this orchestrator |
|---------------------|----------------------------|
| Progressive disclosure by phase | **Adopted** — Tier 1/2 model, retrieval, per-phase budgets |
| Self-learning across tasks | **Adopted** — retro, capture, accept, ledger retrieval |
| Architecture-first gate | **Adopted** — architect readiness before code |
| Multi-agent orchestration | **Adopted** (prompt-based) — phase commands + session handoffs |
| Dynamic `#SkillName` / `!SkillName` | **Adopted** — `resolve-agent-context.sh` |
| Harness + skills instruction layer | **Adopted** — `harness/phase-index.md`, `harness/skills/` |
| Compiled multi-agent runtime | **Deferred** — Markdown command adapters instead |
| Automatic skill loader (no script) | **Deferred** — run resolve script or read session brief |
| Curator as separate always-on agent | **Partial** — `/sdlc-spdd-sync` + memory hygiene scripts |
| Token savings measurement | **Not measured** — our model reduces load by design but is not benchmarked |

## Anti-patterns (violates progressive disclosure)

| Anti-pattern | Why it fails | Do instead |
|--------------|--------------|------------|
| Bulk-read `spdd/memory/lessons.jsonl` | Unrelated records interleaved; context bloat | `sdlc-engine context retrieve` filtered by Work ID / area / kind |
| List or read whole directories | Token waste; Lost in the Middle | Start at `current-session.md`; follow its digest and Resolved Context |
| `@`-mention five artifacts when one suffices | Over-loads working context | Use session brief + one Work ID canvas |
| Plan before analysis | Unscoped file reads | `/sdlc-spdd-analysis` → index → `/sdlc-spdd-plan` |
| Load every skill every session | Defeats progressive disclosure | Load `#SkillName` or phase-relevant harness files only |

## Quick reference map

| SDLC Agents concept | Where in this repo |
|---------------------|-------------------|
| Progressive disclosure | Tier 1 grounding + [context loading](context-loading-and-scaling.md) |
| Self-learning | `/sdlc-spdd-retro`, capture, accept, ledger |
| Skills | `harness/skills/` + `resolve-agent-context.sh` |
| `#SkillName` | `resolve-agent-context.sh --text`; [contributing skills](contributing-skills.md) |
| Phase static context | `harness/phase-index.md` |
| Architecture-first | `/sdlc-spdd-architect`, readiness gate, harness |
| Multi-agent orchestration | Phase command packs; `start-agent-session.sh` handoffs |
| Bounded retrieval | `sdlc-engine context retrieve|digest`; Guide `spdd_*` tools |
| Session handoff | `sdlc.sh start` → `current-session.md`; `/sdlc-spdd-whereami` |
| Curator-like sync | `/sdlc-spdd-sync`, `summarize-session-notes.sh` |

## Read next

- [Context loading and scaling](context-loading-and-scaling.md) — mechanics and bootstrap
- [Workflow](workflow.md) — phase sequence and command mapping
- [Session prompt standard](session-prompt-standard.md) — copy-paste prompts that preserve context without over-loading
