# SPDD Prompt Standard

This is the prompt contract for **SPDD governance** within SDLC-SPDD. Use it when you need copy-paste prompts for REASONS Canvas work: planning, alignment, architecture hardening, coding scope, review, prompt-update, and sync.

**Not the default.** For day-to-day sessions, start with [Session prompt standard](session-prompt-standard.md). Open this page when your question is specifically about the canvas contract. See [Which prompt standard?](session-prompt-standard.md#which-prompt-standard) for the full decision guide.

For roadmap and milestone prompts, see [Planning prompt standard](planning-prompt-standard.md).

## Required SPDD Prompt Fields

| Field | Required | Example |
|-------|----------|---------|
| Work ID | Yes | `FEAT-001-order-status-api` |
| Canvas reference | Yes | `@spdd/canvas/<WORK-ID>.md` |
| Operation | For code phase | `operation T01` |
| Source alignment | Before coding | Jira/GitHub issue vs canvas Requirements |
| Next SPDD command | At handoff | `/sdlc-spdd-review @spdd/canvas/<WORK-ID>.md` |

## SPDD Lifecycle Prompts

### Create canvas from requirement

    /sdlc-spdd-plan @requirements/<topic>.md

With planning context:

    /sdlc-spdd-plan @requirements/<topic>.md @ROADMAP.md @milestone-1.md

From milestone-derived requirement (canonical path):

    /sdlc-spdd-plan @requirements/milestones/<WORK-ID>.md @ROADMAP.md @milestone-1.md

After `create-work-from-milestone.sh`, the script prints suggested plan and architect prompts.

### Validate canvas structure

    ./scripts/sdlc-spdd/validate-reasons-canvas.sh spdd/canvas/<WORK-ID>.md

On success, continue with architect. On failure, fix missing REASONS sections before coding.

### Alignment — compare intent before coding

    For <WORK-ID>, compare the canvas Requirements with the Jira acceptance criteria for <JIRA-KEY>. List mismatches before coding.

With GitHub issue:

    For <WORK-ID>, compare @spdd/canvas/<WORK-ID>.md Requirements with GitHub issue <URL>. List mismatches before coding.

### Abstraction first — harden design

    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md

Readiness check prompt:

    For <WORK-ID>, read @spdd/canvas/<WORK-ID>.md. Is Entities, Approach, Structure, Norms, and Safeguards complete enough for coding? What is the readiness state?

Do not run `/sdlc-spdd-code` until readiness is `Ready For Coding`.

### Code one operation

    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01

Scope check before or after:

    For <WORK-ID> operation T01, inspect the canvas and current diff. Are any changes outside the approved operation?

### Iterative review

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md

Review-all-sections prompt:

    For <WORK-ID>, compare the implementation diff and tests against every REASONS section in @spdd/canvas/<WORK-ID>.md. List gaps by section.

### Behavior change — prompt first

    /sdlc-spdd-prompt-update @spdd/canvas/<WORK-ID>.md

With changed requirement:

    For <WORK-ID>, the acceptance criteria changed: <describe change>. Update @spdd/canvas/<WORK-ID>.md Requirements and affected Operations before any code changes.

**Do not edit application behavior until the canvas is updated.**

### Accepted drift — sync after review

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Sync-only prompt:

    For <WORK-ID>, reconcile reviewed implementation reality into @spdd/canvas/<WORK-ID>.md. Record drift in spdd/sync/.

## Prompt-First vs Code-First Decision Table

| Change type | Required SPDD action |
|-------------|---------------------|
| New business rule | Update source requirement, `/sdlc-spdd-prompt-update`, then code |
| Changed acceptance criteria | Update source, `/sdlc-spdd-prompt-update`, then code |
| Behavior bug from wrong intent | `/sdlc-spdd-prompt-update`, then code |
| Behavior bug from implementation mismatch | Review against canvas, fix within approved operation |
| Refactor with no behavior change | Code small step, review, then `/sdlc-spdd-sync` |
| Detail discovered during coding | Record in progress log, review, sync if accepted |

Golden rule:

    Behavior changes update the canvas before code.
    Non-behavioral refactors sync the canvas after review.

## One-Operation Coding Loop

    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01
    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Repeat for T02, T03, and later operations.

## Canvas Drift and Resync

Before a new session:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

If drift exists:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --from-canvas --force --phase <phase>

or:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --from-feature --force --phase <phase>

## Milestone → SPDD Bridge Prompts

Map milestone checklist to draft work:

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

Then for each created Work ID:

    /sdlc-spdd-plan @requirements/milestones/<WORK-ID>.md @ROADMAP.md @milestone-1.md
    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md

Ensure canvas Metadata includes:

    - Roadmap: ROADMAP.md
    - Milestone: milestone-1.md

## SPDD Anti-Patterns

| Bad prompt | Why it fails |
|------------|--------------|
| `Just implement the feature.` | No canvas, no operation boundary |
| Coding before `/sdlc-spdd-architect` | Skips abstraction-first |
| Multiple operations in one code pass | Violates scoped Operations |
| `/sdlc-spdd-sync` for new behavior | Wrong direction — use prompt-update |
| Editing code when Jira criteria changed | Intent drift without canvas update |
| `Continue.` without `@spdd/canvas/` | Loses SPDD contract |

## SPDD Scripts and Generated Prompts

| Script | Prompt output |
|--------|---------------|
| `validate-reasons-canvas.sh` | Suggests architect or plan command after validation |
| `create-work-from-milestone.sh` | Prints plan and architect prompts per created Work ID |
| `resync-agent-session.sh` | Creates session brief with SPDD artifact status |
| `sync-agent-context.sh` | Low-level canvas copy — run before validate when reconciling drift |

## Where SPDD Prompts Are Defined

| Source | What it standardizes |
|--------|---------------------|
| This page | Free-form SPDD governance prompts |
| `templates/cursor/sdlc-spdd-plan.md` through `sdlc-spdd-sync.md` | Cursor phase commands |
| `templates/copilot/prompts/sdlc-spdd-*.prompt.md` | Copilot phase commands |
| `templates/claude/commands/sdlc-spdd-*.md` | Claude Code phase commands |
| `docs/spdd-compliance.md` | Compliance matrix and three core skills |
| `.github/workflows/validate-canvas.yml` | CI canvas structure validation |

## Read Next

- [What SPDD brings](what-spdd-brings.md) — SPDD value proposition
- [SPDD compliance](spdd-compliance.md) — full compliance checklist
- [Session prompt standard](session-prompt-standard.md) — unified session prompts
- [Planning prompt standard](planning-prompt-standard.md) — roadmap and milestone prompts
