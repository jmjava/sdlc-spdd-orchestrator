# What's new in `v2.0.0a6`

Release tag: [`v2.0.0a6`](https://github.com/jmjava/sdlc-spdd-orchestrator/releases/tag/v2.0.0a6) · PR [#109](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/109)

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
| Lean stay-set | Stop committing runtime sprawl; keep contracts + compact memory | [Hot sessions & lean memory](hot-sessions-and-lean-memory.md) |
| Hot sessions | Resume without polluting git | same |
| Triple-path context | Same info in git / SQLite / Guide concurrently | [Triple-path context](triple-path-context.md) |
| Persistence options | Operators choose which backends are on | [Triple-path context](triple-path-context.md#configure-backends) |
| SQLite schema v4 | Local relational graph + coverage | [Local SQLite index](local-sqlite-index.md) |
| Quiet mode | Product testing without canvas T## gravity | [Quiet mode](quiet-mode.md) |
| Work-scoped resolve | Shared progress.md does not bleed other Work IDs | [Hot sessions & lean memory](hot-sessions-and-lean-memory.md#work-scoped-progress) |
| Upgrade / re-init | Move legacy noisy trees aside | [Framework upgrade](framework-upgrade.md) · `sdlc-engine agent-context upgrade` |
| Ops console Persistence tab | GUI for backends + Guide URL notes | [Ops console](ops-console.md) |

## Before / after (paths you touch daily)

| You used to open… | Open this instead |
| ----------------- | ----------------- |
| `agent-context/sessions/current-session.md` | **`.sdlc/sessions/current-session.md`** |
| `agent-context/features/<WID>/progress-log.md` | **`spdd/memory/entries/progress.md`** (shared ledger; resolve writes a scoped excerpt) |
| `agent-context/memory/known-pitfalls.md` (as the only lessons home) | **`spdd/memory/lessons/{pitfalls,decisions,patterns}.md`** (+ dual-written context-index) |
| Grep the tree for “what do we know about WID?” | `sdlc.sh db lookup --work-id <WID> --markdown` or `sdlc-engine context retrieve` |

Legacy paths may still exist after upgrade; new writes prefer the lean/hot paths.

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

1. Upgrade framework files: `./scripts/upgrade-project.sh --target <app> --all`
2. Optional: archive noisy legacy trees with `sdlc-engine agent-context upgrade`
3. Rebuild SQLite: `./scripts/sdlc-spdd/sdlc.sh db rebuild`
4. Point muscle memory at `.sdlc/sessions/current-session.md`
5. If you use Guide, keep dual-write era in mind: orchestrator still writes lean
   **and** legacy `context-index.md` until Guide dual-read lands on `jmjava/guide`
   `main` (see [SPIKE-089](agent-context-cleanup/spikes/SPIKE-089-guide-contract.md))

## Related

- Root [README](../README.md) — product front door  
- [Changelog — 2.0.0a6](../CHANGELOG.md#2000a6---2026-08-08)  
- Program internals: [agent-context-cleanup/](agent-context-cleanup/)  
- Next slice: [ADF templates + Vue3 console](adf-template-library-and-vue3-console.md)  
