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

# FEAT-013: Upstream Guide git-incremental ingest + RAG maintenance

**Work ID:** FEAT-013-guide-git-incremental-upstream  
**Milestone:** Milestone 1 (make it fast — Guide sustainment)  
**Status:** Draft  
**Date:** 2026-08-07

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Depends On | SPIKE-003-embabel-context-graph-absorption | Complete | Hybrid recommendation **accepted** |
| Related | SPIKE-001-guide-rag-context-backend | Provisional GO | Source of Layer B code on fork |

## User / Business Goal

Contribute the Embabel-general **git-incremental directory ingest** and **RAG
maintenance** operator APIs from `jmjava/guide` to upstream `embabel/guide` as a
small, reviewable PR series — without upstreaming the SPDD context-graph package.

## Scope

### IN SCOPE

- Extract / package Layer B from the fork for an upstream PR:
  `GitIncrementalDirectorySupport`, `GitIngestionRevisionStore`, `DataManager`
  hooks, `guide.git-ingestion.*` config (default **off**).
- RAG maintenance operator APIs: content-element purge preview/purge + git
  revision reset (same local-ops posture as `load-references`).
- Related tests and operator docs suitable for Embabel reviewers.
- Optional small ops hardening that unblocks the slice (only if required for the
  PR to compile/run against upstream `main`).

### NOT IN SCOPE

- `com.embabel.guide.spdd` package / `spdd_*` MCP (stays on `jmjava/guide`).
- Generic entity MCP redesign (separate FEAT if Embabel engages).
- Entity↔chunk join on projection HTTP/MCP (fork FEAT).
- SPIKE-002 local LLM / embedding format work.
- Cloud Agent dual-repo `.cursor/*` environment files.
- neo-drivine timestamp pin unless upstream already needs the same pin.

## Acceptance Criteria

- [ ] Upstreamable slice identified as a clean diff vs `embabel/guide` `main`
      (no SPDD package files in the PR).
- [ ] Unit/WebMvc tests for git-incremental + maintenance travel with the slice.
- [ ] Flags remain opt-in (`guide.git-ingestion.enabled` default false).
- [ ] Draft PR opened against `embabel/guide` (or documented blocker if Embabel
      process requires an issue first).
- [ ] Fork sync notes updated: what landed upstream vs what remains fork-local.
- [ ] Orchestrator pin/docs unchanged unless a new Guide tag is cut after merge.

## Non-Goals

- Do not force SPDD conventions into upstream Guide defaults.
- Do not open a giant “entire fork” PR.
- Do not change orchestrator markdown-first defaults or require Guide.

## Implementation home

Primary code changes: **`jmjava/guide`** → PR to **`embabel/guide`**.  
This orchestrator Work ID governs the decision artifacts, cross-links, and
acceptance tracking.

## Jira

Draft for issue creation — paste into Jira UI, MCP, or API. After create, set
**Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Story
- Summary: Upstream Guide git-incremental directory ingest + RAG maintenance
- Labels: sdlc-spdd, guide, upstream, feat-013

### Description

SPIKE-003 accepted hybrid absorption: keep SPDD projection on `jmjava/guide`;
upstream git-incremental ingest + RAG maintenance as the first Embabel-general
slice.

### Acceptance criteria (Given/When/Then)

- Given `embabel/guide` `main` without git-incremental directory ingest  
  When the FEAT-013 PR lands  
  Then operators can enable `guide.git-ingestion.enabled` and reprocess only
  changed files under configured directories, with purge/reset maintenance APIs,
  and no SPDD types are introduced.

## Next Step

    /sdlc-spdd-analysis @requirements/milestones/FEAT-013-guide-git-incremental-upstream.md
