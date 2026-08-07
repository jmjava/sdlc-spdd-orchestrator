# Retro: SPIKE-003-embabel-context-graph-absorption

**Date:** 2026-08-07

## What went well

- Paired dual-repo environment (Guide + orchestrator) made fork-vs-upstream inventory
  and Guide doc updates a single session without context switching.
- Layer classification (SPDD package / git-incremental / ops / pin / cloud-env) kept
  the recommendation from collapsing into “upstream everything” or “never upstream.”
- Guide absorption docs merged quickly (PR #4) while orchestrator research stayed on
  a draft PR for human accept/reject.

## What slowed us down

- Workflow resume landed at architect even though T01–T04 were already Complete —
  research spikes with readiness `reviewed` need an explicit phase jump to review.
- Tip moved after the pin (`a6e3246` → `e487220`); had to re-diff so Layer D
  (Cloud Agent dual-repo) was not mistaken for an upstreamable product slice.
- Docker/Testcontainers in this cloud VM failed dockerd NAT/iptables — inventory and
  docs did not require a live Guide boot, but full dogfood still needs a working
  container runtime.

## Lessons learned

- Absorption spikes should record **pin** and **tip** diffs separately when the fork
  tip carries ops/env docs beyond the product pin tag.
- Do not open Embabel upstream PRs from the research spike — FEAT intake after
  human accept keeps the decision reversible.

## Reusable patterns

- Dual-repo Cloud Agent env for Guide+orchestrator dogfood.
- Upstreamability matrix with coupling / friction / Embabel-general value columns.

## Pitfalls

- Treating Cursor-specific `.cursor/environment.json` as Embabel-upstreamable.
- Renaming `spdd_*` into a “generic” MCP without a separate FEAT / Embabel design.

## Ledger entry

See `agent-context/memory/prompt-optimization-log.md` — SPIKE-003 entry 2026-08-07.
