# Analysis: FEAT-013-guide-git-incremental-upstream

## Metadata

- **Work ID:** FEAT-013-guide-git-incremental-upstream
- **Requirement:** `requirements/milestones/FEAT-013-guide-git-incremental-upstream.md`
- **Prerequisite:** SPIKE-003 (Complete) — inventory reused; contribution path cancelled
- **Timestamp:** 2026-08-07T21:26:00Z
- **Implementation home:** `jmjava/guide` only
- **Policy:** **Never** PR/merge/push to `embabel/guide` (human 2026-08-07)

## Scope Lock-In

### IN SCOPE

- Fork-only sustainment of Layer B (git-incremental + RAG maintenance).
- Documentation of pull-only sync from `embabel/guide`.
- Focused tests on the fork tip.

### NOT IN SCOPE (deferred / forbidden)

| Item | Status |
|------|--------|
| PR to `embabel/guide` | **Forbidden** |
| Merge fork → Embabel | **Forbidden** |
| SPDD package contribution | Forbidden (also SPIKE-003) |
| Generic entity MCP | Future FEAT only if ever wanted on fork |
| SPIKE-002 | Separate Work ID |

## Domain Keywords

- fork sustainment
- pull-only sync
- git-incremental ingest
- RAG maintenance
- never contribute / non-contribution
- `jmjava/guide`

## Code Areas

- Guide `com.embabel.guide.rag` — Layer B on fork
- Guide docs `docs/spdd-upstream-absorption.md` — policy home
- Orchestrator canvas/ROADMAP/GUIDE-INTEGRATION-SPIKE — governance

## Strategic Direction (revised)

1. Keep all SPIKE-001 layers on `jmjava/guide`.
2. Use `embabel/guide` only as `git fetch` / merge-in baseline.
3. Retarget FEAT-013 Operations away from Embabel PRs (prompt-update done).
4. Agents must treat “upstream” wording as **pull-from**, never push/PR.

## Risks

| Risk | Mitigation |
|------|------------|
| Stale SPIKE-003 “upstream Layer B” text | Canvas Safeguards + absorption banner |
| Accidental `gh pr` to embabel | Explicit Never in Ops T04 validation |

## Next

`/sdlc-spdd-code … operation T02` — document fork-only + never-contribute policy.
