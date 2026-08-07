# Spike: Integrating with Guide

We are exploring integration between this project and Embabel Guide (RAG + optional
DICE domain / context graph over Neo4j).

Repository: https://github.com/jmjava/sdlc-spdd-orchestrator  
Guide fork (durable pin): https://github.com/jmjava/guide (tag `sdlc-spdd-projection-v1`)

## Governed Work IDs

| Work ID | Question | Status |
|---------|----------|--------|
| [SPIKE-001-guide-rag-context-backend](requirements/milestones/SPIKE-001-guide-rag-context-backend.md) | Does DICE hybrid retrieval justify optional Guide? | Provisional GO — field dogfood |
| [SPIKE-002-local-llm-and-embedding-format](requirements/milestones/SPIKE-002-local-llm-and-embedding-format.md) | Local LLM + embedding format defaults? | Shelved / blocked on Guide+Ollama |
| [SPIKE-003-embabel-context-graph-absorption](requirements/milestones/SPIKE-003-embabel-context-graph-absorption.md) | Where should the context graph live long-term? | **Complete** — hybrid accepted; FEAT-013 intake |
| [FEAT-013-guide-git-incremental-upstream](requirements/milestones/FEAT-013-guide-git-incremental-upstream.md) | Upstream git-incremental ingest + RAG maintenance to `embabel/guide` | Analysis / plan (accepted follow-on) |

## Branch policy

- Orchestrator research: `cursor/embabel-context-graph-research-65ca` (SPIKE-003)
- Earlier SPIKE-001 exploration used `cursor/spike-*` branches; product dogfood path is
  now `main` with optional Guide (`CONTEXT_BACKEND=guide-dice`).
- Guide absorption docs: paired branch on `jmjava/guide` (see
  `docs/spdd-upstream-absorption.md` there).

## Plan

- Exploration and decisions land as SPDD artifacts (`spdd/canvas/`, `spdd/analysis/`).
- `main` stays markdown-first; Guide remains optional and runtime-resolved.
- Once a spike produces an accepted plan, open FEAT PR(s) for implementation slices
  (do not merge research spikes as silent framework rewrites).

## Operator docs

- [docs/dice-projection-runbook.md](docs/dice-projection-runbook.md)
- [docs/guide-flow.md](docs/guide-flow.md)

Status: exploratory spikes under make-it-fast — no required Guide dependency on default
installs.
