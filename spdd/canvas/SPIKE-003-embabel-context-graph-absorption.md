# REASONS Canvas: SPIKE-003-embabel-context-graph-absorption - Absorb Embabel context graph into durable Guide posture

## Metadata

- Work ID: SPIKE-003-embabel-context-graph-absorption
- Work Type: Spike
- Status: In Progress
- Readiness: Ready for Review
- Created: 2026-08-07
- Updated: 2026-08-07
- Owner: Cursor Agent
- Target Project: sdlc-spdd-orchestrator (self / dogfood) + `jmjava/guide` durable checkout
- Stack: Bash + Markdown harness ↔ JVM (Embabel guide fork) + Neo4j `__Entity__` graph + MCP
- Source System: Roadmap / SPIKE-001 follow-on
- Roadmap: ROADMAP.md
- Milestone:
- Delivery stage: make it fast (optimization) — research spike
- Time-box: 1 focused research session
- Branch: `cursor/embabel-context-graph-research-65ca`
- Related: SPIKE-001 (prerequisite), SPIKE-002 (sibling, out of scope)

## R - Requirements

### User Goal

Decide how the SPIKE-001 **context / domain graph** (typed entities + typed-edge retrieve)
should live long-term relative to Embabel Guide upstream — so the fork does not become an
unmaintainable snowflake and we know what (if anything) to contribute back.

### Business / Product Goal

De-risk Guide sustainment after SPIKE-001’s provisional GO. Produce an absorption
recommendation with an explicit upstreamability matrix and follow-on FEAT sketch only
when justified.

### Framing

SPIKE-001 answered “can DICE hybrid retrieval work?” with **provisional GO**. SPIKE-003
answers “where should that graph capability live?”:

| Option | Meaning |
|--------|---------|
| A. Upstream into `embabel/guide` | Contribute reusable slices via PR(s) |
| B. Maintain `jmjava/guide` fork | Keep SPDD package + ops deltas; sync upstream periodically |
| C. Extract library module | Move reusable graph/projection helpers out of Guide app |
| D. Hybrid | Upstream generic pieces; keep SPDD markdown conventions in fork |

### Decision Criteria (what "done" means)

- [x] Inventory `jmjava/guide` tip (`sdlc-spdd-projection-v1` / `a6e3246`) vs `embabel/guide` `main`.
- [x] Classify each delta as SPDD-specific / reusable / ops-hardening / version-pin.
- [x] Written recommendation with trade-offs.
- [x] Remaining graph gaps listed (severity + owner).
- [x] Guide docs updated with absorption candidates (durable checkout).
- [ ] Human accept/reject of recommendation (post-spike).

### Non-Goals

- No production integration rewrite; no required Guide dependency.
- No SPIKE-002 local-model work.
- No mandatory upstream PR opened in this spike.

### Assumptions

- SPIKE-001 projection package on `jmjava/guide` remains the working reference implementation.
- Markdown remains source of truth; projection is a derived graph view.
- Embabel library already has `NamedEntityDataRepository` / `SearchOperations` entity APIs;
  Guide MCP still lacks *generic* domain-graph tools (only SPDD-prefixed tools exist).

### Open Questions

- Will Embabel accept SPDD directory conventions upstream, or only generic entity MCP?
- Is git-incremental directory ingest valuable enough to upstream independently of SPDD?
- Should entity↔chunk join ship before any upstream attempt (stronger DICE story)?

## E - Entities

### Application Components

- `jmjava/guide` — fork carrying `com.embabel.guide.spdd` + git-incremental RAG
- `embabel/guide` — upstream baseline
- Orchestrator optional Guide DICE path (`CONTEXT_BACKEND=guide-dice`)

### External Systems

- Neo4j (`__Entity__` + `ContentElement`)
- Embabel agent RAG libraries (`NamedEntityDataRepository`, `DataDictionary`)

### Data / Persistence

- Typed labels: WorkId, Canvas, Area, Decision, Pitfall, Pattern (+ `__Entity__`)
- Edges: `canvas`, `area`, `decision`, `pitfall`, `pattern`, `about`

## A - Approach

### Proposed Approach (research)

1. Diff `upstream/main...HEAD` on Guide; catalog layers (package / RAG ingest / cross-cutting).
2. Build upstreamability matrix (effort vs Embabel-general value vs SPDD coupling).
3. Recommend hybrid or fork-maintain posture with sync process.
4. Document absorption candidates in Guide `docs/` and orchestrator research artifact.
5. Sketch follow-on FEATs only for chosen path.

### Alternatives Considered

- Immediate large upstream PR of entire fork delta — rejected (SPDD coupling + pin friction).
- Extract module now without inventory — rejected (premature; need classification first).

### Risks

- Upstream rejects SPDD-named surfaces → sunk cost if we over-generalize too early.
- Fork drift vs `embabel/guide` grows if sync process is informal.
- Stale docs (`DynamicType` note) mislead absorbers — fix in Guide docs this spike.

## S - Structure

### Files To Add (orchestrator)

- `requirements/milestones/SPIKE-003-embabel-context-graph-absorption.md`
- `spdd/canvas/SPIKE-003-embabel-context-graph-absorption.md`
- `spdd/analysis/SPIKE-003-embabel-context-graph-absorption-analysis.md`
- `spdd/analysis/SPIKE-003-embabel-context-graph-absorption-research.md`
- `agent-context/features/SPIKE-003-embabel-context-graph-absorption/*`

### Files To Modify (orchestrator)

- `ROADMAP.md` — list SPIKE-003
- `agent-context/work-registry.tsv` — claim active
- `docs/dice-projection-runbook.md` — link SPIKE-003
- `GUIDE-INTEGRATION-SPIKE.md` — point at governed Work IDs

### Files To Add/Modify (Guide durable checkout)

- `docs/spdd-upstream-absorption.md` (new)
- `docs/spdd-branch-changes.md` — absorption candidates + fix stale schema note

## O - Operations

### T01 - Inventory fork delta vs embabel/guide

- Status: Complete
- Description: Diff `upstream/main...HEAD`; classify 39 files / ~2.8k LOC into layers.
- Validation: Research artifact table matches `git diff --name-status`.

### T02 - Upstreamability matrix + recommendation

- Status: Complete
- Description: Score each layer; recommend hybrid: keep SPDD package on fork; candidate
  upstream git-incremental + maintenance APIs separately; defer generic entity MCP.
- Validation: Written go/no-go style recommendation in research + analysis.

### T03 - Guide absorption docs in durable checkout

- Status: Complete
- Description: Add `docs/spdd-upstream-absorption.md`; update `spdd-branch-changes.md`.
- Validation: Docs reviewable on Guide branch; no runtime flag changes.

### T04 - Orchestrator cross-links + registry

- Status: Complete
- Description: ROADMAP, work-registry, runbook, GUIDE-INTEGRATION-SPIKE links.
- Validation: Work ID discoverable from roadmap and registry.

## N - Norms

- Research spike: decision artifacts over code churn.
- Markdown-first remains default; Guide stays optional.
- Prefer small upstreamable slices over one giant PR.
- Do not rename `spdd_*` tools in orchestrator command packs without a FEAT.

## S - Safeguards

- No change to `guide.spdd-projection.enabled` default (`false`).
- No merge to orchestrator `main` until recommendation accepted.
- Do not open Embabel upstream PR from this spike without human go-ahead.
- Keep SPIKE-002 shelved/independent.

## Review Checklist

- [x] Fork delta inventoried vs `embabel/guide` `main`
- [x] Upstreamability matrix written (SPDD-specific vs reusable)
- [x] Absorption recommendation recorded with trade-offs
- [x] Remaining graph gaps listed with severity
- [x] Guide durable-checkout docs updated
- [x] No production wiring / default-flag changes left behind
- [x] No secrets committed
- [ ] Human accept/reject of recommendation

## Sync Notes

2026-08-07 research: `jmjava/guide` @ `sdlc-spdd-projection-v1` (`a6e3246`) vs
`embabel/guide` `main` (`67f5e9d`) = 39 files, +2838/−22. Full notes in
`spdd/analysis/SPIKE-003-embabel-context-graph-absorption-research.md` and
`spdd/analysis/SPIKE-003-embabel-context-graph-absorption-analysis.md`.

**Recommendation:** keep `com.embabel.guide.spdd` on the fork; upstream candidate #1
is git-incremental directory ingest + RAG maintenance; defer generic entity MCP and
library extract. Guide docs: `docs/spdd-upstream-absorption.md` on
`cursor/embabel-context-graph-absorption-fdca`.

Sibling spikes: SPIKE-001 field dogfood continues independently; SPIKE-002 remains
shelved (model layer).

## Final Status

- Status: In Progress (research complete; awaiting human accept/reject)
- Completed Date:
- PR: orchestrator draft; Guide draft (absorption docs)
- Completed Operations: T01–T04
- Follow-Up Tasks: human accept/reject; optional FEAT intake for git-incremental upstream
