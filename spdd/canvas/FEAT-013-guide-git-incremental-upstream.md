# REASONS Canvas: FEAT-013-guide-git-incremental-upstream - Guide git-incremental fork sustainment (never embabel/guide)

## Metadata

- Work ID: FEAT-013-guide-git-incremental-upstream
- Work Type: Feature
- Status: In Progress
- Readiness: ready-for-coding
- Created: 2026-08-07
- Updated: 2026-08-07 (prompt-update: **never** merge/PR to `embabel/guide`)
- Owner: Cursor Agent
- Target Project: `jmjava/guide` only (orchestrator tracks governance)
- Stack: Java/Kotlin Spring Boot (Embabel Guide fork) + Neo4j RAG
- Source System: SPIKE-003 accept, revised 2026-08-07 (fork-only; no Embabel contribution)
- Analysis: spdd/analysis/FEAT-013-guide-git-incremental-upstream-analysis.md
- Roadmap: ROADMAP.md
- Milestone: milestone-1
- Delivery stage: make it fast (fork sustainment)
- Related: SPIKE-003-embabel-context-graph-absorption (Complete), SPIKE-001-guide-rag-context-backend
- Note: Work ID slug retains `upstream` historically; **meaning is fork-local only**.

## R - Requirements

### User Goal

Keep git-incremental directory ingest + RAG maintenance healthy on **`jmjava/guide`**,
with clear docs and tests — and a hard rule that we **never** open a PR or merge
anything into `embabel/guide`.

### Business / Product Goal

Sustain the Guide fork as the durable home for SPDD + Layer B ingest ops. Treat
`embabel/guide` as a **read-only** baseline to pull from, not a contribution target.

### Acceptance Criteria

- [ ] Hard non-contribution policy documented (orchestrator + Guide absorption docs).
- [ ] Layer B inventory / allowlist kept accurate for fork maintainers (not for Embabel PRs).
- [ ] `guide.git-ingestion.enabled` remains default **false**.
- [ ] Focused Guide tests for git-incremental + maintenance run or env-blocker recorded.
- [ ] Sync process documented as **pull-only** from `embabel/guide` (`fetch`/`merge` in).
- [ ] No PR, push, or merge directed at `embabel/guide` from this Work ID (or future ones
      unless a human explicitly reverses this policy in writing).

### Non-Goals

- **Never** open a PR to `embabel/guide`.
- **Never** merge fork commits into `embabel/guide`.
- No SPDD package contribution to Embabel.
- No generic entity MCP redesign.
- No Cloud Agent `.cursor/*` contribution to Embabel.
- No SPIKE-002 model work.
- No required Guide dependency in orchestrator defaults.

### Assumptions

- SPIKE-003 inventory remains useful for classifying fork layers.
- The earlier “upstream Layer B first” follow-on is **superseded** by this policy.
- Pulling `embabel/guide` `main` into `jmjava/guide` remains allowed and expected.

### Open Questions

- Cadence for pulling `embabel/guide` into the fork (on-demand vs scheduled)?
- When to cut successor pin tags after fork-local Layer B/docs changes?

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
- `embabel/guide` — **read-only upstream remote** (pull only)

### Data / Persistence

- Git ingestion revision marker (file/store used by `GitIngestionRevisionStore`)
- ContentElement purge via maintenance APIs (existing store types)

### Files Likely Affected

- Guide: Layer B sources/tests under `com.embabel.guide.rag`, `GuideProperties`,
  `SecurityConfig`, `application.yml` (only if fork sustainment needs fixes)
- Guide: `docs/spdd-upstream-absorption.md`, `docs/spdd-branch-changes.md`
- Orchestrator: this canvas, requirement, analysis, ROADMAP, GUIDE-INTEGRATION-SPIKE

## A - Approach

### Proposed Approach

1. Prompt-update this canvas (done): forbid any contribution to `embabel/guide`.
2. Rewrite absorption docs: keep-fork for **all** SPIKE-001 layers; sync = pull-only.
3. Keep Layer B allowlist as a **fork maintainer map** (not an Embabel PR packing list).
4. Run focused Guide tests on the fork tip (or record Cloud Agent blocker).
5. Leave pin/tag policy fork-local; never condition tags on Embabel merge.

### Alternatives Considered

1. PR Layer B to `embabel/guide` — **rejected** (human policy 2026-08-07).
2. Upstream entire fork — already rejected (SPIKE-003).
3. Extract library module — deferred (no second consumer).

### Trade-Offs

- Fork drift vs Embabel is accepted; mitigated by pull-only sync + pin tags.
- Work ID name still says `upstream` — historical; docs must say fork-only.

### Risks

- Future agents reopen Embabel PRs from stale SPIKE-003 text — mitigate with
  Safeguards + absorption doc banner.
- Cloud Agent env cannot run Guide tests — record Blocked on V04/T03.

### Failure Modes

- Accidental `gh pr create` against embabel/guide → stop; close without merge; fix docs.

## S - Structure

### Files To Add (orchestrator — governance)

- Already present: requirement, analysis, canvas, feature workspace, probe log

### Files To Modify (orchestrator)

- `ROADMAP.md`, `GUIDE-INTEGRATION-SPIKE.md`, SPIKE-003 sync notes, this canvas

### Files To Add/Modify (Guide)

- `docs/spdd-upstream-absorption.md` — never-contribute policy
- `docs/spdd-branch-changes.md` — matrix: all slices keep-on-fork

### Package / Module Structure

Stay in existing `com.embabel.guide.rag` on the fork; no Embabel packaging work.

### Test Structure

- `GitIncrementalDirectorySupportTest`
- `RagMaintenanceControllerWebMvcTest`

### Documentation Structure

- Fork operator notes; absorption “never contribute” banner

## O - Operations

### T01 - Architect harden + file allowlist

- Status: Complete (superseded intent)
- Description: Originally froze allowlist for an Embabel PR. Allowlist retained as
  **fork Layer B map** only; Embabel PR target cancelled by prompt-update.
- Validation: canvas readiness `ready-for-coding`; policy forbids Embabel PR

### T02 - Document fork-only Layer B + never-contribute policy

- Status: Not Started
- Description: Update Guide absorption / branch-change docs and orchestrator
  cross-links so Layer B (and all SPIKE-001 deltas) stay on `jmjava/guide`;
  sync = pull-only from `embabel/guide`; no PR/merge to Embabel.
- Files: Guide `docs/spdd-upstream-absorption.md`, `docs/spdd-branch-changes.md`;
  orchestrator ROADMAP / GUIDE-INTEGRATION-SPIKE / SPIKE-003 notes
- Validation: docs contain explicit never-contribute language; no Embabel PR opened

### T03 - Run focused Layer B tests on the fork

- Status: Not Started
- Description: Run unit/WebMvc tests for git-incremental + maintenance on
  `jmjava/guide` tip (not an Embabel-based branch).
- Files: `src/test/.../rag/*`
- Validation: targeted tests green or documented env blocker

### T04 - Close the loop (pin/docs/registry; no Embabel PR)

- Status: Not Started
- Description: Confirm registry/roadmap/canvas Final Status language is fork-only;
  record that FEAT-013 does not produce an `embabel/guide` PR.
- Files: orchestrator canvas Final Status, progress log, GUIDE-INTEGRATION-SPIKE
- Validation: no `embabel/guide` PR URL; policy lines present

## V - Verification (freeform agent probes)

Freeform checks for design/env — **without** advancing T02–T04. Prefer
`/sdlc-spdd-verify`. Longer transcripts:
`spdd/tasks/FEAT-013-guide-git-incremental-upstream-agent-probes.md`.

### Dual-env orientation (read first in Cloud Agent)

| Checkout | Path | Role for this FEAT |
|----------|------|--------------------|
| Orchestrator | `/agent/repos/sdlc-spdd-orchestrator` | Governance (canvas, allowlist, probe log) |
| Guide | `/agent/repos/guide` | Fork home for Layer B + SPDD (**never** push to embabel) |

Active Work ID: `FEAT-013-guide-git-incremental-upstream`  
Next coding op: **T02** (docs/policy on Guide + orchestrator)  
Do **not** resume stale FEAT-004 session briefs.

### How to use

1. Pick a Suggested probe (or invent one); print Probe intent first.
2. Run read-only checks unless the user asked for a fix.
3. Append **Probe log**; classify Pass / Fail / Blocked / Inconclusive.
4. Intent change → `/sdlc-spdd-prompt-update` before T02+.

### Suggested probes

| ID | Probe | When | Pass looks like |
|----|-------|------|-----------------|
| V01 | Dual-env map — name both checkouts, branches, Work ID, next T## | Session start | Orientation table matches reality |
| V02 | Allowlist vs fork tip — Layer B paths exist; SPDD is separate package | Before T02 | Allowlist present; Layer B has no `guide.spdd` imports |
| V03 | Default-off flags — `guide.git-ingestion.enabled` default false | Anytime | Default remains false |
| V04 | Focused Guide tests on **fork** tip | After T02 / with T03 | Green or documented env blocker |
| V05 | Non-contribution check — docs/policy forbid PR/merge to `embabel/guide` | Before T04 | Explicit never-contribute language present |
| V06 | Design sanity — Layer B has no compile dependency on `com.embabel.guide.spdd` | Anytime | No imports from `guide.spdd` in allowlisted sources |

### Probe log

| When | Probe | Result | Notes |
|------|-------|--------|-------|
| 2026-08-07T21:23Z | V01 Dual-env map | Pass | Orchestrator `cursor/embabel-context-graph-research-65ca` @ `8cc65ca`; Guide `cursor/spike-003-absorption-tip-refresh-decf` @ `f870b73`; Work ID FEAT-013; next **T02**; verify prompt surfaced in `sdlc.sh next`. Detail: `spdd/tasks/FEAT-013-guide-git-incremental-upstream-agent-probes.md` |
| 2026-08-07T21:24Z | V02 Allowlist vs fork tip | Pass | All 12 allowlist paths present on Guide tip; Layer B files in `upstream/main...HEAD`; SPDD package paths also in tip diff (fork keeps both); core Layer B sources have no `guide.spdd` imports. Repo probed: **guide**. Note: “excludable for Embabel PR” framing **superseded** — we do not PR to Embabel. |
| 2026-08-07T21:26Z | Policy | Recorded | Human: never merge/PR to `embabel/guide`. Canvas prompt-updated; T04 Embabel PR cancelled. |

## N - Norms

- Implement one Operation per coding session.
- Prefer small, reviewable commits **on `jmjava/guide` / orchestrator only**.
- Update this canvas before behavior changes (`/sdlc-spdd-prompt-update`).
- Freeform probes (section V / `/sdlc-spdd-verify`) may run anytime; they do not
  count as a coding Operation and must not silently expand scope.
- When wording says “upstream”, mean **pull from** `embabel/guide`, never push/PR.

## S - Safeguards

- **Never** open a pull request against `embabel/guide`.
- **Never** push or merge fork commits into `embabel/guide`.
- `embabel/guide` remotes are fetch/merge-in only.
- Do not change `guide.spdd-projection.enabled` or `guide.git-ingestion.enabled` defaults.
- Do not include `.cursor/environment.json` as something to “contribute upstream”.
- Do not silently expand into generic entity MCP.
- Do not retag orchestrator Guide pin unless the **fork** contract changed.

## Review Checklist

- [ ] Requirements satisfied
- [ ] Entities updated correctly
- [ ] Approach followed or synced
- [ ] Structure followed or synced
- [ ] Operations completed
- [ ] Norms followed
- [ ] Safeguards respected (especially never-contribute)
- [ ] Tests added or updated / blockers recorded
- [ ] No unrelated refactors
- [ ] No unexplained dependencies
- [ ] Documentation updated if needed
- [ ] No PR/push to `embabel/guide`

## Sync Notes

Intake from SPIKE-003 accept (2026-08-07) originally sketched an Embabel Layer B PR.
**2026-08-07 prompt-update:** human policy — **never** merge/PR to `embabel/guide`.
FEAT-013 retargeted to fork sustainment + documentation. T01 allowlist kept as fork
map. T02–T04 rewritten; former “open draft PR to embabel/guide” cancelled.

## Final Status

- Status: In Progress
- Completed Date:
- PR: none to `embabel/guide` (forbidden)
- Completed Operations: T01
- Follow-Up Tasks: T02–T04 on fork/docs only
