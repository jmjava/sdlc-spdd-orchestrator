# Daily SDLC-SPDD Runbook

Use this runbook when operating an initialized application day to day.

## Daily Operating Rules

1. Keep one active Work ID per unit of work.
2. Keep the REASONS Canvas as the design contract.
3. Ask questions with explicit artifact references.
4. Code one approved operation at a time.
5. Review against the canvas before starting the next operation.
6. Record learnings and drift before the work disappears from memory.

## Morning or Start-of-Session Check

Goal: recover context before asking the assistant to act.

Prompt:

    For <WORK-ID>, read @spdd/canvas/<WORK-ID>.md, @agent-context/features/<WORK-ID>/progress-log.md, and @agent-context/memory/known-pitfalls.md. Summarize:
    - current status
    - next approved operation
    - open risks
    - recommended SDLC-SPDD command

If no Work ID exists yet:

    We are starting new work for <short requirement>. Create a Work ID, plan the work, and link any external issue I provide.

Then invoke:

    /sdlc-spdd-plan <requirement, Jira issue, GitHub issue, or @requirements/file.md>

## Triage New Work

Use triage when a request arrives from chat, Jira, GitHub Issues, or a stakeholder.

Prompt:

    Triage this request before planning. Identify whether it is FEAT, BUG, REF, SPIKE, DOC, TEST, or CHORE; propose a Work ID; list missing information; and tell me whether we can safely run /sdlc-spdd-plan.

If the request is ready:

    /sdlc-spdd-plan <request details>

If the request is not ready, ask a bounded question:

    For <proposed WORK-ID>, what single clarification is required before planning?

## Plan Work

Goal: create the design contract without changing source code.

Prompt examples:

    /sdlc-spdd-plan @requirements/order-status-api.md

    /sdlc-spdd-plan Jira ABC-123: create order status lookup. Link to https://jira.example.com/browse/ABC-123.

    /sdlc-spdd-plan GitHub issue https://github.com/example/orders-api/issues/42. Use the issue as the external reference.

Before leaving planning, check:

- The canvas has a Work ID.
- Requirements are explicit.
- Operations are small enough for one coding session.
- External links are in Metadata.
- Risks and safeguards are recorded.

## Harden Architecture

Goal: make the canvas safe to code.

Prompt:

    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md

Follow-up question:

    For <WORK-ID>, what must change before this canvas is Ready For Coding?

Only move to coding when readiness is `Ready For Coding`.

## Code One Operation

Goal: implement one approved operation.

Prompt:

    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01

Context-safe variants:

    For <WORK-ID>, implement only operation T01. Do not start T02. Update the progress log and tests.

    For <WORK-ID>, read the canvas and current diff first. If T01 is already complete, stop and recommend the next operation.

Before coding starts, verify:

- The selected operation is named.
- The operation is approved by the canvas.
- Safeguards allow the change.
- Test expectations are clear.

## Ask Questions During Coding

Use questions to preserve context and prevent drift.

Good prompts:

    For <WORK-ID> T01, does this implementation still match the Approach section in @spdd/canvas/<WORK-ID>.md?

    For <WORK-ID>, inspect the current diff and tell me whether any file changes are unrelated to T01.

    For <WORK-ID>, what test should be added before this operation can be reviewed?

    For <WORK-ID>, update no files. Explain the next smallest safe step for T01.

Bad prompts:

    Keep going.
    Fix the tests.
    What should I change?

## Review the Operation

Goal: compare implementation to the design contract.

Prompt:

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md

Review must check:

- Requirements
- Entities
- Approach
- Structure
- Operations
- Norms
- Safeguards
- Tests
- Unrelated changes
- Architecture drift

If review requests changes:

    For <WORK-ID>, implement only the required review fixes for operation T01.

Then review again.

## Sync Drift

Use sync when implementation reality differs from the canvas, or after several reviewed operations.

Prompt:

    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Use sync to record:

- Completed operations
- Changed assumptions
- Stale tasks
- Follow-up tasks
- Accepted drift

Do not use sync to hide unreviewed changes.

## Capture Retro

Run retro when the feature, bugfix, refactor, or spike is complete.

Prompt:

    /sdlc-spdd-retro @spdd/canvas/<WORK-ID>.md

Retro updates:

- `agent-context/features/<WORK-ID>/retro.md`
- `agent-context/memory/project-memory.md`
- `agent-context/memory/known-pitfalls.md`
- `agent-context/memory/reusable-patterns.md`

## End-of-Session Handoff

Prompt:

    For <WORK-ID>, create a handoff summary from @spdd/canvas/<WORK-ID>.md, @agent-context/features/<WORK-ID>/progress-log.md, and current git status. Include completed work, validation, open risks, and next command.

The handoff should include:

- Work ID
- External issue link
- Canvas path
- Last completed operation
- Current review result
- Tests run
- Next recommended command

## Common Daily Loops

### New feature

    /sdlc-spdd-plan @requirements/<feature>.md
    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01
    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

### Bugfix

    /sdlc-spdd-plan BUG: <bug summary and reproduction>
    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01
    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-retro @spdd/canvas/<WORK-ID>.md

### Follow-up question

    For <WORK-ID>, read @spdd/canvas/<WORK-ID>.md before answering. <question>

### Continue interrupted work

    For <WORK-ID>, read the canvas, progress log, review report, and current diff. Tell me whether to code, review, sync, or retro next.

