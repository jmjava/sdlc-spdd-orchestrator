# Documentation

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

You can treat these six pages as the canonical onboarding path.

## If You Are Installing or Upgrading

| Guide | Use it when |
|-------|-------------|
| [Installing into your project](installing-into-your-project.md) | You are adding SDLC-SPDD to a target application for the first time |
| [Framework upgrade](framework-upgrade.md) | A target app already has an older SDLC-SPDD install |
| [Cursor usage](cursor-usage.md) | You only need Cursor command setup and invocation |
| [GitHub Copilot usage](copilot-usage.md) | You only need Copilot instructions and prompt files |
| [Agent session scripts](agent-session-scripts.md) | You need the setup/resync/capture scripts and target-local runtime commands |

## If You Are Using This Daily

| Guide | Use it when |
|-------|-------------|
| [Three-part operating path](three-part-operating-path.md) | You need the canonical Planning → SPDD → SDLC loop for a session or work item |
| [Session prompt standard](session-prompt-standard.md) | You need copy-paste prompts that bridge milestones, SPDD, and SDLC lifecycle |
| [Daily runbook](daily-runbook.md) | You need repeatable day-to-day actions for triage, planning, coding, review, retro, sync, and handoff |
| [Initialization and invocation](initialization-and-invocation.md) | You need concrete examples for starting work and invoking each SDLC-SPDD skill |
| [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md) | You use `ROADMAP.md`, `milestone-*.md`, and `session-notes/` to track project progress |
| [Top useful concepts and commands](useful-concepts-and-commands.md) | You want a fast reference for common commands and prompt patterns |
| [Cheat sheet](sdlc-spdd-cheat-sheet.md) | You want a one-page PDF-friendly quick reference |

## If You Are Integrating with Jira or GitHub

| Guide | Use it when |
|-------|-------------|
| [Jira runbook](jira-runbook.md) | You need to create Jira issues or keep Jira synchronized with SDLC-SPDD artifacts |
| [Integration linking](integration-linking.md) | You need to link canvases to Jira, GitHub issues, pull requests, or GitHub Pages |
| [GitHub project setup](github-project-setup.md) | You need labels, milestones, and issue template conventions |

## If You Are Contributing or Editing Docs

| Guide | Use it when |
|-------|-------------|
| [CONTRIBUTING.md](../CONTRIBUTING.md) | You are changing scripts or documentation — includes orchestrator vs target paths and a consistency checklist |
| [Design decisions](design-decisions.md) | You need rationale for major choices (including planned-but-not-installed features) |

## If You Want the Architecture and Theory

| Guide | Use it when |
|-------|-------------|
| [What SDLC brings](what-sdlc-brings.md) | You want a single-page answer for what SDLC lifecycle discipline contributes |
| [What SPDD brings](what-spdd-brings.md) | You want a single-page answer for what REASONS Canvas governance contributes |
| [What planning brings](what-planning-brings.md) | You want a single-page answer for what roadmap, milestones, and session notes contribute |
| [Hybrid SDLC Agents + SPDD model](hybrid-model.md) | You want to understand how SDLC Agents lifecycle practices and SPDD prompt governance fit together |
| [SPDD compliance](spdd-compliance.md) | You need to verify the workflow against Structured Prompt-Driven Development expectations |
| [Architecture](architecture.md) | You want the repository architecture and artifact model |
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

## Common Entry Points

First day path:

    Read first-day-with-sdlc-spdd.md

Understand the system:

    Read ten-thousand-foot-view.md

Install the scaffold into a target application:

    ./scripts/setup-agent-prompts.sh --target /path/to/your/project --all

After install, target-local usage docs are available at:

    /path/to/your/project/docs/sdlc-spdd/

Initialize the application context in Cursor:

    /sdlc-spdd-init

Initialize the application context in GitHub Copilot Chat:

    /sdlc-spdd-init

Start new work from a requirement document:

    /sdlc-spdd-plan @requirements/my-feature.md

Start one approved implementation task:

    /sdlc-spdd-code @spdd/canvas/FEAT-001-my-feature.md

Capture session memory:

    cd /path/to/your/project
    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id FEAT-001-my-feature --phase code --summary "Completed T01" --validation "tests passed"

Upgrade an older installation:

    ./scripts/upgrade-project.sh --target /path/to/your/project --all
