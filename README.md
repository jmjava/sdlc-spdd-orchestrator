# SDLC-SPDD Orchestrator

A Cursor-first AI software delivery scaffold that combines SDLC Agents' multi-agent lifecycle with OpenSPDD's REASONS Canvas design-contract model.

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

## Why Combine SDLC Agents and OpenSPDD?

SDLC Agents provides the software delivery lifecycle and role separation.

OpenSPDD provides the structured design contract.

Together they create a practical workflow where AI agents do not just generate code; they operate against an explicit contract.

## Quick Start

Clone this repo:

    git clone https://github.com/jmjava/sdlc-spdd-orchestrator.git
    cd sdlc-spdd-orchestrator

Install into a target project for Cursor:

    ./scripts/init-project.sh --target /path/to/your/project --cursor

Install into a target project for GitHub Copilot:

    ./scripts/init-project.sh --target /path/to/your/project --copilot

Install both assistant integrations:

    ./scripts/init-project.sh --target /path/to/your/project --cursor --copilot

Then in Cursor or GitHub Copilot Chat:

    /sdlc-spdd-init
    /sdlc-spdd-plan @requirements/my-feature.md
    /sdlc-spdd-architect @spdd/canvas/FEAT-001-my-feature.md
    /sdlc-spdd-code @spdd/tasks/FEAT-001/T01-task.md
    /sdlc-spdd-review @spdd/canvas/FEAT-001-my-feature.md
    /sdlc-spdd-retro @spdd/canvas/FEAT-001-my-feature.md
    /sdlc-spdd-sync @spdd/canvas/FEAT-001-my-feature.md

## Recommended Workflow

    Requirement
      -> Plan
      -> Architect
      -> Code Task 1
      -> Review
      -> Code Task 2
      -> Review
      -> Retro
      -> Sync

## Repository Layout

| Path | Purpose |
|------|---------|
| `templates/` | REASONS Canvas, Cursor commands, Copilot prompts, stack rules |
| `scripts/` | Init, detect, validate, sync helpers |
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
- [Architecture](docs/architecture.md)
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
