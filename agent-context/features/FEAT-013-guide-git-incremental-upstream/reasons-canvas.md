# REASONS Canvas: FEAT-013-guide-git-incremental-upstream - Upstream Guide git-incremental ingest + RAG maintenance

## Metadata

- Work ID: FEAT-013-guide-git-incremental-upstream
- Work Type: Feature
- Status: Complete
- Readiness: complete
- Created: 2026-08-07
- Updated: 2026-08-08 (fork-only complete; never Embabel PR)
- Owner: Cursor Agent
- Target Project: jmjava/guide only (orchestrator tracks governance)
- Stack: Java/Kotlin Spring Boot (Embabel Guide) + Neo4j RAG
- Source System: SPIKE-003 accept (hybrid absorption) — **revised**: no Embabel merge asks
- Analysis: spdd/analysis/FEAT-013-guide-git-incremental-upstream-analysis.md
- Roadmap: ROADMAP.md
- Milestone: milestone-1
- Delivery stage: make it fast (fork sustainment slice)
- Related: SPIKE-003-embabel-context-graph-absorption (Complete), SPIKE-001-guide-rag-context-backend

## R - Requirements

### User Goal

Keep git-incremental directory ingest and RAG maintenance operator APIs on the
`jmjava/guide` fork (clean, testable slice) **without** opening or asking for any
PR against `embabel/guide`.

### Business / Product Goal

Sustain Embabel-general ingest ops on the fork under a hard fork-only policy;
never treat contribution-back as a workflow step.

### Acceptance Criteria

- [x] Clean Layer B slice with **no** `com.embabel.guide.spdd` paths (fork review branch OK).
- [x] Tests for git-incremental + maintenance included.
- [x] `guide.git-ingestion.enabled` remains default **false**.
- [x] **No** Embabel PR; fork-only posture enforced (Cursor rule + git guard + CI).
- [x] Fork absorption docs state fork-only forever (not a contribution queue).
- [x] Explicit fork tag `sdlc-spdd-projection-v2` cut; orchestrator pin bumped.

### Non-Goals

- **Never** open or ask for a PR against `embabel/guide`.
- No SPDD package / `spdd_*` contributed upstream.
- No generic entity MCP in this FEAT.
- No Cloud Agent `.cursor/*` env files contributed upstream.
- No SPIKE-002 model work.
- No required Guide dependency in orchestrator defaults.

### Assumptions

- SPIKE-003 hybrid recommendation remains accepted.
- Layer B on the fork is the reference implementation.
- Embabel will review small ops PRs more readily than a giant fork dump.

### Open Questions

- Does Embabel require a tracking issue before accepting a PR?
- Which ops-hardening commits (Neo4j auth / persona resilience / KSP enforcer) are
  strictly required for Layer B to build on upstream `main`?

## E - Entities

### Application Components

- `GitIncrementalDirectorySupport` — diff directory ingest vs last git revision
- `GitIngestionRevisionStore` — revision state persistence
- `DataManager` — hooks incremental path into `loadReferences()`
- `RagContentMaintenanceService` / `RagMaintenanceController` /
  `RagMaintenanceExceptionHandler` — purge preview/purge + revision reset
- `GuideProperties.gitIngestion` — opt-in config

### External Systems

- Neo4j content-element store (existing Guide RAG)
- Git working tree for configured ingest directories

### Data / Persistence

- Git ingestion revision marker (file/store used by `GitIngestionRevisionStore`)
- ContentElement purge via maintenance APIs (existing store types)

### Files Likely Affected (Guide)

- `src/main/java/com/embabel/guide/rag/GitIncrementalDirectorySupport.java`
- `src/main/java/com/embabel/guide/rag/GitIngestionRevisionStore.java`
- `src/main/java/com/embabel/guide/rag/DataManager.java`
- `src/main/java/com/embabel/guide/rag/RagMaintenanceController.java`
- `src/main/kotlin/com/embabel/guide/rag/RagContentMaintenanceService.kt`
- `src/main/kotlin/com/embabel/guide/rag/RagMaintenanceExceptionHandler.kt`
- `src/main/kotlin/com/embabel/guide/GuideProperties.kt`
- `src/main/kotlin/com/embabel/guide/chat/security/SecurityConfig.kt`
- `src/main/resources/application.yml`
- Matching tests under `src/test/.../rag/`
- Docs suitable for Embabel (not SPDD-only)

## A - Approach

### Proposed Approach

1. Architect-harden this canvas (file allowlist, PR shape, validation).
2. Create Guide branch from tip or rebase Layer B onto `upstream/main`.
3. Strip any SPDD-coupled files from the candidate commit set.
4. Run Guide unit/WebMvc tests for the slice.
5. Open draft PR to `embabel/guide` with operator notes + default-off flags.
6. Sync fork absorption docs + orchestrator cross-links with PR URL / outcome.

### Alternatives Considered

1. Upstream entire fork delta — rejected (SPIKE-003).
2. Extract a separate library module first — deferred (no second consumer).
3. Upstream ops hardening alone without git-incremental — lower value; bundle with B.

### Trade-Offs

- Smaller PR increases accept odds but may leave useful ops hardening on the fork.
- Cherry-picking onto `upstream/main` may need conflict resolution vs shipping from tip.

### Risks

- Embabel contribution process friction.
- Accidental inclusion of SPDD paths.
- Version pin entanglement.

### Failure Modes

- PR closed as out-of-scope → keep Layer B on fork; update absorption docs; stop.
- Build fails on upstream without pin → document and either minimal pin PR or fork-only.

## S - Structure

### Files To Add (orchestrator — governance)

- `requirements/milestones/FEAT-013-guide-git-incremental-upstream.md`
- `spdd/analysis/FEAT-013-guide-git-incremental-upstream-analysis.md`
- `spdd/canvas/FEAT-013-guide-git-incremental-upstream.md`
- `agent-context/features/FEAT-013-guide-git-incremental-upstream/*`

### Files To Modify (orchestrator)

- `ROADMAP.md`, `GUIDE-INTEGRATION-SPIKE.md`, work-registry

### Files To Add/Modify (Guide — implementation)

- Layer B sources/tests/docs as listed under Entities
- `docs/spdd-upstream-absorption.md` — mark FEAT-013 in progress / PR link

### Package / Module Structure

Stay in existing `com.embabel.guide.rag` package; no new top-level module.

### Test Structure

- `GitIncrementalDirectorySupportTest`
- `RagMaintenanceControllerWebMvcTest`
- Related `DataManager` / ingestion tests as needed

### Documentation Structure

- Embabel-facing operator notes (flag defaults, endpoints, local-ops posture)
- Fork absorption matrix update after PR opened

## O - Operations

### T01 - Architect harden + file allowlist

- Status: Complete
- Description: Confirm readiness Ready For Coding; freeze allowlist of Guide paths
  for the upstream PR; record Embabel PR target branch (`embabel/guide` `main`).
- Files: this canvas; Guide absorption doc
- Validation: canvas readiness `ready-for-coding`; no SPDD paths in allowlist
- Allowlist (Guide):
  - `src/main/java/com/embabel/guide/rag/GitIncrementalDirectorySupport.java`
  - `src/main/java/com/embabel/guide/rag/GitIngestionRevisionStore.java`
  - `src/main/java/com/embabel/guide/rag/DataManager.java` (incremental hooks only)
  - `src/main/java/com/embabel/guide/rag/IngestionRunner.java` (only if required by B)
  - `src/main/java/com/embabel/guide/rag/RagMaintenanceController.java`
  - `src/main/kotlin/com/embabel/guide/rag/RagContentMaintenanceService.kt`
  - `src/main/kotlin/com/embabel/guide/rag/RagMaintenanceExceptionHandler.kt`
  - `src/main/kotlin/com/embabel/guide/GuideProperties.kt` (`gitIngestion` only)
  - `src/main/kotlin/com/embabel/guide/chat/security/SecurityConfig.kt` (maintenance routes)
  - `src/main/resources/application.yml` (`guide.git-ingestion.*` docs/defaults)
  - Matching `src/test/.../rag/` tests for the above
  - Embabel-facing operator doc (new or trimmed; **not** SPDD projection docs)
  - Explicitly **excluded:** `com/embabel/guide/spdd/**`, `.cursor/**`, neo-drivine pin unless build-blocking

### T02 - Produce clean Layer B branch vs embabel/guide main

- Status: Complete
- Description: Branch/cherry-pick Layer B onto upstream base; exclude `spdd` package
  and Cursor env files.
- Files: Guide Layer B sources/tests/config/security as allowlisted
- Validation: `git diff --name-only upstream/main...HEAD` contains no `guide/spdd` paths
- Branch: `jmjava/guide` `cursor/feat-013-layer-b-upstream-f564` (based on `embabel/guide` `main` @ `67f5e9d`)
- Commit: `0cca348` — no `com.embabel/guide/spdd` paths; includes `docs/git-incremental-ingestion.md`

### T03 - Verify tests on the upstreamable slice

- Status: Complete
- Description: Run unit/WebMvc tests for git-incremental + maintenance on the branch.
- Files: `src/test/.../rag/*`
- Validation: targeted tests green (or document environment blocker)
- Result: `./mvnw -Dtest=GitIncrementalDirectorySupportTest,RagMaintenanceControllerWebMvcTest test` exit 0

### T04 - Enforce fork-only (no Embabel PR) + sync docs

- Status: Complete
- Description: Do **not** open an Embabel PR. Harden prevention (Cursor rule,
  `scripts/forbid-embabel-upstream.sh`, CI workflow, absorption posture rewrite).
- Files: Guide `.cursor/rules`, `scripts/forbid-embabel-upstream.sh`,
  `.github/workflows/forbid-embabel-upstream.yml`,
  `docs/spdd-upstream-absorption.md`; orchestrator
  `.cursor/rules/no-embabel-guide-upstream.mdc`
- Validation: forbid script OK on fork remotes; negative test rejects embabel push URL

## N - Norms

- Implement one Operation per coding session.
- Prefer small, Embabel-reviewable commits.
- Keep SPDD package out of every commit in this FEAT.
- Update this canvas before behavior changes (`/sdlc-spdd-prompt-update`).
- Record assumptions when Embabel process is unclear.

## S - Safeguards

- Do not change `guide.spdd-projection.enabled` or include SPDD sources.
- Do not change `guide.git-ingestion.enabled` default away from false.
- Do not include `.cursor/environment.json` or dual-repo install scripts.
- Do not silently expand into generic entity MCP.
- Do not retag orchestrator Guide pin until upstream merge (or explicit fork tag).

## Review Checklist

- [ ] Requirements satisfied
- [ ] Entities updated correctly
- [ ] Approach followed or synced
- [ ] Structure followed or synced
- [ ] Operations completed
- [ ] Norms followed
- [ ] Safeguards respected
- [ ] Tests added or updated
- [ ] No unrelated refactors
- [ ] No unexplained dependencies
- [ ] Documentation updated if needed
- [ ] No `com.embabel.guide.spdd` paths in upstream PR

## Sync Notes

Human clarified policy: **never ask Embabel to merge**. FEAT-013 closes fork-only.
Prevention stack landed (Cursor rules + git pre-push guard + CI). Pin
`sdlc-spdd-projection-v2` remains the dogfood default.

## Final Status

- Status: Complete
- Completed Date: 2026-08-08
- PR: fork docs/guards on `cursor/feat-013-absorption-status-f564`;
  orchestrator pin/docs on `cursor/guide-persistence-pin-f564`;
  Layer B review branch `cursor/feat-013-layer-b-upstream-f564` (not an Embabel PR)
- Completed Operations: T01–T04
- Follow-Up Tasks: none (fork-only sustainment)
