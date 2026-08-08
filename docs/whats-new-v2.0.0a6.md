# What's new in `v2.0.0a6`

Release tag: [`v2.0.0a6`](https://github.com/jmjava/sdlc-spdd-orchestrator/releases/tag/v2.0.0a6) · PR [#109](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/109)

> **Historical release notes.** The "lean stay-set" described here
> (`spdd/memory/entries/`, `lessons/*.md`, dual-written context-index) was an
> intermediate step and has since been replaced by **storage v3** — one
> committed JSONL ledger + the Guide working store. Current model:
> [Storage v3](storage-v3.md) and [Runtime and ledger](runtime-and-ledger.md).

This page is the **operator-facing** tour of what landed with the agent-context
cleanup program. For spike history and issue closeout, see
[agent-context-cleanup/](agent-context-cleanup/).

## In one paragraph

Session noise left the git commit stream. Requirements and REASONS canvases stay
as the reviewable contracts. Progress, lessons, and pointers live in a **lean
stay-set** under `spdd/memory/`. Session briefs are **hot** under `.sdlc/sessions/`.
The same facts can also live in **SQLite** and optional **Guide**, controlled by
persistence backends. Quiet mode turns off T## dogfood gravity when you are doing
product work.

## Feature map

| Feature | Why it exists | Start here |
| ------- | ------------- | ---------- |
| Lean stay-set | Stop committing runtime sprawl; keep contracts + compact memory | superseded — [Runtime and ledger](runtime-and-ledger.md) |
| Hot sessions | Resume without polluting git | same |
| Triple-path context | Same info in git / SQLite / Guide concurrently | [Triple-path context](triple-path-context.md) |
| Persistence options | Operators choose which backends are on | [Triple-path context](triple-path-context.md#configure-backends) |
| SQLite schema v4 | Local relational graph + coverage | now schema v5 — [Local SQLite index](local-sqlite-index.md) |
| Quiet mode | Product testing without canvas T## gravity | [Quiet mode](quiet-mode.md) |
| Work-scoped resolve | Shared progress file does not bleed other Work IDs | superseded — per-record ledger retrieval |
| Upgrade / re-init | Move legacy noisy trees aside | [Framework upgrade](framework-upgrade.md) · now `sdlc-engine storage migrate` |
| Ops console Persistence tab | GUI for backends + Guide URL notes | [Ops console](ops-console.md) |

## Before / after (paths you touch daily)

The middle column shows the `v2.0.0a6` paths as released; the intermediate
`spdd/memory/entries/` and `lessons/*.md` files were later folded into the
single ledger `spdd/memory/lessons.jsonl` (storage v3):

| You used to open… | `v2.0.0a6` said | Storage v3 today |
| ----------------- | --------------- | ---------------- |
| Legacy committed session briefs | **`.sdlc/sessions/current-session.md`** | unchanged |
| Legacy per-feature progress logs | shared progress entries file | ledger `session` records, retrieved on demand |
| Legacy per-kind memory logs | per-kind lesson markdown + dual-written index | ledger records (`decision`/`pitfall`/`pattern`) |
| Grep the tree for “what do we know about WID?” | `sdlc.sh db lookup` / `sdlc-engine context retrieve` | unchanged (plus `spdd_*` Guide MCP tools) |

## Quick try (dogfood this repo)

```bash
# Hot session brief
./scripts/sdlc.sh claim FEAT-001-example   # or any Work ID you have
./scripts/sdlc.sh start
ls -la .sdlc/sessions/current-session.md

# Local graph
./scripts/sdlc.sh db rebuild
./scripts/sdlc.sh db lookup --work-id FEAT-001-example --markdown

# Persistence backends
python3 -m pip install -e './engine[dev]'
sdlc-engine context backends
sdlc-engine context backends --set git-pointers,sqlite

# Quiet mode
SDLC_QUIET=1 ./scripts/sdlc.sh next
sdlc-engine agent-context quiet-status
```

## What did **not** change

- Planning / SPDD / SDLC are still three parts.
- REASONS canvases still govern execution (`spdd/canvas/<WORK-ID>.md`).
- `/sdlc-spdd-*` still runs in AI chat, not the shell.
- Guide remains **optional**. Files + SQLite work with Guide off or down.
- Jira push stays **explicit** (`issues draft|push`) — never auto on save.

## Migration notes for existing installs

Superseded — for current installs, use the storage v3 path instead:

1. Upgrade framework files: `./scripts/upgrade-project.sh --target <app> --all`
2. Convert legacy memory trees: `sdlc-engine storage migrate` ([Storage v3](storage-v3.md#migrating-a-legacy-install))
3. Rebuild the opt-in SQLite cache if enabled: `./scripts/sdlc-spdd/sdlc.sh db rebuild`
4. Point muscle memory at `.sdlc/sessions/current-session.md`

(The dual-write era described in the original notes —
[SPIKE-089](agent-context-cleanup/spikes/SPIKE-089-guide-contract.md) — ended
when Guide moved to ledger ingest at tag `spdd-projection-v3`.)

## Related

- Root [README](../README.md) — product front door  
- [Changelog — 2.0.0a6](../CHANGELOG.md#2000a6---2026-08-08)  
- Program internals: [agent-context-cleanup/](agent-context-cleanup/)  
- Next slice: [ADF templates + Vue3 console](adf-template-library-and-vue3-console.md)  
