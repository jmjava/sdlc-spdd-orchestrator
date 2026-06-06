# SDLC-SPDD Orchestrator

A multi-assistant AI software delivery scaffold that combines SDLC Agents' role-separated lifecycle with SPDD's REASONS Canvas design-contract model.

## What This Is

This project provides a practical orchestration layer for AI-assisted software development.

It helps AI coding tools move through a disciplined lifecycle:

1. Initialize project context
2. Plan from requirements
3. Create a REASONS Canvas
4. Review architecture
5. Implement one task at a time
6. Review against the contract
7. Capture retro learnings
8. Sync design docs with implementation reality

## What This Is Not

This is not initially a full agent runtime.

It is not a replacement for Cursor, Claude Code, Copilot, OpenSPDD, or SDLC Agents.

It is a scaffold that makes those tools more disciplined and repeatable.

## Why Combine SDLC Agents and SPDD?

SDLC Agents provides the software delivery lifecycle, specialized agent roles, architecture-first handoffs, progressive context loading, continual learning, and guardrails.

SPDD provides the structured prompt contract through the REASONS Canvas and the rule that prompt artifacts evolve with code.

Together they create a practical workflow where AI agents do not just generate code; they operate in role-specific phases against an explicit, versioned design contract.

## Quick Start

If you are new to the project, start with [First day with SDLC-SPDD](docs/first-day-with-sdlc-spdd.md) and the [10,000-foot view](docs/ten-thousand-foot-view.md).

Clone this repo:

    git clone https://github.com/jmjava/sdlc-spdd-orchestrator.git
    cd sdlc-spdd-orchestrator

Install into a target project for Cursor:

    ./scripts/init-project.sh --target /path/to/your/project --cursor

Install into a target project for GitHub Copilot:

    ./scripts/init-project.sh --target /path/to/your/project --copilot

Install both assistant integrations:

    ./scripts/init-project.sh --target /path/to/your/project --cursor --copilot

Or run the integrated setup wrapper:

    ./scripts/setup-agent-prompts.sh --target /path/to/your/project --all

Upgrade an existing project initialized by an older version without touching application source, canvases, feature workspaces, or existing memory:

    ./scripts/upgrade-project.sh --target /path/to/your/project --all

Then in Cursor or GitHub Copilot Chat:

    /sdlc-spdd-init
    /sdlc-spdd-plan @requirements/my-feature.md
    /sdlc-spdd-architect @spdd/canvas/FEAT-001-my-feature.md
    /sdlc-spdd-code @spdd/canvas/FEAT-001-my-feature.md operation T01
    /sdlc-spdd-review @spdd/canvas/FEAT-001-my-feature.md
    /sdlc-spdd-prompt-update @spdd/canvas/FEAT-001-my-feature.md
    /sdlc-spdd-retro @spdd/canvas/FEAT-001-my-feature.md
    /sdlc-spdd-sync @spdd/canvas/FEAT-001-my-feature.md

For a new agent session, resync previous work and create a session brief:

    cd /path/to/your/project
    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id FEAT-001-my-feature --check-only
    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-my-feature --phase code

At the end of a session, persist memory for future agents:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id FEAT-001-my-feature --phase code --summary "Completed T01" --validation "tests passed" --next "/sdlc-spdd-review @spdd/canvas/FEAT-001-my-feature.md"

## Recommended Workflow

    Requirement
      -> Plan
      -> Architect
      -> Code Task 1
      -> Review
      -> Code Task 2
      -> Review
      -> Prompt Update when intent changes
      -> Retro
      -> Sync

## Repository Layout

| Path | Purpose |
|------|---------|
| `templates/` | REASONS Canvas, Cursor commands, Copilot prompts, stack rules |
| `scripts/` | Init, prompt setup, session start/resync/capture, detect, validate, sync helpers |
| `agent-context/` | Memory, playbooks, harness for this repo |
| `examples/` | Reference workflows (Spring Boot, Tekton) |
| `docs/` | Architecture, workflow, and usage guides |

## Java / Spring Boot Usage

This scaffold works especially well for Java/Spring Boot projects because it can encode project-specific rules around:

- Controllers
- Services
- Repositories
- DTOs
- Validation
- Transactions
- Tests
- Build tooling
- Architecture boundaries

See [docs/java-spring-boot-usage.md](docs/java-spring-boot-usage.md) and [examples/spring-boot-order-api/](examples/spring-boot-order-api/).

## Documentation

- [Documentation hub](docs/README.md)
- [First day with SDLC-SPDD](docs/first-day-with-sdlc-spdd.md)
- [10,000-foot view](docs/ten-thousand-foot-view.md)
- [Installing into your project](docs/installing-into-your-project.md)
- [Maintaining your project](docs/maintaining-your-project.md)
- [Top useful concepts and commands](docs/useful-concepts-and-commands.md)
- [Architecture](docs/architecture.md)
- [Hybrid SDLC Agents + SPDD model](docs/hybrid-model.md)
- [Agent session scripts](docs/agent-session-scripts.md)
- [Framework upgrade](docs/framework-upgrade.md)
- [Workflow](docs/workflow.md)
- [Cursor usage](docs/cursor-usage.md)
- [GitHub Copilot usage](docs/copilot-usage.md)
- [Initialization and invocation](docs/initialization-and-invocation.md)
- [Daily runbook](docs/daily-runbook.md)
- [Integration linking](docs/integration-linking.md)
- [Jira runbook](docs/jira-runbook.md)
- [SPDD compliance](docs/spdd-compliance.md)
- [Cheat sheet](docs/sdlc-spdd-cheat-sheet.md)
- [GitHub project setup](docs/github-project-setup.md)
- [Tekton usage](docs/tekton-usage.md)
- [Design decisions](docs/design-decisions.md)
- [Roadmap](docs/roadmap.md)

## License

MIT

## Attribution

This project is inspired by:

- [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents): multi-agent software delivery lifecycle
- [OpenSPDD](https://github.com/gszhangwei/open-spdd): structured prompt-driven development and REASONS Canvas style design contracts

This project is not an official extension of either project unless that relationship is established later.
