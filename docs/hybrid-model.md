# Hybrid SDLC Agents + SPDD Model

> Deep theory. For onboarding, read [Three-part operating path](three-part-operating-path.md) and the [What each part brings](README.md#what-each-part-brings-read-before-deep-theory) value guides first. This page explains the historical SDLC + SPDD influences and how Planning was added as a third part.

This project is intentionally hybrid. It combines the SDLC Agents lifecycle and context-engineering model with SPDD's REASONS Canvas and prompt-governance contract, then connects both to the planning layer (`ROADMAP.md`, `milestone-*.md`, `requirements/`, `session-notes/`). These map to the three parts: SDLC, SPDD, and Planning.

## Three-Layer Operating Model

    ROADMAP.md / milestone-*.md / requirements/milestones/ / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

The first layer is for humans and project narrative. The second layer is for agents and governed work-item execution. The third layer is the implementation evidence.

## Why Hybrid

SDLC Agents and SPDD solve related but different problems:

| Need | SDLC Agents contribution | SPDD contribution | This scaffold's hybrid behavior |
|------|--------------------------|-------------------|---------------------------------|
| Keep AI work disciplined | Specialized lifecycle agents | Versioned structured prompts | Each command acts as a phase-specific agent operating on versioned artifacts |
| Keep work tied to milestones | Handoffs and progressive context | Canvas metadata and Work IDs | Roadmap and milestone docs map into Work IDs and canvases |
| Prevent structural debt | Architecture-first validation | Structure and Safeguards sections | `/sdlc-spdd-architect` validates the canvas before coding |
| Avoid ad hoc prompt drift | Agent handoffs and memory | REASONS Canvas as contract | Work moves through canvas, progress log, review, sync, and retro artifacts |
| Keep context focused | Progressive disclosure | Canvas references and scoped operations | Prompts load only the relevant files, Work ID, memory, and operation |
| Learn across tasks | Retro and curator patterns | Reusable prompt assets | Session notes, retro, and memory accumulate reusable learning |
| Support multiple assistants | Tool adapters for Copilot, Cursor, and others | Prompt files as portable Markdown | Cursor commands, Copilot prompt files, and Claude Code commands share the same lifecycle semantics |

## What Comes from SDLC Agents

This scaffold adopts these SDLC Agents ideas:

- **Specialized phases**: Initializer, Planning, Architect, Coding, Code Review, Retro, and knowledge curation responsibilities.
- **Architecture-first flow**: architecture is validated before code changes begin.
- **Incremental coding**: coding agents implement one approved operation at a time.
- **Context engineering**: each phase should read only the artifacts relevant to the current Work ID and operation.
- **Continual learning**: retros capture lessons into durable memory.
- **Guardrails**: no-code phases, operation boundaries, review gates, and safeguards are explicit.
- **Multi-assistant adapters**: the same lifecycle can be invoked from Cursor, GitHub Copilot, or Claude Code.

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

`/sdlc-spdd-*` skills run in **AI chat** (Cursor/Copilot/Claude Code), not a terminal. [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

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

    Roadmap, milestone, external request, or Jira issue
      -> optional milestone-to-work mapping
      -> Planning Agent creates REASONS Canvas
      -> Architect Agent hardens the canvas
      -> Coding Agent implements one Operation
      -> Review Agent checks code against the canvas
      -> Prompt Update Agent handles changed intent
      -> Sync Agent reconciles accepted implementation drift
      -> Retro Agent captures reusable learning
      -> roadmap/session-note summaries are refreshed

## Scripted Session Lifecycle

The hybrid model is operationalized with scripts:

| Need | Script | Hybrid role |
|------|--------|-------------|
| Install prompts and artifacts | `scripts/setup-agent-prompts.sh` | Creates assistant adapters plus SPDD artifact folders and SDLC memory/playbooks |
| Start a new session | `scripts/sdlc-spdd/sdlc.sh start` (or `start-agent-session.sh`) | Builds an SDLC handoff brief anchored to SPDD artifacts; sets pointer |
| Orient / team | `scripts/sdlc-spdd/sdlc.sh next`, `team`, `claim` | Local phase tracking + committed team registry |
| Resync previous work | `scripts/sdlc-spdd/resync-agent-session.sh` | Checks or reconciles canvas copies and validates the REASONS contract |
| Capture session learning | `scripts/sdlc-spdd/sdlc.sh capture` (or `capture-session-memory.sh`) | Guarded persist of retro-style memory for future agents |
| Create work from milestones | `scripts/sdlc-spdd/create-work-from-milestone.sh` | Maps project planning items into SDLC-SPDD Work IDs and draft canvases |
| Refresh roadmap | `scripts/sdlc-spdd/sync-roadmap-from-spdd.sh` | Summarizes governed canvas state back into `ROADMAP.md` |
| Import session notes | `scripts/sdlc-spdd/summarize-session-notes.sh` | Converts existing narrative session notes into durable memory |

Use these scripts around assistant invocations so context survives beyond chat history.

Concept guides: [What SDLC brings](what-sdlc-brings.md), [What SPDD brings](what-spdd-brings.md), [What planning brings](what-planning-brings.md). Prompt standards: [Session](session-prompt-standard.md), [SPDD](spdd-prompt-standard.md), [Planning](planning-prompt-standard.md).

## Context Loading Rules

Use SDLC Agents-style progressive disclosure with SPDD artifacts. Load only what the current phase needs; use indexes instead of directory scans. See [SDLC Agents and the framework](sdlc-agents-and-the-framework.md).

| Phase | Load this context | Avoid loading |
|-------|-------------------|---------------|
| Init | Repo layout, stack markers, existing memory | Full codebase unless needed for stack detection |
| Analysis | Requirement, `domain-index.md`, `context-index.md`, `code-areas.md`; scan only matched code areas | Unrelated modules, whole repo |
| Plan | `spdd/analysis/<WORK-ID>-analysis.md`, requirement, roadmap, milestone, source issue | Unrelated source files |
| Architect | Analysis + canvas, architecture notes, relevant interfaces, safeguards | Implementation details not needed for design |
| Code | Canvas, selected operation, relevant files, tests | Other operations or unrelated modules |
| API test | Canvas Requirements/Operations, implemented endpoints for this Work ID | Unrelated features |
| Review | Canvas, diff, tests, safeguards | New feature ideation |
| Prompt update | Canvas, changed requirement, source issue | Source code edits |
| Sync | Canvas, accepted code changes, review report | Unreviewed behavior changes |
| Retro | Canvas, progress log, review, sync | New implementation work |

## Skills and Extensions

SDLC Agents supports dynamic skill selection and extensions. This scaffold documents the same pattern in assistant-neutral form:

- Use `#SkillName` to request relevant skills, such as `#TDD`, `#java`, `#security`, or `#tekton`.
- Use `!SkillName` to exclude irrelevant skills, such as `!Kafka`.
- Store reusable project guidance in `agent-context/memory/` and `agent-context/playbooks/`.
- Resolve skills and phase extensions with `./scripts/sdlc-spdd/resolve-agent-context.sh` (see [SDLC Agents and the framework](sdlc-agents-and-the-framework.md)).
- Add project-specific rules under `agent-context/extensions/` (SDLC Agents agent folder names) — loaded via resolve script or session brief **Resolved Context**.
- Use `ROADMAP.md`, `milestone-*.md`, and `session-notes/` for human-level planning context, not as replacements for the REASONS Canvas.

Example:

    /sdlc-spdd-analysis Add order processing API #java #TDD !Kafka
    ./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id <WORK-ID>
    /sdlc-spdd-plan @spdd/analysis/<WORK-ID>-analysis.md

The expected behavior is to load Java and TDD guidance, avoid Kafka assumptions, and record the selected skills in the canvas or progress log.

## What This Is Not

This scaffold is not a full clone of SDLC Agents and is not a drop-in replacement for OpenSPDD.

Current boundaries:

- No compiled multi-agent runtime.
- No automatic dynamic skill loader yet.
- No automatic Jira service synchronization.
- No mandatory dependency on the upstream `openspdd` CLI.
- Cursor, Copilot, and Claude Code are supported through Markdown prompt adapters.

The hybrid contract is repository-based: role-separated lifecycle prompts from SDLC Agents plus versioned REASONS Canvas governance from SPDD.

## Read Next

- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md)
- [10,000-foot view](ten-thousand-foot-view.md)
- [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md)
- [Top useful concepts and commands](useful-concepts-and-commands.md)
