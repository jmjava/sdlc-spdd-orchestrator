# Analysis: FEAT-013-guide-git-incremental-upstream

## Metadata

- **Work ID:** FEAT-013-guide-git-incremental-upstream
- **Requirement:** `requirements/milestones/FEAT-013-guide-git-incremental-upstream.md`
- **Prerequisite:** SPIKE-003-embabel-context-graph-absorption (**Accepted** 2026-08-07)
- **Research basis:** `spdd/analysis/SPIKE-003-embabel-context-graph-absorption-research.md` Layer B
- **Timestamp:** 2026-08-07T21:12:00Z
- **Implementation home:** `jmjava/guide` → upstream PR to `embabel/guide`

## Scope Lock-In

### IN SCOPE

- Fork Layer B: git-incremental directory ingest + RAG maintenance APIs + tests/docs
  needed for an Embabel-reviewable PR.
- Minimal cross-cutting config/security permit-all for those operator routes only
  when required for the slice to work on upstream `main`.

### NOT IN SCOPE (deferred)

| Item | Deferred to |
|------|-------------|
| `com.embabel.guide.spdd` / `spdd_*` | Keep on fork (SPIKE-003 accepted) |
| Generic entity MCP | Future FEAT if Embabel engages |
| Entity↔chunk join on HTTP/MCP | Fork FEAT after demand |
| Cloud Agent dual-repo env | Fork-local Layer D |
| SPIKE-002 models | Separate Work ID |

## Domain Keywords

- git-incremental ingest
- directory ingest revision
- RAG maintenance
- content-element purge
- Embabel Guide upstream
- `guide.git-ingestion`
- DataManager loadReferences

## Code Areas

- Guide `com.embabel.guide.rag` — git-incremental + maintenance (fork)
- Guide `GuideProperties` / `application.yml` — `gitIngestion` config block
- Guide `SecurityConfig` — permit-all for new operator routes
- Guide tests under `src/test/.../rag/`
- Guide docs: `docs/spdd-upstream-absorption.md` (posture only; not SPDD package)
- Orchestrator cross-links: `GUIDE-INTEGRATION-SPIKE.md`, `docs/dice-projection-runbook.md`

## Existing Concepts (from SPIKE-003)

| Layer | Verdict |
|-------|---------|
| A. SPDD package | Keep on fork |
| B. Git-incremental + maintenance | **Best first upstream PR** (this FEAT) |
| C. Ops hardening | Upstream with B only if needed |
| C′. neo-drivine pin | Fork-local until versions align |
| D. Cloud Agent env | Fork-local |

Upstream `embabel/guide` `main` (`67f5e9d` as of SPIKE-003) has no git-incremental
directory ingest. Fork tip carries the implementation behind
`guide.git-ingestion.enabled` (default false).

## Strategic Direction

1. Branch from current `jmjava/guide` tip (or cherry-pick Layer B onto a branch
   based on `upstream/main`).
2. Produce a **minimal diff** against `embabel/guide` `main` containing only Layer B
   (+ necessary config/security/test/doc files).
3. Exclude every `com.embabel.guide.spdd.*` path and SPDD projection docs from the PR.
4. Open draft PR to Embabel with operator walkthrough and flag defaults documented.
5. After merge (or rejection), update fork absorption docs and orchestrator pin notes.

## Risks and Gaps

| Risk | Mitigation |
|------|------------|
| Upstream rejects operator purge APIs | Keep same local-ops posture as existing `load-references`; document threat model |
| Diff entangled with SPDD package | Explicit file allowlist in canvas Operations; CI/self-check that `spdd/` paths absent |
| Agent/neo-drivine version lag | Do not include pin unless upstream build requires it |
| Embabel contribution process unknown | Open draft PR or issue first; record blocker in progress log |

## Resolved Decisions (carried from SPIKE-003 accept)

- Hybrid absorption accepted.
- First upstreamable slice = git-incremental + RAG maintenance.
- SPDD package stays on `jmjava/guide`.

## Next

`/sdlc-spdd-plan` → REASONS Canvas for FEAT-013, then `/sdlc-spdd-architect`.
