# SDLC-SPDD (installed in this project)

These docs were installed by the SDLC-SPDD orchestrator. **Start with the six pages below** — the other `.md` files in this folder are task-specific reference.

## Assistant commands vs terminal

`/sdlc-spdd-init` and other `/sdlc-spdd-*` lines are **AI chat prompts**, not terminal commands. Run them in Cursor Chat, Copilot Chat, or Claude Code.

**Daily workflow CLI** (terminal, from the repo root):

    ./sdlc-spdd/scripts/sdlc.sh next          # what to do now
    ./sdlc-spdd/scripts/sdlc.sh claim <WORK-ID>
    ./sdlc-spdd/scripts/sdlc.sh start         # open session brief
    ./sdlc-spdd/scripts/sdlc.sh capture --summary "..."
    ./sdlc-spdd/scripts/sdlc.sh accept --work-id <WORK-ID>   # promote staged lessons

In chat: `/sdlc-spdd-whereami` — same orientation as `next`, plus team registry context.

**Other shell scripts** live under `sdlc-spdd/scripts/` (for example `start-agent-session.sh`). Install/upgrade run once from the orchestrator repo (`./scripts/setup-agent-prompts.sh --target ...`), not from here.

## How storage works (single folder)

Everything the framework owns lives under one folder: `sdlc-spdd/` at the repo root.

- **Committed memory** — one lessons ledger at `sdlc-spdd/spdd/memory/lessons.jsonl` (JSONL records: decisions, pitfalls, patterns, sessions, analysis) plus the append-only work registry `sdlc-spdd/spdd/memory/registry.jsonl` (managed via `sdlc.sh claim/release`). Never edit either by hand.
- **Stage, then accept** — `sdlc.sh capture` writes records to the gitignored `sdlc-spdd/.sdlc/staged/lessons.jsonl`; at retro/sync, `sdlc.sh accept --work-id <ID>` promotes them into the committed ledger. No script ever git-commits or pushes.
- **Runtime state** (gitignored): `sdlc-spdd/.sdlc/` holds session briefs, the pointer, staged records, and the optional sqlite cache.
- **Artifacts**: canvases and phase artifacts under `sdlc-spdd/spdd/`, requirements under `sdlc-spdd/requirements/`, harness/playbooks/extensions alongside them.

Retrieve memory with `sdlc-engine context retrieve|show|digest` — never bulk-read the ledger.

[How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands) · [Runtime scripts + workflow CLI](agent-session-scripts.md)

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

## How each part works

- [Three-part operating path](three-part-operating-path.md)
- [Storage v3](storage-v3.md)
- [Workflow](workflow.md)

## Runtime scripts

Installed under `sdlc-spdd/scripts/` in this project. Prefer `sdlc.sh` for daily rhythm; use individual scripts when you need low-level control.
