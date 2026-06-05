# Integration Linking

This guide explains how to link SDLC-SPDD work to Jira-based systems and GitHub Pages.

## Link Types

Use different links for different jobs:

| Link type | Purpose | Example |
|-----------|---------|---------|
| Jira issue link | Tracks delivery status, ownership, and acceptance criteria | `https://jira.example.com/browse/ABC-123` |
| GitHub issue link | Tracks repo-native work and discussion | `https://github.com/org/repo/issues/42` |
| GitHub pull request link | Tracks implementation review | `https://github.com/org/repo/pull/43` |
| GitHub Pages link | Publishes human-readable docs, runbooks, or canvas summaries | `https://org.github.io/repo/spdd/FEAT-001.html` |

Jira and GitHub Issues are work tracking systems. GitHub Pages is a documentation publishing surface. Do not use Pages as the source of truth for delivery state.

## Canvas Metadata

Every externally tracked Work ID should include links in the canvas Metadata section.

Example:

    ## Metadata

    - Work ID: FEAT-001-order-status-api
    - Source system: Jira
    - Source issue: ABC-123
    - Source URL: https://jira.example.com/browse/ABC-123
    - Docs URL: https://org.github.io/orders-api/spdd/FEAT-001-order-status-api.html
    - Pull request: TBD
    - Status: Planned

If the work starts from GitHub Issues:

    ## Metadata

    - Work ID: BUG-003-null-discount-checkout
    - Source system: GitHub Issues
    - Source issue: #42
    - Source URL: https://github.com/org/repo/issues/42
    - Docs URL: https://org.github.io/orders-api/spdd/BUG-003-null-discount-checkout.html
    - Pull request: TBD
    - Status: Planned

## Linking to Jira-Based Systems

Use Jira links when work is governed by Jira status, sprint planning, assignment, or acceptance criteria.

For detailed issue creation and synchronization steps, see [jira-runbook.md](jira-runbook.md).

### Create a new Jira issue

When the request starts outside Jira, first draft the issue from the requirement:

    Draft a Jira issue for this request. Include issue type, summary, business value, scope in, scope out, Given/When/Then acceptance criteria, labels, components, and links.

Create the issue in Jira using your team's approved UI, automation, MCP tool, or API workflow. After Jira returns a key, plan from that key:

    /sdlc-spdd-plan Jira ABC-123: <summary>. Link the canvas to https://jira.example.com/browse/ABC-123 and use the Jira acceptance criteria as the Requirements source.

### Start from Jira

Prompt:

    /sdlc-spdd-plan Jira ABC-123: <summary>. Link the canvas to https://jira.example.com/browse/ABC-123 and preserve the acceptance criteria below.

Include acceptance criteria if the assistant cannot read Jira:

    Acceptance criteria:
    - <criterion 1>
    - <criterion 2>
    - <criterion 3>

Expected canvas updates:

- `Source system: Jira`
- `Source issue: ABC-123`
- `Source URL: https://jira.example.com/browse/ABC-123`
- Jira acceptance criteria copied into Requirements
- Operations broken into small implementation tasks

### Link Jira from branch, commit, and PR text

Use the Jira key in human-readable places:

    branch: feature/ABC-123-order-status-api
    commit: ABC-123 implement order status lookup
    PR title: ABC-123 Order status lookup

If your repository uses a stricter branch naming policy, keep the Jira key in the canvas, commits, and PR body even if it is not in the branch name.

### Daily Jira update prompt

Use this when posting status back to Jira manually:

    For FEAT-001, read @spdd/canvas/FEAT-001-order-status-api.md and @agent-context/features/FEAT-001-order-status-api/progress-log.md. Draft a Jira update for ABC-123 with status, completed work, validation, risks, and next step.

### Keep Jira and canvas in sync

Use this rule:

- If Jira acceptance criteria or intended behavior change, update Jira and then run `/sdlc-spdd-prompt-update` before coding.
- If code was refactored without behavior change, review and then run `/sdlc-spdd-sync`.

Prompt:

    Jira ABC-123 changed acceptance criteria: <new rule>. For FEAT-001, update @spdd/canvas/FEAT-001-order-status-api.md first with /sdlc-spdd-prompt-update. Do not change source code.

### Jira status mapping

| SDLC-SPDD state | Typical Jira status |
|-----------------|---------------------|
| Planned canvas exists | To Do or Selected for Development |
| Ready For Coding | In Progress |
| Operation implemented | In Progress |
| Review Approved | In Review or Ready for QA |
| Retro and sync complete | Done |
| Blocked readiness or review | Blocked |

Adapt these names to your Jira workflow.

## Linking to GitHub Pages

Use GitHub Pages to publish documentation for humans: runbooks, architecture notes, canvas summaries, and cheat sheets.

Recommended published content:

- `docs/`
- selected `spdd/canvas/` summaries
- selected `spdd/reviews/` summaries
- daily runbooks and onboarding guides

Avoid publishing secrets, private issue details, customer data, credentials, or internal-only incident context.

### Pages link pattern

Choose one stable link pattern and record it in Metadata:

    https://<org>.github.io/<repo>/docs/daily-runbook.html
    https://<org>.github.io/<repo>/spdd/<WORK-ID>.html

Example:

    - Docs URL: https://acme.github.io/orders-api/spdd/FEAT-001-order-status-api.html

### Prompt to prepare Pages-ready docs

    For FEAT-001, read @spdd/canvas/FEAT-001-order-status-api.md. Create a public-safe summary suitable for GitHub Pages. Exclude secrets, customer data, internal Jira comments, and implementation details that should remain private.

### Prompt to link Pages from a canvas

    For FEAT-001, update only the canvas Metadata. Add Docs URL https://acme.github.io/orders-api/spdd/FEAT-001-order-status-api.html.

### Pages vs Jira decision

| Need | Use Jira | Use GitHub Pages |
|------|----------|------------------|
| Sprint status | Yes | No |
| Assignment | Yes | No |
| Acceptance criteria | Yes | Optional summary |
| Public or team docs | No | Yes |
| Runbook publishing | No | Yes |
| Audit trail for delivery | Yes | No |
| Stable link to design summary | Optional | Yes |

## Cross-Link Checklist

Before coding:

- Canvas Metadata includes source system and source URL.
- Requirements include issue acceptance criteria.
- Operations are small and traceable.
- Jira or GitHub issue link is included in the progress log.

Before review:

- Progress log references completed operation IDs.
- PR body links the canvas and external issue.
- Public docs link is added only if content is safe to publish.

Before done:

- Review report is linked from the canvas or feature folder.
- Retro captures reusable learning.
- Sync log records drift and remaining work.
- Jira or GitHub issue update can be generated from the canvas and progress log.
