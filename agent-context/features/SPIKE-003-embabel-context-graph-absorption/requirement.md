---
work_id: "SPIKE-003-embabel-context-graph-absorption"
jira_key: ""
jira_epic: ""
jira_type: "Story"
jira_status: "Draft"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-1"
blocks: []
depends_on:
  - "SPIKE-001-guide-rag-context-backend"
related:
  - "SPIKE-002-local-llm-and-embedding-format"
---

# Requirement: SPIKE-003-embabel-context-graph-absorption

## Summary

Time-boxed research spike: decide how to **absorb** the SPIKE-001 Embabel Guide
**context / domain graph** (typed `__Entity__` projection + `spdd_*` MCP retrieve) into a
durable long-term shape — upstream `embabel/guide`, a maintained `jmjava/guide` fork
module, or a thinner wrapper over Embabel library `SearchOperations` — without collapsing
markdown-first defaults or conflating this with SPIKE-002 (local models).

## Source

- Roadmap: ROADMAP.md (make it fast — optimization; follows SPIKE-001 provisional GO)
- Prerequisite: SPIKE-001-guide-rag-context-backend (leg 3 projection shipped on
  `jmjava/guide` tag `sdlc-spdd-projection-v1`)
- Sibling: SPIKE-002-local-llm-and-embedding-format (shared substrate; different question)

## Question to answer

1. Which fork surfaces are **SPDD-specific** vs reusable Embabel “context graph”
   capabilities that belong upstream?
2. What is the **minimal upstreamable slice** vs what should stay forever on
   `jmjava/guide` / orchestrator-only?
3. Should follow-on work target (a) PR into `embabel/guide`, (b) long-lived fork package,
   or (c) extract a library module — and under what criteria?

## Why a spike (not a feature)

SPIKE-001 already built the graph in the Guide fork and provisionally shipped the
optional orchestrator path. The remaining risk is **sustainability and upstreamability**,
not greenfield projection. The output is a **decision + inventory**, not a production
integration rewrite.

## Success / decision criteria

- [x] Fork delta inventory vs `embabel/guide` `main` with upstreamability matrix.
- [x] Explicit classification: SPDD-specific vs reusable Embabel context-graph surface.
- [x] Written recommendation: upstream PR / maintain fork / extract module (or hybrid).
- [x] Remaining graph gaps listed with severity (entity↔chunk join, Operation/Keyword,
      generic entity MCP vs `spdd_*`).
- [x] Follow-on FEAT sketch only if recommendation says “absorb further”; otherwise
      document keep-fork posture and sync process.
- [x] Human accept/reject — **Accepted** 2026-08-07 → `FEAT-013-guide-git-incremental-upstream`.

## Dependencies / sequencing

- After SPIKE-001 provisional GO and Guide tag `sdlc-spdd-projection-v1`.
- Independent of SPIKE-002 (local LLM / embedding format).
- Does not block SPIKE-001 field dogfood (T06 keep/rollback).

## Non-Goals

- No rewrite of the projection package.
- No change to markdown-first defaults or required Guide dependency.
- No collapsing into SPIKE-002 model work.
- No mandatory upstream PR in this spike — research may conclude “keep fork”.

## Branch policy

- Orchestrator: `cursor/embabel-context-graph-research-65ca`
- Guide durable checkout edits: paired branch on `jmjava/guide`
  (`cursor/embabel-context-graph-absorption-fdca`)

## Next Step

Complete. Recommendation accepted. Continue on
`/sdlc-spdd-analysis @requirements/milestones/FEAT-013-guide-git-incremental-upstream.md`
(or resume that Work ID).

## Jira

Draft for issue creation — paste into Jira UI, MCP, or approved API.
After create, set **Key** and commit.

- Key: TBD
- Issue type: Story
- Summary: SPIKE-003 Embabel context-graph absorption
- Labels: spike, guide, dice

## GitHub

Optional — use when tracking is GitHub Issues instead of/in addition to Jira.

- Number: TBD
- Title: SPIKE-003 Embabel context-graph absorption
- Labels: spike
- URL:
