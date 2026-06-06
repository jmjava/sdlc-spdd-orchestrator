# First Day with SDLC-SPDD

Use this guide when you are trying SDLC-SPDD for the first time in an application repository.

The goal for day one is not to automate everything. The goal is to create a small, reviewable loop:

    Install -> Initialize -> Plan -> Architect -> Code one operation -> Review -> Capture memory

## Before You Start

You need:

- A target application repository.
- Cursor or GitHub Copilot Chat.
- A small requirement, bug, refactor, or spike to practice with.
- This orchestrator repository cloned locally.

Good first examples:

- Add a small endpoint.
- Fix one reproducible bug.
- Refactor one class without changing behavior.
- Document one operational runbook.

Avoid starting with a large migration or broad rewrite.

## 1. Install the Framework into Your Project

From the orchestrator repository:

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all

If the project was initialized by an older version:

    ./scripts/upgrade-project.sh --target /path/to/app --all --dry-run
    ./scripts/upgrade-project.sh --target /path/to/app --all

Then open the target application in Cursor or a Copilot-enabled editor.

## 2. Initialize Project Context

In Cursor or GitHub Copilot Chat:

    /sdlc-spdd-init

Expected result:

- `requirements/` exists.
- `spdd/` exists.
- `agent-context/` exists.
- `ROADMAP.md`, `milestone-1.md`, and `session-notes/` exist when they were missing.
- stack information is captured in project memory.
- no application source code is changed.

## 3. Create or Choose a Work ID

Use one Work ID for each unit of work.

Examples:

- `FEAT-001-order-status-api`
- `BUG-003-null-discount-checkout`
- `REF-002-split-billing-service`
- `DOC-004-deployment-runbook`

If you are not sure which ID to use, ask:

    Triage this request. Propose a Work ID, work type, missing information, and whether it is ready for /sdlc-spdd-plan.

## 4. Start a Session Brief

In the target application:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase plan

Then ask the assistant:

    For FEAT-001-order-status-api, read @agent-context/sessions/current-session.md and continue with the recommended SDLC-SPDD command.

The session brief gives a new agent enough context to resume without relying on chat history.

## 5. Plan the Work

From a requirement file:

    /sdlc-spdd-plan @requirements/order-status-api.md

From plain language:

    /sdlc-spdd-plan Create an endpoint that returns current order status by ID. Use FEAT-001-order-status-api.

From Jira:

    /sdlc-spdd-plan Jira ABC-123: add order status lookup. Link https://jira.example.com/browse/ABC-123 and use the acceptance criteria below.

Planning should create a REASONS Canvas under:

    spdd/canvas/<WORK-ID>.md

If this work belongs to a milestone, include that in the canvas Metadata:

    - Roadmap: ROADMAP.md
    - Milestone: milestone-1.md

## 6. Harden Architecture Before Coding

Run:

    /sdlc-spdd-architect @spdd/canvas/FEAT-001-order-status-api.md

Do not code until readiness is:

    Ready For Coding

If readiness is blocked or unclear, update the canvas first.

## 7. Code One Operation

Run one operation, not the entire feature:

    /sdlc-spdd-code @spdd/canvas/FEAT-001-order-status-api.md operation T01

The coding agent should:

- read the canvas.
- implement only T01.
- add or update tests.
- update the progress log.
- stop before starting T02.

## 8. Review Against the Canvas

Run:

    /sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md

Review checks whether the implementation matches:

- Requirements
- Entities
- Approach
- Structure
- Operations
- Norms
- Safeguards
- tests

## 9. Persist Memory Before You Stop

At the end of the session:

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id FEAT-001-order-status-api \
      --phase code \
      --summary "Implemented T01 for order status lookup." \
      --validation "Tests run: <command/result>" \
      --milestone milestone-1.md \
      --next "/sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md"

This stores context in files that future sessions can read.

## First-Day Checklist

- [ ] Framework installed or upgraded.
- [ ] `/sdlc-spdd-init` completed.
- [ ] Work ID chosen.
- [ ] Session brief created.
- [ ] Requirement planned into a REASONS Canvas.
- [ ] Architecture reviewed.
- [ ] One operation implemented.
- [ ] Review run.
- [ ] Memory captured.

## Where to Go Next

- [10,000-foot view](ten-thousand-foot-view.md)
- [Installing into your project](installing-into-your-project.md)
- [Maintaining your project](maintaining-your-project.md)
- [Top useful concepts and commands](useful-concepts-and-commands.md)
