# Documentation

**Orchestrator repo hub** — when SDLC-SPDD is installed into a target application, that project gets a leaner hub at `docs/sdlc-spdd/README.md` (same guides, clearer entry path).

Use this hub to choose the right guide for your current task. If you are new, read the first section in order. If you are already operating a project, jump to the section that matches what you are doing.

**Start with the six onboarding pages below.** They are the complete path from install to daily use. The other sections are task-specific reference — open one when its description matches what you are doing.

## Core Model

    Planning: ROADMAP.md, milestone-*.md, requirements/, requirements/milestones/, session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

Use roadmap, milestone, and session-note files for project planning and narrative. Use SDLC-SPDD artifacts for governed execution and durable agent memory.

**How do Planning, SPDD, and SDLC fit together in practice?** → [Three-part operating path](three-part-operating-path.md)

## If You Are New, Read These in Order

1. [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md) — hands-on first session from install to memory capture.
2. [Three-part operating path](three-part-operating-path.md) — how Planning, SPDD, and SDLC work together end to end.
3. [10,000-foot view](ten-thousand-foot-view.md) — the high-level model, artifacts, skills, and workflow.
4. [Installing into your project](installing-into-your-project.md) — fresh install, upgrade path, verification, and troubleshooting.
5. [Top useful concepts and commands](useful-concepts-and-commands.md) — Work IDs, canvases, sessions, commands, and prompt patterns.
6. [Maintaining your project](maintaining-your-project.md) — upgrades, memory hygiene, canvas sync, links, and session maintenance.

**Workflow CLI reference** (pointer, phase tracking, team registry): [agent-context/README.md](../agent-context/README.md#sdlc-pointer-current-choretask) — installed in target projects at `agent-context/README.md`.

You can treat these six pages as the canonical onboarding path.

## If You Are Installing or Upgrading

| Guide | Use it when |
|-------|-------------|
| [Installing into your project](installing-into-your-project.md) | You are adding SDLC-SPDD to a target application for the first time |
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
| [Jira runbook](jira-runbook.md) | You need to create Jira issues or keep Jira synchronized with SDLC-SPDD artifacts |
| [Integration linking](integration-linking.md) | You need to link canvases to Jira, GitHub issues, pull requests, or GitHub Pages |
| [GitHub project setup](github-project-setup.md) | You need labels, milestones, and issue template conventions |
| [Installing into your project](installing-into-your-project.md) | You need target-project CI checks (adapter parity workflow and script validation) |

## If You Are Contributing or Editing Docs

| Guide | Use it when |
|-------|-------------|
| [CONTRIBUTING.md](../CONTRIBUTING.md) | You are changing scripts or documentation — includes orchestrator vs target paths and a consistency checklist |
| [Guide RAG research and dogfooding](guide-rag-research-and-dogfooding.md) | You use Embabel Guide + MCP for `/sdlc-spdd-analysis` or want the framework self-improvement loop explained |
| [Narrated demos bundle](demos/README.md) | You maintain or extend the docgen bundle under `docs/demos/` |
| [TESTING.md](../TESTING.md) | You need the command-testing confidence stack (CI gates, local smoke, planning-sync verification) |
| [Design decisions](design-decisions.md) | You need rationale for major choices (including planned-but-not-installed features) |

## What Each Part Brings (read before deep theory)

Start here when you want to know **why** each part exists. One page per part:

| Guide | Answers |
|-------|---------|
| [What planning brings](what-planning-brings.md) | Why roadmap, milestones, and session notes matter |
| [What SPDD brings](what-spdd-brings.md) | Why the REASONS Canvas governs execution |
| [What SDLC brings](what-sdlc-brings.md) | Why lifecycle phases and session handoffs matter |

## Deep Theory (after value guides)

Read these when you need historical context, compliance detail, or repository architecture — not for day-one onboarding:

| Guide | Use it when |
|-------|-------------|
| [Hybrid SDLC Agents + SPDD model](hybrid-model.md) | You want the original two-influence story and how Planning was added |
| [Architecture](architecture.md) | You want the five delivery concerns built on the three parts |
| [Context loading and scaling](context-loading-and-scaling.md) | Tiers, scaling, and [bootstrap + index-based loading](context-loading-and-scaling.md#bootstrap-and-index-based-loading) |
| [SPDD compliance](spdd-compliance.md) | You need to verify against Structured Prompt-Driven Development expectations |
| [Chelsea Troy and the framework](chelsea-troy-and-the-framework.md) | You want the LLM context/judgment rationale behind index-driven loading |
| [SDLC Agents and the framework](sdlc-agents-and-the-framework.md) | You want progressive disclosure, `#SkillName`, and extensions mapped to this orchestrator |
| [Design decisions](design-decisions.md) | You want the rationale behind major choices |

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
| [Roadmap](roadmap.md) | You want planned future capabilities |

## Quick Start (one path)

Follow the adoption path in the repository [README](../README.md#the-adoption-path): install → first day → three-part operating path → daily prompts.

After install, target-local copies of these docs live at `docs/sdlc-spdd/` in your application. Cursor/Copilot/Claude Code slash-command examples: [Initialization and invocation](initialization-and-invocation.md).
