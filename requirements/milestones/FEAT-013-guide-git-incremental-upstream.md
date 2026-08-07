---
work_id: "FEAT-013-guide-git-incremental-upstream"
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
  - "SPIKE-003-embabel-context-graph-absorption"
related:
  - "SPIKE-001-guide-rag-context-backend"
---

# FEAT-013: Guide git-incremental fork sustainment (never embabel/guide)

**Work ID:** FEAT-013-guide-git-incremental-upstream  
**Milestone:** Milestone 1 (make it fast — fork sustainment)  
**Status:** Draft (prompt-updated 2026-08-07)  
**Date:** 2026-08-07

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Depends On | SPIKE-003-embabel-context-graph-absorption | Complete | Inventory kept; Embabel contribution path **cancelled** |
| Related | SPIKE-001-guide-rag-context-backend | Provisional GO | Layer B lives on fork |

## User / Business Goal

Sustain git-incremental ingest + RAG maintenance on **`jmjava/guide`**, with a hard
rule that we **never** open a PR or merge into `embabel/guide`. Upstream is
pull-only.

## Scope

### IN SCOPE

- Document never-contribute / pull-only sync policy (Guide + orchestrator).
- Keep Layer B inventory/allowlist accurate for fork maintainers.
- Run or record focused Layer B tests on the fork tip.
- Confirm defaults stay opt-in (`guide.git-ingestion.enabled` default false).

### NOT IN SCOPE

- Any PR, push, or merge to `embabel/guide`.
- Contributing `com.embabel.guide.spdd` / `spdd_*` anywhere outside the fork.
- Generic entity MCP, SPIKE-002, Cloud Agent env “upstreaming”.

## Acceptance Criteria

- [ ] Never-contribute policy explicit in Guide absorption docs + orchestrator links.
- [ ] Layer B fork map (allowlist) remains accurate.
- [ ] Focused Guide tests green or env-blocker recorded.
- [ ] No `embabel/guide` PR created for this Work ID.

## Non-Goals

- Do not contribute to Embabel Guide.
- Do not force SPDD conventions into Embabel defaults (N/A — we are not contributing).

## Implementation home

**`jmjava/guide` only.** Orchestrator tracks governance.  
Work ID slug retains `upstream` historically; meaning is fork-local.

## Jira

- Key: TBD
- Issue type: Story
- Summary: Guide git-incremental fork sustainment (never embabel/guide)
- Labels: sdlc-spdd, guide, fork-only, feat-013

## Next Step

    /sdlc-spdd-code @spdd/canvas/FEAT-013-guide-git-incremental-upstream.md operation T02
