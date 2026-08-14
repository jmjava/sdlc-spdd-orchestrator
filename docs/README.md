# Documentation

**Orchestrator repo hub** — when SDLC-SPDD is installed into a target application, that project gets a leaner hub at `docs/sdlc-spdd/README.md` (same guides, clearer entry path).

Use this hub to choose the right guide for your current task. If you are new, read the first section in order. If you are already operating a project, jump to the section that matches what you are doing.

**Start with the seven onboarding pages below.** They are the complete path from install to daily use. The other sections are task-specific reference — open one when its description matches what you are doing.

## Core Model

    Planning: ROADMAP.md, milestone-*.md, requirements/, requirements/milestones/, session-notes/
            -> inform and summarize
    spdd/canvas/ + spdd/memory/ (lessons ledger)  [+ hot .sdlc/ runtime]
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

Use roadmap, milestone, and session-note files for project planning and narrative.
Use SDLC-SPDD artifacts for governed execution and durable agent memory.

**One mental model everywhere:** canvas + contracts are read directly; the
lessons ledger (`spdd/memory/lessons.jsonl`) is the committed record; the
**Guide DICE graph is the working store** queried on demand; SQLite is an
optional local cache; captures are staged quietly and accepted at gates.

**How do Planning, SPDD, and SDLC fit together in practice?** → [Three-part operating path](three-part-operating-path.md)

## Storage v3 — where memory and context live

Start here for anything about memory, sessions, retrieval, or backends:

| Guide | Use it when |
|-------|-------------|
| [**Storage v3**](storage-v3.md) | **The canonical storage architecture** — ledger, stage-then-accept, Guide working store, parity |
| [Runtime and ledger](runtime-and-ledger.md) | Day-to-day view: hot briefs under `.sdlc/`, capture → accept, retrieval commands |
| [Guide flow](guide-flow.md) | How phases query the Guide DICE working store (`spdd_*` MCP tools) |
| [DICE projection runbook](dice-projection-runbook.md) | Run Guide + Neo4j locally (tag `spdd-projection-v3`) |
| [Context loading and scaling](context-loading-and-scaling.md) | What loads automatically vs on demand; per-phase budgets |
| [Triple-path context](triple-path-context.md) | Configure backends (`CONTEXT_BACKENDS`): git + guide default, sqlite opt-in |
| [Local SQLite index](local-sqlite-index.md) | The opt-in regenerable cache (`.sdlc/index.sqlite`, schema v5) |
| [Diagrams](diagrams/README.md) | All 14 PlantUML architecture diagrams |

Also useful: [Quiet mode](quiet-mode.md) (product work without T## dogfood
gravity), [Ops console](ops-console.md) (Dashboard tab + install / Guide /
Jira link & sync / ADF viewer), [ADF templates + Vue3 console](adf-template-library-and-vue3-console.md)
(product slice in progress).

## If You Are New, Read These in Order

1. [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md) — hands-on first session from install to memory capture.
2. [Three-part operating path](three-part-operating-path.md) — how Planning, SPDD, and SDLC work together end to end.
3. [Installing into your project](installing-into-your-project.md) — fresh install, upgrade path, verification, and troubleshooting.
4. [Top useful concepts and commands](useful-concepts-and-commands.md) — Work IDs, canvases, sessions, commands, and prompt patterns.
5. [Maintaining your project](maintaining-your-project.md) — upgrades, memory hygiene, canvas sync, links, and session maintenance.
6. [Storage v3](storage-v3.md) — where memory lives: ledger, Guide working store, runtime, backends.

**Workflow CLI reference** (pointer, phase tracking, team registry): [agent-context/README.md](../agent-context/README.md#sdlc-pointer-current-choretask) — installed in target projects at `sdlc-spdd/scripts/` with docs under `docs/sdlc-spdd/`.

**Python engine:** [SDLC Engine](engine-v2.md) — reusable `sdlc_engine` package; `SDLC_ENGINE=auto|python|shell` on `scripts/sdlc.sh`.

**Local GUIs (experimental ops console + ADF Viewer):** [Ops console and ADF Viewer](ops-console.md).

You can treat the onboarding pages above as the canonical path.

## If You Are Installing or Upgrading

| Guide | Use it when |
|-------|-------------|
| [Installing into your project](installing-into-your-project.md) | You are adding SDLC-SPDD to a target application for the first time |
| [Ops console and ADF Viewer](ops-console.md) | You want the experimental localhost UIs (Dashboard, Jira link/sync, install/Guide/viewer) |
| [ADF Viewer](adf-viewer.md) | You edit checked-in `adf/*.adf.json` or sync ticket descriptions with Jira |
| [Framework upgrade](framework-upgrade.md) | A target app already has an older SDLC-SPDD install |
| [Cursor usage](cursor-usage.md) | You only need Cursor command setup and invocation |
| [GitHub Copilot usage](copilot-usage.md) | You only need Copilot instructions and prompt files |
| [Claude Code usage](claude-usage.md) | You only need Claude Code command and CLAUDE.md setup |
| [Agent session scripts](agent-session-scripts.md) | You need the setup/resync/capture scripts and target-local runtime commands |

## If You Are Using This Daily

Three docs work together — each has a distinct job; prompts are not duplicated across them:

| Guide | Role |
|-------|------|
| [Session prompt standard](session-prompt-standard.md) | **Prompts** — copy-paste text for triage, phases, handoff |
| [Daily runbook](daily-runbook.md) | **Rhythm** — rules, script sequences, phase checklists |
| [Workflow](workflow.md) | **Sequence** — 15-step table and which part owns each step |
| [Three-part operating path](three-part-operating-path.md) | **Loop** — how Planning → SPDD → SDLC connect for a work item |

Also useful day to day:

| Guide | Use it when |
|-------|-------------|
| [Initialization and invocation](initialization-and-invocation.md) | You need concrete examples for starting work and invoking each SDLC-SPDD skill |
| [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md) | You use `ROADMAP.md`, `milestone-*.md`, and `session-notes/` to track project progress |
| [Top useful concepts and commands](useful-concepts-and-commands.md) | You want definitions for Work ID, canvas, sync, memory |
| [Cheat sheet](sdlc-spdd-cheat-sheet.md) | You want a one-page PDF-friendly **command** reference |
| [agent-context/README.md](../agent-context/README.md) | You need workflow CLI, pointer, or team registry detail |

## If You Are Integrating with Jira or GitHub

| Guide | Use it when |
|-------|-------------|
| [Jira runbook](jira-runbook.md) | Create issues in Jira UI, link keys locally, push/pull requirement markdown |
| [Issue sync and branching](issue-sync-and-branching.md) | Tracker-to-branch naming, commit/PR linkage, ops console Issues tab, ADF viewer sync |
| [Jira-compatible requirements format](jira-compatible-requirements-format.md) | YAML frontmatter, Related Work, and validation for requirements |
| [Analysis phase scope validation](analysis-phase-scope-validation.md) | Scope Lock before analysis generation |
| [Ops console](ops-console.md) | Configure integrations (`.sdlc/integrations-config.json`), link issues, sync from the GUI |

## If You Are Contributing or Editing Docs

| Guide | Use it when |
|-------|-------------|
| [CONTRIBUTING.md](../CONTRIBUTING.md) | You are changing scripts or documentation — includes orchestrator vs target paths and a consistency checklist |
| [Command specs](contributing-command-specs.md) | You are editing Cursor/Copilot/Claude commands via `spec/commands/` |
| [Contributing skills](contributing-skills.md) | You are adding or updating `#SkillName` files under `harness/skills/` |
| [Ops console and ADF Viewer](ops-console.md) | Two local GUIs (`:5051` / `:5050`), tabs, and Guide integration map |
| [MCP Guide for agents](mcp-guide-for-agents.md) | You query Guide from CLI or delegate `spdd_*` MCP tools during analysis/code phases |
| [DICE projection runbook](dice-projection-runbook.md) | You run the local Guide + Neo4j stack for dogfood or retrieval tests |
| [Local SQLite index](local-sqlite-index.md) | Zero-install `.sdlc/index.sqlite` query cache; opt-in, fully regenerable from the ledger |
| [Jira ADF + requirements sync (research)](research/jira-adf-and-requirements-sync.md) | Exact Cloud ADF / Server wiki payloads; requirements as source of truth for Jira + REASONS |
| [SDLC Engine — commit-message](engine-v2.md#commit-message-diff-report) | Python engine diff report for `/sdlc-spdd-commit-message` |
| [SDLC Engine — sunset](engine-v2.md#feature-sunset-snapshot) | Close-out snapshot of GitHub PR, commits, and Jira into the ledger |
| [Guide flow](guide-flow.md) | End-to-end Guide working store: ledger + canvas ingest, runtime resolution, per-phase tools, persist loop |
| [DICE projection runbook](dice-projection-runbook.md) | Run against Guide tag `spdd-projection-v3` (or `GUIDE_GIT_REF=main`): typed entity persist/retrieve, `spdd_*` MCP tools |
| [Narrated demos bundle](demos/README.md) | You maintain or extend the docgen bundle under `docs/demos/` |
| [TESTING.md](../TESTING.md) | You need the command-testing confidence stack (CI gates, local smoke, planning-sync verification) |
| [Design decisions](design-decisions.md) | Rationale for major choices (including planned-but-not-installed features) |

## Prompt Standards by Concept

**Start with [Session prompt standard](session-prompt-standard.md)** — it is the default for day-to-day agent work. That page includes [Which prompt standard?](session-prompt-standard.md#which-prompt-standard) — a decision guide for when to drill into SPDD or Planning.

| Guide | Use it when |
|-------|-------------|
| [Session prompt standard](session-prompt-standard.md) | **Default.** Starting, continuing, or ending an agent session across all layers |
| [SPDD prompt standard](spdd-prompt-standard.md) | Canvas governance only: alignment, architect, operations scope, review, prompt-update, sync |
| [Planning prompt standard](planning-prompt-standard.md) | Delivery narrative only: roadmap, milestones, session notes, capture, roadmap refresh |

## If You Need Stack or Reference Material

| Guide | Use it when |
|-------|-------------|
| [Java Spring Boot usage](java-spring-boot-usage.md) | You are applying SDLC-SPDD to a Spring Boot project |
| [Tekton usage](tekton-usage.md) | You are applying SDLC-SPDD to Tekton pipelines |
| [Roadmap](../ROADMAP.md) | Planned capabilities (repo root, not docs/) |

## Quick Start (one path)

Follow the adoption path in the repository [README](../README.md#the-adoption-path): install → first day → three-part operating path → daily prompts.

After install, target-local copies of these docs live at `docs/sdlc-spdd/` in your application. Cursor/Copilot/Claude Code slash-command examples: [Initialization and invocation](initialization-and-invocation.md).
