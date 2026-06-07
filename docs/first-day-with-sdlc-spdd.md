# First Day with SDLC-SPDD

Use this guide when you are trying SDLC-SPDD for the first time in an application repository.

For the full Planning → SPDD → SDLC path beyond day one, see [Three-part operating path](three-part-operating-path.md).

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
- Run a short spike to explore an approach.

Avoid starting with a large migration or broad rewrite.

## 1. Install the Framework into Your Project

| Part | Action |
|------|--------|
| SDLC | From the orchestrator repository: |

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all

If the project was initialized by an older version:

    ./scripts/upgrade-project.sh --target /path/to/app --all --dry-run
    ./scripts/upgrade-project.sh --target /path/to/app --all

Confirm the three-part scaffold is complete (install and upgrade also run this automatically). Still from the **orchestrator repo**:

    ./scripts/verify-project-install.sh --target /path/to/app

Then open the target application in Cursor or a Copilot-enabled editor.

## 2. Initialize Project Context

| Part | Action |
|------|--------|
| SDLC | In **AI chat** (not the terminal) — see [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands): |

**Cursor:** Chat or Agent → type `/sdlc-spdd-init` (or pick `sdlc-spdd-init` from the `/` menu).

**Copilot:** Chat → `/sdlc-spdd-init`, or `#prompt:sdlc-spdd-init` if slash commands are missing.

    /sdlc-spdd-init

Expected result:

- `requirements/` exists.
- `spdd/` exists.
- `agent-context/` exists.
- `ROADMAP.md`, `milestone-1.md`, `requirements/milestones/`, and `session-notes/` exist when they were missing.
- stack information is captured in project memory.
- no application source code is changed.

## 3. Create or Choose a Work ID

| Part | Action |
|------|--------|
| SDLC | Use one Work ID for each unit of work. |

Examples:

- `FEAT-001-order-status-api`
- `BUG-003-null-discount-checkout`
- `REF-002-split-billing-service`
- `SPIKE-004-cache-options`

If you are not sure which ID to use, ask:

    Triage this request. Propose a Work ID, work type, missing information, and whether it is ready for /sdlc-spdd-plan.

## 4. Map Milestone Work (optional)

| Part | Action |
|------|--------|
| Planning → SPDD | If work already exists as milestone checklist items, map it **before** the session brief: |

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

This creates draft Work IDs, canvases, and **Linked Work** rows in the milestone file. Follow the **Next SPDD prompts** the script prints.

Skip this step for ad-hoc requirements — go to step 5.

## 5. Start a Session Brief

| Part | Action |
|------|--------|
| SDLC | In the target application, set `--phase` to the phase you are about to run. On day one that is usually `plan`: |

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase plan

Then **paste the Resume Prompt** from `agent-context/sessions/current-session.md` — do not paraphrase it. The script generates the authoritative prompt with canvas, memory, and planning references.

This first-day walkthrough uses the **ad-hoc entry** (you have a requirement but no prior canvas). If you mapped milestone work in step 4 and the canvas is already planned and architected, start the brief at `--phase code` instead. See [Session brief timing](three-part-operating-path.md#session-brief-timing) for the milestone-driven vs ad-hoc rule.

See [Session prompt standard](session-prompt-standard.md). Source of truth: the generated **Resume Prompt** section in `current-session.md`.

## 6. Plan the Work

| Part | Action |
|------|--------|
| SPDD (+ Planning) | From a requirement file: |

    /sdlc-spdd-plan @requirements/order-status-api.md @ROADMAP.md @milestone-1.md

From plain language:

    /sdlc-spdd-plan Create an endpoint that returns current order status by ID. Use FEAT-001-order-status-api.

From Jira:

    /sdlc-spdd-plan Jira ABC-123: add order status lookup. Link https://jira.example.com/browse/ABC-123 and use the acceptance criteria below.

Planning should create a REASONS Canvas under:

    spdd/canvas/<WORK-ID>.md

If this work belongs to a milestone, include that in the canvas Metadata:

    - Roadmap: ROADMAP.md
    - Milestone: milestone-1.md

## 7. Harden Architecture Before Coding

| Part | Action |
|------|--------|
| SPDD | Run: |

    /sdlc-spdd-architect @spdd/canvas/FEAT-001-order-status-api.md

Do not code until readiness is:

    Ready For Coding

If readiness is blocked or unclear, update the canvas first.

## 8. Code One Operation

| Part | Action |
|------|--------|
| SDLC + SPDD | Refresh the session brief for the code phase, then run one operation: |

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code
    /sdlc-spdd-code @spdd/canvas/FEAT-001-order-status-api.md operation T01

The coding agent should:

- read the canvas.
- implement only T01.
- add or update tests.
- update the progress log.
- stop before starting T02.

## 9. Review Against the Canvas

| Part | Action |
|------|--------|
| SPDD | Run: |

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

## 10. Persist Memory Before You Stop

| Part | Action |
|------|--------|
| SDLC + Planning | At the end of the session: |

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id FEAT-001-order-status-api \
      --phase code \
      --summary "Implemented T01 for order status lookup." \
      --validation "Tests run: <command/result>" \
      --milestone milestone-1.md \
      --roadmap-note "FEAT-001 completed first operation." \
      --next "/sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md"

`--milestone` is optional when the Work ID already appears in a `milestone-*.md` file (auto-detected). This stores context in files that future sessions can read.

## First-Day Checklist

- [ ] Framework installed or upgraded.
- [ ] `/sdlc-spdd-init` completed.
- [ ] Work ID chosen.
- [ ] Milestone work mapped (if applicable).
- [ ] Session brief created; Resume Prompt pasted.
- [ ] Requirement planned into a REASONS Canvas.
- [ ] Architecture reviewed.
- [ ] One operation implemented.
- [ ] Review run.
- [ ] Memory captured.

## Where to Go Next

- [Three-part operating path](three-part-operating-path.md)
- [10,000-foot view](ten-thousand-foot-view.md)
- [Installing into your project](installing-into-your-project.md)
- [Maintaining your project](maintaining-your-project.md)
- [Top useful concepts and commands](useful-concepts-and-commands.md)
