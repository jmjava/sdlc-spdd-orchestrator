# Workflow

This page is the **canonical step sequence** (15 steps, which part owns each). It is a reference table — not a daily runbook and not the prompt library.

| Need | Open |
|------|------|
| Step order and part ownership | **This page** |
| Copy-paste prompts | [Session prompt standard](session-prompt-standard.md) |
| Rules, scripts, phase checklists | [Daily runbook](daily-runbook.md) |
| Planning → SPDD → SDLC entry paths | [Three-part operating path](three-part-operating-path.md) |

The workflow is hybrid: SDLC Agents supplies the lifecycle; SPDD supplies the REASONS Canvas contract; Planning supplies roadmap, milestone, and session-note narrative.

## Three-Layer Flow

    ROADMAP.md / milestone-*.md / requirements/milestones/ / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

## Recommended Sequence

Claim the Work ID, then open a session brief. Prefer `./scripts/sdlc-spdd/sdlc.sh claim` → `start`; paste the **Resume Prompt** from `current-session.md` — see [Session prompt standard](session-prompt-standard.md). Orient anytime with `./scripts/sdlc-spdd/sdlc.sh next` or `/sdlc-spdd-whereami`.

`/sdlc-spdd-*` steps are **assistant commands** (Cursor/Copilot/Claude Code chat). `./scripts/sdlc-spdd/*` steps are **shell commands** (terminal). [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

| Step | Part | Action |
|------|------|--------|
| 1 | SDLC | **Set up prompts and memory** — from orchestrator repo: `./scripts/setup-agent-prompts.sh --target /path/to/app --all` |
| 2 | SDLC | **Initialize** — `/sdlc-spdd-init` |
| 3 | Planning → SPDD | **Map milestone work when needed** — `./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all` |
| 4 | SDLC | **Claim + start session** — `./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>` then `sdlc.sh start` (or `resume` + `start`) → paste Resume Prompt |
| 5 | SPDD (+ Planning) | **Analysis** — `/sdlc-spdd-analysis @requirements/my-feature.md @ROADMAP.md @milestone-1.md`, then `./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id <WORK-ID>` |
| 6 | SPDD (+ Planning) | **Plan** — `/sdlc-spdd-plan @spdd/analysis/<WORK-ID>-analysis.md` (requires the analysis artifact from step 5) |
| 7 | SPDD | **Architect** — `/sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md` |
| 8 | SDLC + SPDD | **Code** — `/sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01` (one operation at a time) |
| 9 | SPDD | **API test** — `/sdlc-spdd-api-test @spdd/canvas/<WORK-ID>.md` |
| 10 | SPDD | **Review** — `/sdlc-spdd-review @spdd/canvas/<WORK-ID>.md` |
| 11 | SPDD | **Prompt update when intent changes** — `/sdlc-spdd-prompt-update @spdd/canvas/<WORK-ID>.md` |
| 12 | SDLC | **Retro** — `/sdlc-spdd-retro @spdd/canvas/<WORK-ID>.md` |
| 13 | SPDD | **Sync** — `/sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md` |
| 14 | SDLC + Planning | **Capture memory and session notes** — `./scripts/sdlc-spdd/sdlc.sh capture ...` (milestone auto-detected when Work ID is in `milestone-*.md`) |
| 15 | Planning ← SPDD | **Refresh roadmap summary** — `./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .` |

## Work IDs

Use prefixes: FEAT, BUG, REF, SPIKE, DOC, TEST, CHORE.

Example: `FEAT-001-order-status-api`

## Quality Gates

See `agent-context/harness/quality-gates.md`.

## Validation

In your installed project, runtime scripts live under `scripts/sdlc-spdd/`:

    ./scripts/sdlc-spdd/validate-reasons-canvas.sh spdd/canvas/

## Related Guides

For the full documentation map, see [docs/README.md](README.md). Daily essentials:

- [Daily runbook](daily-runbook.md) — operational rhythm and checklists
- [Session prompt standard](session-prompt-standard.md) — copy-paste prompts
- [Agent session scripts](agent-session-scripts.md) — setup, resync, capture scripts
