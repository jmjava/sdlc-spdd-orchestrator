# Hybrid SDLC Agents + SPDD Model

This project is intentionally hybrid. It combines the SDLC Agents lifecycle and context-engineering model with SPDD's REASONS Canvas and prompt-governance contract.

## Why Hybrid

SDLC Agents and SPDD solve related but different problems:

| Need | SDLC Agents contribution | SPDD contribution | This scaffold's hybrid behavior |
|------|--------------------------|-------------------|---------------------------------|
| Keep AI work disciplined | Specialized lifecycle agents | Versioned structured prompts | Each command acts as a phase-specific agent operating on versioned artifacts |
| Prevent structural debt | Architecture-first validation | Structure and Safeguards sections | `/sdlc-spdd-architect` validates the canvas before coding |
| Avoid ad hoc prompt drift | Agent handoffs and memory | REASONS Canvas as contract | Work moves through canvas, progress log, review, sync, and retro artifacts |
| Keep context focused | Progressive disclosure | Canvas references and scoped operations | Prompts load only the relevant files, Work ID, memory, and operation |
| Learn across tasks | Retro and curator patterns | Reusable prompt assets | Retro updates `agent-context/memory/`; sync keeps canvas current |
| Support multiple assistants | Tool adapters for Copilot, Cursor, and others | Prompt files as portable Markdown | Cursor commands and Copilot prompt files share the same lifecycle semantics |

## What Comes from SDLC Agents

This scaffold adopts these SDLC Agents ideas:

- **Specialized phases**: Initializer, Planning, Architect, Coding, Code Review, Retro, and knowledge curation responsibilities.
- **Architecture-first flow**: architecture is validated before code changes begin.
- **Incremental coding**: coding agents implement one approved operation at a time.
- **Context engineering**: each phase should read only the artifacts relevant to the current Work ID and operation.
- **Continual learning**: retros capture lessons into durable memory.
- **Guardrails**: no-code phases, operation boundaries, review gates, and safeguards are explicit.
- **Multi-assistant adapters**: the same lifecycle can be invoked from Cursor or GitHub Copilot.

SDLC Agents reference:

- https://github.com/dsilahcilar/sdlc-agents

## What Comes from SPDD

This scaffold adopts these SPDD ideas:

- **Prompts as first-class artifacts** stored with the repository.
- **REASONS Canvas** as the design contract:
  - Requirements
  - Entities
  - Approach
  - Structure
  - Operations
  - Norms
  - Safeguards
- **Prompt-first behavior changes**: when business intent changes, update the canvas before code.
- **Closed-loop synchronization**: when implementation reality changes, review and sync the canvas.
- **Iterative review**: compare generated or edited code against the structured prompt contract.

SPDD reference:

- https://martinfowler.com/articles/structured-prompt-driven/

## Hybrid Command Mapping

| Hybrid skill | SDLC Agents role | SPDD role | Primary artifacts |
|--------------|------------------|-----------|-------------------|
| `/sdlc-spdd-init` | Initializer | Establish prompt/artifact workspace | `requirements/`, `spdd/`, `agent-context/` |
| `/sdlc-spdd-plan` | Planning Agent | Generate REASONS Canvas from requirement | `spdd/canvas/<WORK-ID>.md`, feature workspace |
| `/sdlc-spdd-architect` | Architect Agent | Validate Entities, Approach, Structure, Norms, Safeguards | Canvas readiness decision |
| `/sdlc-spdd-code` | Coding Agent | Execute one approved Operation | Code, tests, progress log |
| `/sdlc-spdd-review` | Code Review Agent | Compare implementation to REASONS contract | `spdd/reviews/` |
| `/sdlc-spdd-prompt-update` | Planning/Architect handoff | Update prompt first when intent changes | Canvas and progress log |
| `/sdlc-spdd-retro` | Retro Agent | Convert lessons into reusable assets | `agent-context/memory/` |
| `/sdlc-spdd-sync` | Curator-like knowledge maintenance | Reconcile code reality back into prompt artifacts | `spdd/sync/`, updated canvas |

## Hybrid Workflow

    External request or Jira issue
      -> Planning Agent creates REASONS Canvas
      -> Architect Agent hardens the canvas
      -> Coding Agent implements one Operation
      -> Review Agent checks code against the canvas
      -> Prompt Update Agent handles changed intent
      -> Sync Agent reconciles accepted implementation drift
      -> Retro Agent captures reusable learning

## Scripted Session Lifecycle

The hybrid model is operationalized with scripts:

| Need | Script | Hybrid role |
|------|--------|-------------|
| Install prompts and artifacts | `scripts/setup-agent-prompts.sh` | Creates assistant adapters plus SPDD artifact folders and SDLC memory/playbooks |
| Start a new session | `scripts/sdlc-spdd/start-agent-session.sh` | Builds an SDLC handoff brief anchored to SPDD artifacts |
| Resync previous work | `scripts/sdlc-spdd/resync-agent-session.sh` | Checks or reconciles canvas copies and validates the REASONS contract |
| Capture session learning | `scripts/sdlc-spdd/capture-session-memory.sh` | Persists retro-style memory for future agents |

Use these scripts around assistant invocations so context survives beyond chat history.

## Context Loading Rules

Use SDLC Agents-style progressive disclosure with SPDD artifacts:

| Phase | Load this context | Avoid loading |
|-------|-------------------|---------------|
| Init | Repo layout, stack markers, existing memory | Full codebase unless needed for stack detection |
| Plan | Requirement, source issue, relevant modules, memory | Unrelated source files |
| Architect | Canvas, architecture notes, relevant interfaces, safeguards | Implementation details not needed for design |
| Code | Canvas, selected operation, relevant files, tests | Other operations or unrelated modules |
| Review | Canvas, diff, tests, safeguards | New feature ideation |
| Prompt update | Canvas, changed requirement, source issue | Source code edits |
| Sync | Canvas, accepted code changes, review report | Unreviewed behavior changes |
| Retro | Canvas, progress log, review, sync | New implementation work |

## Skills and Extensions

SDLC Agents supports dynamic skill selection and extensions. This scaffold documents the same pattern in assistant-neutral form:

- Use `#SkillName` to request relevant skills, such as `#TDD`, `#java`, `#security`, or `#tekton`.
- Use `!SkillName` to exclude irrelevant skills, such as `!Kafka`.
- Store reusable project guidance in `agent-context/memory/` today.
- If a team wants SDLC Agents-style extensions, add Markdown guidance under `agent-context/playbooks/` or a project-local `agent-context/extensions/` folder and reference it from the active prompt.

Example:

    /sdlc-spdd-plan Add order processing API #java #TDD !Kafka

The expected behavior is to load Java and TDD guidance, avoid Kafka assumptions, and record the selected skills in the canvas or progress log.

## What This Is Not

This scaffold is not a full clone of SDLC Agents and is not a drop-in replacement for OpenSPDD.

Current boundaries:

- No compiled multi-agent runtime.
- No automatic dynamic skill loader yet.
- No automatic Jira service synchronization.
- No mandatory dependency on the upstream `openspdd` CLI.
- Cursor and Copilot are supported through Markdown prompt adapters.

The hybrid contract is repository-based: role-separated lifecycle prompts from SDLC Agents plus versioned REASONS Canvas governance from SPDD.

## Read Next

- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md)
- [10,000-foot view](ten-thousand-foot-view.md)
- [Top useful concepts and commands](useful-concepts-and-commands.md)
