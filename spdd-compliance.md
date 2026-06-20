# SPDD Compliance

> Deep theory. For onboarding, read [Three-part operating path](three-part-operating-path.md) and [What SPDD brings](what-spdd-brings.md) first. This page is for compliance verification and Fowler/SPDD contract detail.

This project follows Structured Prompt-Driven Development (SPDD) as described in Martin Fowler's article, [Structured-Prompt-Driven Development](https://martinfowler.com/articles/structured-prompt-driven/), inside a hybrid lifecycle influenced by [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents).

SPDD treats prompts as first-class delivery artifacts that are version controlled, reviewed, reused, and improved over time. This scaffold implements that contract with REASONS Canvas files, lifecycle prompt templates, assistant command prompts, progress logs, review reports, sync logs, and reusable project memory.

For the SDLC Agents side of the hybrid, see [hybrid-model.md](hybrid-model.md). For copy-paste SPDD prompts, see [SPDD prompt standard](spdd-prompt-standard.md). For planning-layer prompts, see [Planning prompt standard](planning-prompt-standard.md).

Project-level planning documents are also supported:

    ROADMAP.md / milestone-*.md / requirements/milestones/ / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

These planning documents inform SPDD work, but they do not replace the REASONS Canvas. The canvas remains the governed prompt contract for each Work ID.

## Compliance Summary

| SPDD expectation | How this scaffold satisfies it |
|------------------|--------------------------------|
| Prompts are first-class artifacts | Cursor commands, Copilot prompt files, Claude Code commands, REASONS Canvas files, and agent memory live in the repository |
| Prompts are version controlled | Generated canvases and prompt assets are normal files committed with code |
| Business intent is explicit before coding | `/sdlc-spdd-analysis` produces scoped analysis context; `/sdlc-spdd-plan` creates the REASONS Canvas from that artifact |
| Abstraction comes before execution | Analysis (Fowler Step 3) precedes canvas; `/sdlc-spdd-architect` hardens intent before `/sdlc-spdd-code` |
| Code generation has boundaries | `/sdlc-spdd-code` implements exactly one approved operation; `/sdlc-spdd-api-test` verifies at the API boundary (Fowler Step 5) |
| Review checks intent, not only code | `/sdlc-spdd-review` compares implementation against all REASONS sections |
| Prompt and code evolve together | `/sdlc-spdd-sync` reconciles implementation reality back into canvas artifacts |
| Learnings become reusable | `/sdlc-spdd-retro` updates project memory and reusable patterns |

## REASONS Canvas Contract

Every compliant canvas must contain these sections:

| Section | Contract |
|---------|----------|
| R - Requirements | Problem, business outcome, acceptance criteria, definition of done |
| E - Entities | Domain entities, relationships, inputs, outputs, and external systems |
| A - Approach | Strategy for satisfying the requirement |
| S - Structure | Components, modules, boundaries, dependencies, and file locations |
| O - Operations | Concrete, testable, ordered implementation steps |
| N - Norms | Reusable engineering standards and conventions |
| S - Safeguards | Non-negotiable constraints, invariants, security rules, and performance limits |

Validate canvas structure with (runtime scripts live under `scripts/sdlc-spdd/` in your project):

    ./scripts/sdlc-spdd/validate-reasons-canvas.sh spdd/canvas/

## Workflow Contract

Use this closed loop:

    Business input
      -> Roadmap, milestone, requirement, Jira issue, or session note
      -> Analysis context (domain keywords, scoped code scan)
      -> REASONS Canvas
      -> Architecture hardening
      -> One operation of code
      -> API test verification
      -> Review against canvas
      -> Sync prompt artifacts with reality
      -> Retro into reusable memory

## Fowler / OpenSPDD Command Mapping

This scaffold implements Martin Fowler's [SPDD article](https://martinfowler.com/articles/structured-prompt-driven/) workflow through **Cursor**, **GitHub Copilot**, and **Claude Code** command packs (same semantics, different install paths). It does not require the upstream `openspdd` CLI.

| Fowler / OpenSPDD | Hybrid command | Cursor | Copilot | Claude |
|-------------------|----------------|--------|---------|--------|
| (planning / story) | Milestone + `create-work-from-milestone.sh` | — | — | — |
| `/spdd-analysis` | `/sdlc-spdd-analysis` | `.cursor/commands/` | `.github/prompts/` | `.claude/commands/` |
| `/spdd-reasons-canvas` | `/sdlc-spdd-plan` (after analysis) | same | same | same |
| (architecture hardening) | `/sdlc-spdd-architect` | same | same | same |
| `/spdd-generate` | `/sdlc-spdd-code` | same | same | same |
| `/spdd-api-test` | `/sdlc-spdd-api-test` | same | same | same |
| (code review) | `/sdlc-spdd-review` | same | same | same |
| `/spdd-prompt-update` | `/sdlc-spdd-prompt-update` | same | same | same |
| `/spdd-sync` | `/sdlc-spdd-sync` | same | same | same |
| (learnings) | `/sdlc-spdd-retro` | SDLC extension | same | same |

**Decision memory** (Fowler's cross-iteration asset accumulation) lives in:

| Artifact | Role |
|----------|------|
| `spdd/analysis/<WORK-ID>-analysis.md` | Step 3 strategic analysis (domain keywords, scoped areas) |
| `spdd/canvas/<WORK-ID>.md` | REASONS Canvas governing prompt |
| `agent-context/memory/domain-index.md` | Keyword → area → analysis/canvas lookup |
| `agent-context/memory/context-index.md` | Area → context (Kinds: analysis, session, decision, pitfall, pattern) |
| `agent-context/memory/code-areas.md` | Canonical code-area registry |

After `/sdlc-spdd-analysis`, run:

    ./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id <WORK-ID>

Required commands (run `/sdlc-spdd-*` in **AI chat** — Cursor, Copilot, or Claude Code, not a terminal — see [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands)):

| Phase | Command |
|-------|---------|
| Initialize | `/sdlc-spdd-init` |
| Analysis | `/sdlc-spdd-analysis @requirements/<file>.md` |
| Plan | `/sdlc-spdd-plan @spdd/analysis/<WORK-ID>-analysis.md` |
| Architect | `/sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md` |
| Code | `/sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01` |
| API test | `/sdlc-spdd-api-test @spdd/canvas/<WORK-ID>.md` |
| Review | `/sdlc-spdd-review @spdd/canvas/<WORK-ID>.md` |
| Prompt update | `/sdlc-spdd-prompt-update @spdd/canvas/<WORK-ID>.md` |
| Retro | `/sdlc-spdd-retro @spdd/canvas/<WORK-ID>.md` |
| Sync | `/sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md` |

This scaffold does not require the upstream `openspdd` CLI. All three assistant adapters share the same lifecycle and grounding anchors, validated by `scripts/validate-command-adapters.sh`.

For the **context and judgment** rationale (Lost in the Middle, scoped investigation, human evaluation gates), see [Chelsea Troy and the framework](chelsea-troy-and-the-framework.md).

## Three Core Skills

### Alignment

Alignment means the assistant, developer, and business source agree on what is being built.

Evidence:

- Jira or GitHub issue link in canvas Metadata
- Acceptance criteria copied into Requirements
- Work ID used consistently in canvas, progress log, review, sync, branch, commit, or PR text
- Clarifying assumptions recorded before coding

Required prompt:

    For <WORK-ID>, compare the canvas Requirements with the Jira acceptance criteria. List mismatches before coding.

### Abstraction First

Abstraction first means design intent is reviewed before implementation detail dominates.

Evidence:

- Entities, Approach, and Structure are reviewed before `/sdlc-spdd-code`
- Readiness is `Ready For Coding`
- Operations are small and testable
- Safeguards are explicit

Required prompt:

    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md

### Iterative Review

Iterative review means every implementation step is checked against intent and then synchronized.

Evidence:

- One operation per coding session
- Review report exists for the work
- Sync log records drift or confirms no drift
- Retro updates reusable memory

Required loop:

    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01
    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

## Prompt-First vs Code-First Rule

When reality diverges, choose the correct direction.

| Change type | Required SPDD action |
|-------------|----------------------|
| New business rule | Update Jira/source requirement, run `/sdlc-spdd-prompt-update`, then code |
| Changed acceptance criteria | Update Jira/source requirement, run `/sdlc-spdd-prompt-update`, then code |
| Behavior bug caused by wrong intent | Run `/sdlc-spdd-prompt-update`, then code |
| Behavior bug caused by implementation mismatch | Review against canvas, then fix code inside the approved operation |
| Refactor with no behavior change | Refactor code in a small step, review, then sync canvas |
| Implementation detail discovered during coding | Record in progress log, review, then sync canvas if accepted |

Golden rule:

    Behavior changes update the prompt first.
    Non-behavioral refactors sync the prompt after review.

## Compliance Checklist

A work item is SPDD-compliant only when:

- [ ] A Work ID exists.
- [ ] Source issue is linked, or the lack of external tracking is explicit.
- [ ] Roadmap and milestone metadata are linked when the work belongs to a milestone.
- [ ] A REASONS Canvas exists in `spdd/canvas/`.
- [ ] Canvas passes `validate-reasons-canvas.sh`.
- [ ] Requirements include acceptance criteria and definition of done.
- [ ] Entities, Approach, and Structure are reviewed before coding.
- [ ] Operations are small enough for one implementation pass.
- [ ] Norms and Safeguards are explicit.
- [ ] Coding invokes one operation at a time.
- [ ] Tests or validation are attached to each operation.
- [ ] Review compares code to the canvas.
- [ ] Behavior changes update canvas before code.
- [ ] Refactors sync canvas after review.
- [ ] Retro updates reusable memory.
- [ ] Session notes or memory capture preserve useful session context.
- [ ] Jira/GitHub issue status is synchronized from the artifact state.

## Known Boundaries

This scaffold is compliant as a repository-based SPDD workflow, but it is not a full Jira synchronization service and it is not a drop-in replacement for the `openspdd` CLI.

Current boundaries:

- Jira creation and transition require your team's Jira UI, automation, MCP server, or approved API workflow.
- GitHub Pages publishing is documented as a link and publication pattern; no Pages workflow is generated by default.
- PDF output is provided as a PDF-friendly Markdown cheat sheet unless a team-approved converter is installed.

These boundaries do not break SPDD compliance because SPDD requires governed prompt artifacts and closed-loop synchronization; it does not require a specific Jira or Pages automation mechanism.
