# Documentation

Use this hub to choose the right guide for your current task. If you are new, read the first section in order. If you are already operating a project, jump to the section that matches what you are doing.

## If You Are New, Read These in Order

1. [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md) — a guided first-session path from install to memory capture.
2. [10,000-foot view](ten-thousand-foot-view.md) — the high-level model, artifacts, skills, and workflow.
3. [Installing into your project](installing-into-your-project.md) — fresh install, upgrade path, verification, and troubleshooting.
4. [Top useful concepts and commands](useful-concepts-and-commands.md) — Work IDs, canvases, sessions, commands, and prompt patterns.
5. [Maintaining your project](maintaining-your-project.md) — upgrades, memory hygiene, canvas sync, links, and session maintenance.

You can treat these five pages as the canonical onboarding path.

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
| [Daily runbook](daily-runbook.md) | You need repeatable day-to-day actions for triage, planning, coding, review, retro, sync, and handoff |
| [Initialization and invocation](initialization-and-invocation.md) | You need concrete examples for starting work and invoking each SDLC-SPDD skill |
| [Top useful concepts and commands](useful-concepts-and-commands.md) | You want a fast reference for common commands and prompt patterns |
| [Cheat sheet](sdlc-spdd-cheat-sheet.md) | You want a one-page PDF-friendly quick reference |

## If You Are Integrating with Jira or GitHub

| Guide | Use it when |
|-------|-------------|
| [Jira runbook](jira-runbook.md) | You need to create Jira issues or keep Jira synchronized with SDLC-SPDD artifacts |
| [Integration linking](integration-linking.md) | You need to link canvases to Jira, GitHub issues, pull requests, or GitHub Pages |
| [GitHub project setup](github-project-setup.md) | You need labels, milestones, and issue template conventions |

## If You Want the Architecture and Theory

| Guide | Use it when |
|-------|-------------|
| [Hybrid SDLC Agents + SPDD model](hybrid-model.md) | You want to understand how SDLC Agents lifecycle practices and SPDD prompt governance fit together |
| [SPDD compliance](spdd-compliance.md) | You need to verify the workflow against Structured Prompt-Driven Development expectations |
| [Architecture](architecture.md) | You want the repository architecture and artifact model |
| [Design decisions](design-decisions.md) | You want the rationale behind major choices |

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
