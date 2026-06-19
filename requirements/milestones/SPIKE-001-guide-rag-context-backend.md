# Requirement: SPIKE-001-guide-rag-context-backend

## Summary

Time-boxed feasibility spike: evaluate using the Embabel **guide** project (a RAG MCP
server over Neo4j) as an *optional* retrieval/memory backend for the orchestrator —
storing work memory as we go and retrieving the most relevant of it before composing
prompt context, to optimize outcomes.

## Source

- Roadmap: ROADMAP.md (make it fast — optimization; parked behind FEAT-004/005)
- Milestone: none (not part of milestone-1 / make it right)

## Question to answer

Does retrieving context from guide's Neo4j RAG before composing a prompt measurably
improve outcomes (lower rework, stable/better review-result, fewer/looser tokens)
versus today's markdown `context-index.md` + `resolve-agent-context.sh` resolver —
enough to justify an optional JVM + Neo4j dependency?

## Why a spike (not a feature)

It introduces a heavy runtime dependency (JVM + Neo4j + a guide instance) onto a
deliberately markdown-first, portable framework. We must prove value on real sessions
before committing. The output is a **decision**, not production code.

## Success / decision criteria

- [ ] A measured A/B on at least one real Work ID: guide-RAG retrieval vs. current resolver, scored on the FEAT-004 ledger (rework, review-result) and approximate context tokens.
- [ ] A clear go / no-go recommendation with the trade-offs (value vs. dependency/adoption cost).
- [ ] If go: a sketch of the follow-on FEAT(s) — corpus/ingest wiring, retrieval seam, and (optionally) a live `remember()` write tool in the fork.

## Dependencies / sequencing

- After FEAT-004 (ledger) exists — it is the scoreboard this spike needs.
- Independent of the make-it-right refactors except that they come first.

## Non-Goals

- No production integration, no required dependency, no changes to the default
  markdown-first path.

## Next Step

When its turn comes (make it fast):

    /sdlc-spdd-architect @spdd/canvas/SPIKE-001-guide-rag-context-backend.md
