# SDLC-SPDD (installed in this project)

These docs were installed by the SDLC-SPDD orchestrator. **Start with the six pages below** — the other `.md` files in this folder are task-specific reference.

## Assistant commands vs terminal

`/sdlc-spdd-init` and other `/sdlc-spdd-*` lines are **AI chat prompts**, not terminal commands. Run them in Cursor Chat, Copilot Chat, or Claude Code.

**Daily workflow CLI** (terminal):

    ./scripts/sdlc-spdd/sdlc.sh next          # what to do now
    ./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>
    ./scripts/sdlc-spdd/sdlc.sh start         # open session brief
    ./scripts/sdlc-spdd/sdlc.sh capture --summary "..."

In chat: `/sdlc-spdd-whereami` — same orientation as `next`, plus team registry context.

**Other shell scripts** live under `scripts/sdlc-spdd/` (for example `start-agent-session.sh`). Install/upgrade run once from the orchestrator repo (`./scripts/setup-agent-prompts.sh --target ...`), not from here.

Local agent state (gitignored): `.sdlc/pointer`, `.sdlc/workflows/`. Team claims (committed): `agent-context/work-registry.tsv`.

[How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands) · [Workflow CLI reference](../../agent-context/README.md#sdlc-pointer-current-choretask)

## Read in order

1. [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md) — hands-on first session
2. [Three-part operating path](three-part-operating-path.md) — Planning → SPDD → SDLC
3. [Session prompt standard](session-prompt-standard.md) — copy-paste prompts (**default**)
4. [Daily runbook](daily-runbook.md) — rules, scripts, checklists
5. [Workflow](workflow.md) — 13-step sequence table
6. [Installing into your project](installing-into-your-project.md) — upgrade and troubleshooting

## Quick reference

| Need | Open |
|------|------|
| One-page command sheet (print/PDF) | [Cheat sheet](sdlc-spdd-cheat-sheet.md) |
| Concept definitions (Work ID, canvas, sync…) | [Top useful concepts and commands](useful-concepts-and-commands.md) |
| Cursor / Copilot / Claude Code slash commands | [Initialization and invocation](initialization-and-invocation.md) |
| Runtime scripts + workflow CLI | [Agent session scripts](agent-session-scripts.md) |

## What each part brings

- [What planning brings](what-planning-brings.md)
- [What SPDD brings](what-spdd-brings.md)
- [What SDLC brings](what-sdlc-brings.md)

## Runtime scripts

Installed under `scripts/sdlc-spdd/` in this project. Prefer `sdlc.sh` for daily rhythm; use individual scripts when you need low-level control.
