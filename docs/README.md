# Documentation Hub

Use these guides to install the scaffold, invoke the SDLC-SPDD commands, link work to external systems, and run daily delivery actions.

## Start Here

| Guide | Use it for |
|-------|------------|
| [Hybrid SDLC Agents + SPDD model](hybrid-model.md) | How SDLC Agents lifecycle patterns combine with SPDD/REASONS prompt governance |
| [Agent session scripts](agent-session-scripts.md) | Runnable setup, session resume/resync, and memory capture commands |
| [Framework upgrade](framework-upgrade.md) | Upgrade older target projects without overwriting implementation files or accumulated memory |
| [Workflow](workflow.md) | The SDLC-SPDD lifecycle and quality gates |
| [Cursor usage](cursor-usage.md) | Installing and invoking Cursor commands |
| [GitHub Copilot usage](copilot-usage.md) | Installing and invoking Copilot instructions and prompt files |
| [Initialization and invocation](initialization-and-invocation.md) | First run, starting work, asking context-preserving questions, and invoking each SDLC skill in Cursor or Copilot |
| [Daily runbook](daily-runbook.md) | Repeatable daily actions for triage, planning, coding, review, retro, and sync |
| [Integration linking](integration-linking.md) | Linking canvases and work items to Jira-based systems or GitHub Pages |
| [Jira runbook](jira-runbook.md) | Creating new Jira issues and keeping Jira synchronized with SDLC-SPDD artifacts |
| [SPDD compliance](spdd-compliance.md) | Mapping this scaffold to the Structured Prompt-Driven Development contract |
| [Cheat sheet](sdlc-spdd-cheat-sheet.md) | One-page PDF-friendly quick reference |

## Existing Reference Guides

| Guide | Use it for |
|-------|------------|
| [Architecture](architecture.md) | Repository architecture and orchestration model |
| [Design decisions](design-decisions.md) | Design rationale and tradeoffs |
| [GitHub project setup](github-project-setup.md) | Labels, milestones, and issue templates |
| [Java Spring Boot usage](java-spring-boot-usage.md) | Spring Boot patterns and stack-specific guidance |
| [Tekton usage](tekton-usage.md) | Tekton pipeline example guidance |
| [Roadmap](roadmap.md) | Planned future capabilities |

## Common Entry Points

Install the scaffold into a target application:

    ./scripts/setup-agent-prompts.sh --target /path/to/your/project --all

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
