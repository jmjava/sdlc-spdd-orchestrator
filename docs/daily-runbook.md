# Daily SDLC-SPDD Runbook

Use this runbook for **operational rhythm**: rules, script sequences, phase checklists, and when to move between steps. It does not duplicate copy-paste prompts — those live in one place.

| Need | Open |
|------|------|
| Copy-paste prompts (default) | [Session prompt standard](session-prompt-standard.md) |
| Which of the three prompt standards? | [Which prompt standard?](session-prompt-standard.md#which-prompt-standard) |
| Step order (1–13) | [Workflow](workflow.md) |
| Planning → SPDD → SDLC loop | [Three-part operating path](three-part-operating-path.md) |
| **Rules, scripts, checklists** | **This page** |
| Workflow CLI + team registry (reference) | [agent-context/README.md](../agent-context/README.md#sdlc-pointer-current-choretask) |

## Daily Operating Rules

1. Keep one active Work ID per unit of work (local pointer + optional team claim).
2. Keep the REASONS Canvas as the design contract.
3. Ask questions with explicit artifact references.
4. Code one approved operation at a time.
5. Review against the canvas before starting the next operation.
6. For behavior changes, update the canvas before coding.
7. For refactors, review the code and then sync the canvas.
8. Record learnings and drift before the work disappears from memory.

## Morning or Start-of-Session Check

Goal: recover context before asking the assistant to act.

**Fast path** — orientation without opening files:

    ./scripts/sdlc-spdd/sdlc.sh next

In chat: `/sdlc-spdd-whereami` (same answer as `next`, plus team registry context).

**Team coordination** — before claiming work on a shared repo:

    ./scripts/sdlc-spdd/sdlc.sh team
    ./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>    # commit agent-context/work-registry.tsv after

If you already have an active pointer, resume or switch:

    ./scripts/sdlc-spdd/sdlc.sh resume <WORK-ID> [--phase <phase>]

**Full session loop** (recommended daily rhythm):

1. Orient: `./scripts/sdlc-spdd/sdlc.sh next` (or `/sdlc-spdd-whereami` in chat).
2. Check canvas sync when resuming stale work:

       ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

3. Open the session brief (sets pointer + workflow phase):

       ./scripts/sdlc-spdd/sdlc.sh start
       # or: ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>

4. **Paste the Resume Prompt** from `agent-context/sessions/current-session.md`. That generated prompt is the source of truth — it directs the agent to load only the files listed under **Resolved Context** in the same brief (phase extensions, Work ID artifacts, and area-filtered index rows).

5. After completing a phase step: `./scripts/sdlc-spdd/sdlc.sh advance`

Optional — ask for a status summary after pasting the resume prompt:

    Summarize current status, next approved operation, open risks, and recommended SDLC-SPDD command.

If no Work ID exists yet:

    We are starting new work for <short requirement>. Create a Work ID, plan the work, and link any external issue I provide.

Then invoke analysis first (Fowler Step 3), index it, and plan from the artifact:

    /sdlc-spdd-analysis <requirement, Jira issue, GitHub issue, or @requirements/file.md>
    ./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id <WORK-ID>
    /sdlc-spdd-plan @spdd/analysis/<WORK-ID>-analysis.md

## Triage New Work

Use triage when a request arrives from chat, Jira, GitHub Issues, or a stakeholder.

Prompts: [Triage (no Work ID yet)](session-prompt-standard.md#triage-no-work-id-yet) in Session prompt standard.

## Plan Work

Goal: create the design contract without changing source code.

Prompts: [Phase-specific prompts — Plan](session-prompt-standard.md#phase-specific-standard-prompts) and [During session — milestone-aware planning](session-prompt-standard.md#milestone-aware-planning) in Session prompt standard.

Before leaving planning, check:

- The canvas has a Work ID.
- Requirements are explicit.
- Operations are small enough for one coding session.
- External links are in Metadata.
- Risks and safeguards are recorded.

## Harden Architecture

Goal: make the canvas safe to code.

Prompts: [Phase-specific prompts — Architect](session-prompt-standard.md#phase-specific-standard-prompts) in Session prompt standard. Follow-up: ask what must change before the canvas is `Ready For Coding`.

Only move to coding when readiness is `Ready For Coding`.

## Code One Operation

Goal: implement one approved operation.

Prompts: [Phase-specific prompts — Code](session-prompt-standard.md#phase-specific-standard-prompts) and [Check scope before coding](session-prompt-standard.md#check-scope-before-coding) in Session prompt standard.

Before coding starts, verify:

- The selected operation is named.
- The operation is approved by the canvas.
- Safeguards allow the change.
- Test expectations are clear.

## Ask Questions During Coding

Use [Context-preserving question](session-prompt-standard.md#context-preserving-question) prompts from Session prompt standard. Avoid vague prompts (`Keep going.`, `Fix the tests.`) — see [Anti-patterns](session-prompt-standard.md#anti-patterns).

## Review the Operation

Goal: compare implementation to the design contract.

Prompts: [Phase-specific prompts — Review](session-prompt-standard.md#phase-specific-standard-prompts) and [Behavior change / drift](session-prompt-standard.md#behavior-change-spdd-rule) in Session prompt standard.

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

If review requests changes, implement only the required fixes for the operation, then review again. If acceptance criteria changed, run prompt-update before more code — see Session prompt standard.

## Sync Drift

Use sync when implementation reality differs from the canvas, or after several reviewed operations.

Prompts: [Phase-specific prompts — Sync](session-prompt-standard.md#phase-specific-standard-prompts) and [Accepted implementation drift](session-prompt-standard.md#accepted-implementation-drift) in Session prompt standard.

Use sync to record:

- Completed operations
- Changed assumptions
- Stale tasks
- Follow-up tasks
- Accepted drift

Do not use sync to hide unreviewed changes.

Do not use sync for a new behavior requirement. Update the source issue and canvas first via prompt-update.

## Keep Jira Synchronized

Use [jira-runbook.md](jira-runbook.md) when work is tracked in Jira.

Create new Jira issue draft in the milestone requirement file first:

    requirements/milestones/<WORK-ID>.md   →   ## Jira section (Key, Summary, Type, …)

See [requirements/milestones/README.md](../requirements/milestones/README.md) and [jira-runbook.md](jira-runbook.md). On claim, `./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>` auto-links the Key into `agent-context/work-registry.tsv`.

Then draft for Jira UI or automation:

    Draft a Jira issue from requirements/milestones/<WORK-ID>.md ## Jira. Include issue type, summary, business value, scope in, scope out, Given/When/Then acceptance criteria, labels, components, and links.

Daily Jira comment:

    For <WORK-ID>, read the canvas, progress log, review report, and sync log. Draft a Jira update for <JIRA-KEY> with state, completed operations, validation, risks, and next command.

Behavior change from Jira:

    Jira <JIRA-KEY> changed acceptance criteria: <new rule>. For <WORK-ID>, update the canvas first with /sdlc-spdd-prompt-update. Do not change source code.

## Capture Retro

Run retro when the feature, bugfix, refactor, or spike is complete.

Prompt: [Phase-specific prompts — Retro](session-prompt-standard.md#phase-specific-standard-prompts) in Session prompt standard.

Retro updates:

- `agent-context/features/<WORK-ID>/retro.md`
- `agent-context/memory/project-memory.md`
- `agent-context/memory/known-pitfalls.md`
- `agent-context/memory/reusable-patterns.md`

## End-of-Session Handoff

Prompts and script: [End of session](session-prompt-standard.md#end-of-session) in Session prompt standard.

**Preferred capture** — guarded against pointer mismatch (refuses wrong Work ID):

    ./scripts/sdlc-spdd/sdlc.sh capture --summary "<what changed>" --validation "<tests>" --next "<next command>"

With milestone progress:

    ./scripts/sdlc-spdd/sdlc.sh capture --summary "..." --validation "..." \
      --milestone milestone-1.md --roadmap-note "..." --next "/sdlc-spdd-review @spdd/canvas/<WORK-ID>.md"

Park work for later:

    ./scripts/sdlc-spdd/sdlc.sh shelf --reason "blocked on review"
    ./scripts/sdlc-spdd/sdlc.sh list-shelved

The handoff should include:

- Work ID
- External issue link
- Canvas path
- Last completed operation
- Current review result
- Tests run
- Next recommended command

If you used `claim`, commit `agent-context/work-registry.tsv` so teammates see your status.

## Common Daily Loops

Quick command sequences. Full prompt wording: [Session prompt standard](session-prompt-standard.md).

### New feature

    /sdlc-spdd-analysis @requirements/<feature>.md
    ./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id <WORK-ID>
    /sdlc-spdd-plan @spdd/analysis/<WORK-ID>-analysis.md
    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01
    /sdlc-spdd-api-test @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

### Bugfix

    /sdlc-spdd-analysis BUG: <bug summary and reproduction>
    ./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id <WORK-ID>
    /sdlc-spdd-plan @spdd/analysis/<WORK-ID>-analysis.md
    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01
    /sdlc-spdd-api-test @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-retro @spdd/canvas/<WORK-ID>.md

### Follow-up question

    For <WORK-ID>, read @spdd/canvas/<WORK-ID>.md before answering. <question>

### Continue interrupted work

    ./scripts/sdlc-spdd/sdlc.sh resume <WORK-ID>
    ./scripts/sdlc-spdd/sdlc.sh next

Script sequence: [Morning or Start-of-Session Check](#morning-or-start-of-session-check) above. Resume prompt and follow-up: [Continue interrupted work](session-prompt-standard.md#continue-interrupted-work) in Session prompt standard.

### Daily workflow CLI reference

| Goal | Command |
|------|---------|
| What now? | `./scripts/sdlc-spdd/sdlc.sh next` or `/sdlc-spdd-whereami` |
| Open session brief | `./scripts/sdlc-spdd/sdlc.sh start` |
| Move to next phase | `./scripts/sdlc-spdd/sdlc.sh advance` |
| Skip a phase | `./scripts/sdlc-spdd/sdlc.sh skip <phase> --reason "..."` |
| Re-read artifacts | `./scripts/sdlc-spdd/sdlc.sh sync` |
| See all Work IDs | `./scripts/sdlc-spdd/sdlc.sh list-work` |
| Team who-is-on-what | `./scripts/sdlc-spdd/sdlc.sh team` |
| Claim for team | `./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>` → commit `work-registry.tsv` |

Local state (gitignored): `.sdlc/pointer`, `.sdlc/workflows/`. Shared via git: `agent-context/work-registry.tsv`.
