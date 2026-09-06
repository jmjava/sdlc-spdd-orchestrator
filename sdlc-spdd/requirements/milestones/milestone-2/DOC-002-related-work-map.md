---
work_id: "DOC-002-related-work-map"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Documentation"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-2"
blocks:
  - "TEST-001-evaluation-protocol"
depends_on:
  - "SPIKE-004-academic-contribution-bar"
related:
  - "DOC-001-research-questions-and-constructs"
---

# DOC-002: Related-work and novelty matrix

**Work ID:** DOC-002-related-work-map  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** To Do  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | `TEST-001-evaluation-protocol` | Planned | See milestone-2 |
| Depends On | `SPIKE-004-academic-contribution-bar` | Planned | See milestone-2 |
| Related | `DOC-001-research-questions-and-constructs` | Planned | See milestone-2 |

## User / Business Goal

Position SDLC-SPDD against parent methods and 2024–2026 AI-SE tooling so a referee can see the delta in one matrix.

## Scope

### IN SCOPE

- Matrix: Spec Kit, OpenSpec, OpenSPDD, BMAD, Fowler SPDD, SDLC Agents, Aider, SWE-agent, OpenHands, AutoGen/CrewAI, Cursor/Copilot/Claude native memory, design-rationale and process-modeling classics
- One-sentence novelty claim the authors would defend in rebuttal
- What we are *not* claiming (new LLM, new RAG theory, compiled multi-agent runtime)

### NOT IN SCOPE

- A complete literature review of all AI coding papers
- Citing Embabel/Guide as an upstream PR

## Acceptance Criteria

- [x] Committed related-work matrix with claim × system × delta
- [x] Novelty sentence is consistent with DOC-001 RQs
- [x] Guide remains fork-only; no Embabel-upstream framing

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Documentation
- Summary: Related-work and novelty matrix
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Position SDLC-SPDD against parent methods and 2024–2026 AI-SE tooling so a referee can see the delta in one matrix.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Related-work and novelty matrix
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-2/DOC-002-related-work-map.md
