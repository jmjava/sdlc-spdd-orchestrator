# Jira Runbook

Use this runbook to create Jira issues from SDLC-SPDD work and keep Jira synchronized with the REASONS Canvas, implementation progress, reviews, and sync logs.

## Source of Truth

| Artifact | Source of truth for |
|----------|---------------------|
| Jira issue | Delivery status, ownership, sprint/board workflow, business acceptance criteria |
| REASONS Canvas | Design contract, scope boundaries, operations, norms, safeguards |
| Progress log | Implementation history by operation |
| Review report | Fit between implementation and canvas |
| Sync log | Drift, reconciled assumptions, and follow-up tasks |

Jira should not replace the canvas. The canvas should not replace Jira workflow state.

## Create a New Jira Issue

Use this flow when a request starts outside Jira.

### 0. Draft in the milestone requirement (recommended)

For Work IDs created from milestones, store Jira field syntax in:

    requirements/milestones/<WORK-ID>.md

under `## Jira` (scaffolded by `create-work-from-milestone.sh`). Fill Summary, Description,
and Given/When/Then acceptance criteria there first — it is the copy-paste source for Jira UI,
MCP, or API creation. After Jira returns a key, set `- Key: ABC-123` in that section and commit.
`./scripts/sdlc.sh claim <WORK-ID>` then auto-links `jira:ABC-123` in `work-registry.tsv`.

### 1. Triage the request

Prompt:

    Triage this request before creating Jira. Identify type, proposed Jira summary, business value, acceptance criteria, risks, and whether it should be FEAT, BUG, REF, SPIKE, DOC, TEST, or CHORE:

    <paste request>

### 2. Draft the Jira issue

Prompt:

    Draft a Jira issue for this SDLC-SPDD work. Include:
    - Issue type
    - Summary
    - Description
    - Business value
    - Scope in
    - Scope out
    - Acceptance criteria in Given/When/Then form
    - Suggested labels
    - Suggested components
    - Links to any existing GitHub issue, PR, or docs page

    Request:
    <paste request>

### 3. Create the issue in Jira

Create the issue using your team's Jira UI, Jira automation, MCP tool, or approved API workflow.

Minimum required fields:

    Project: <PROJECT>
    Issue type: Story, Bug, Task, Spike, or Chore
    Summary: <short user/business outcome>
    Description: <drafted description>
    Acceptance criteria: <Given/When/Then criteria>
    Labels: sdlc-spdd, <work type>, <system/component>
    Components: <component>
    Links: <GitHub issue, PR, or GitHub Pages URL if known>

Do not ask the coding assistant to create Jira directly unless the environment has an approved Jira integration and credentials. If direct Jira tools are available, pass the same field set explicitly and ask the assistant to report the created key.

### 4. Create the SDLC-SPDD Work ID

After Jira returns a key, create a Work ID that keeps the local lifecycle stable.

Examples:

    Jira: ABC-123
    Work ID: FEAT-123-order-status-api

    Jira: PAY-456
    Work ID: BUG-456-null-discount-checkout

The Work ID does not have to equal the Jira key, but the canvas Metadata must link them.

### 5. Plan from the new Jira issue

Prompt:

    /sdlc-spdd-plan Jira ABC-123: <summary>. Link the canvas to https://jira.example.com/browse/ABC-123 and use this Jira description and acceptance criteria as the requirement:

    <paste Jira description and acceptance criteria>

Expected result:

- Jira key is captured in canvas Metadata.
- Acceptance criteria are captured in Requirements.
- Operations are decomposed into small implementation tasks.
- Risks, norms, and safeguards are recorded before code changes.

## Create Jira Children from a Canvas

Use this when one Jira issue is too large for the board.

Prompt:

    For FEAT-123, read @spdd/canvas/FEAT-123-order-status-api.md. Draft Jira child issues from the Operations section. Each child should include summary, description, acceptance criteria, parent key ABC-123, and the operation ID it implements.

Recommended mapping:

| Canvas operation | Jira issue type |
|------------------|-----------------|
| User-visible feature slice | Story or Task |
| Defect correction | Bug |
| Investigation | Spike |
| Test-only work | Test or Task |
| Documentation | Task |

Keep child issues small enough that each maps to one canvas operation or one cohesive operation group.

## Keep Jira in Sync

Synchronize Jira at lifecycle checkpoints. Use comments or fields according to your team's Jira workflow.

| SDLC-SPDD checkpoint | Jira update |
|----------------------|-------------|
| Canvas created | Add canvas path and design summary |
| Architect ready | Move to In Progress or Ready for Dev; add readiness decision |
| Operation started | Comment with operation ID and intent |
| Operation reviewed | Comment with review result and test evidence |
| Behavior requirement changed | Update Jira acceptance criteria, then update canvas before coding |
| Refactor changed structure only | Comment with refactor summary, then sync canvas from code |
| Blocked | Move to Blocked and add the missing decision/dependency |
| Retro and sync complete | Add final validation and move toward Done |

### Daily Jira sync prompt

Use this to generate a Jira comment:

    For <WORK-ID>, read @spdd/canvas/<WORK-ID>.md, @agent-context/features/<WORK-ID>/progress-log.md, @spdd/reviews/<WORK-ID>-review.md if it exists, and @spdd/sync/<WORK-ID>-sync.md if it exists. Draft a Jira update for <JIRA-KEY> with:
    - current SDLC-SPDD state
    - completed operations
    - validation performed
    - review result
    - risks or blockers
    - next operation or command

### Status mapping

| SDLC-SPDD state | Typical Jira status |
|-----------------|---------------------|
| Request triaged | Backlog |
| Canvas created | To Do or Selected for Development |
| Ready For Coding | In Progress |
| Operation implemented | In Progress |
| Review Approved | In Review or Ready for QA |
| Review Changes Requested | In Progress |
| Blocked readiness or review | Blocked |
| Retro and sync complete | Done |

Adapt these names to your team's workflow.

## Requirement Changes vs Refactoring

SPDD requires different sync directions depending on the type of change.

### Behavior or requirement change

Update Jira first, then update the canvas, then update code.

Prompt:

    Jira ABC-123 changed acceptance criteria: <new rule>. For FEAT-123, update @spdd/canvas/FEAT-123-order-status-api.md first. Do not change source code. Identify which Requirements, Approach, Operations, Norms, and Safeguards changed.

After the canvas is reviewed:

    /sdlc-spdd-code @spdd/canvas/FEAT-123-order-status-api.md operation <operation>

### Refactoring or non-behavioral cleanup

Refactor in a small step, review, then sync the prompt artifacts back to reality.

Prompt:

    For FEAT-123, refactor only <specific target> without changing observable behavior. Stay inside the current canvas safeguards.

Then:

    /sdlc-spdd-review @spdd/canvas/FEAT-123-order-status-api.md
    /sdlc-spdd-sync @spdd/canvas/FEAT-123-order-status-api.md

Jira comment:

    Refactor completed with no intended behavior change. Canvas synchronized after review. Validation: <tests>.

## Jira Sync Checklist

Before coding:

- Jira key exists or the decision not to use Jira is recorded.
- Canvas Metadata includes Jira key and URL.
- Jira acceptance criteria and canvas Requirements match.
- Operations are small and traceable.

During coding:

- Each update references the Work ID and operation ID.
- Jira comments are generated from canvas/progress/review artifacts, not from memory alone.
- Requirement changes update Jira and canvas before code.

Before done:

- Jira status matches review outcome.
- Final comment includes validation, review result, and remaining follow-ups.
- Canvas sync log records implementation drift.
- Retro updates reusable memory.
