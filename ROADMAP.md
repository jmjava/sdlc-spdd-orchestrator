# Roadmap

Operating-model roadmap for the SDLC-SPDD orchestrator, driven through its own
SDLC-SPDD workflow (the project dogfoods itself).

## Vision

A repository-based operating model that makes AI-assisted delivery governable,
reviewable, and reusable across Cursor, GitHub Copilot, and Claude Code.

## Delivery posture (Kent Beck: make it work → make it right → make it fast)

We sequence framework work through Kent Beck's progression. This is a posture for
planning, not a branching strategy: we stay on one line of work and advance the
whole framework through the stages in order.

| Stage | State | Focus |
|-------|-------|-------|
| **Make it work** | mostly done | MVP delivered — three assistant adapters, capture, indexes, session briefs, and validation CI all function end to end. |
| **Make it right** | **complete** | Refactors landed (FEAT-001→003, FEAT-009→012) and archived. Active: **storage v3** on integration branch. |
| **Make it fast** | **spikes (shelved)** | Measurement landed (FEAT-004/005). SPIKE-001/002 archived pending Guide MCP; act on metrics when resumed. |

Planning guidance:

- **Prompt optimization is "make it fast" and comes last.** This includes the measurement that supports it — the optimization ledger and leading indicators. We do not start it until the framework is structurally *right*.
- **Make it right first: refactor, don't add.** Near-term work makes the code and docs we already have easier to read, maintain, and extend; it does not add new optimization capability.
- **Do not optimize an unmeasured system** — but build that measurement as the first step *of* "make it fast", not as a prerequisite that jumps the queue.
- When proposing new work, name the stage it serves. Default new framework work to "make it right" (a refactor) unless it is explicitly prompt/context optimization.

### Stage classification rubric

Use this to classify any unit of work — a Work ID, a canvas Operation, or a PR.
Every contribution should name its stage.

| Stage | Goal | It belongs here when… | One-line litmus |
|-------|------|------------------------|-----------------|
| **Make it work** | The capability functions end to end | The capability does not exist yet, or does not function at all | "Does it exist and run?" |
| **Make it right** | The existing code/docs are readable, maintainable, extensible | It works, but is hard to read, change, or extend — and the fix is a refactor, not a new feature | "Does it make what already exists easier to read, change, or extend?" |
| **Make it fast** | Prompts/context optimized, driven by measurement | You are optimizing prompts or context — or building the ledger/indicators that measure that optimization | "Is it prompt/context optimization, or the measurement that drives it?" |

Tie-breaker, in order:

1. Capability doesn't exist yet → **make it work**.
2. Change refactors existing code/docs for readability/maintainability/extensibility (no new optimization) → **make it right**.
3. Change is prompt/context optimization, or the measurement built to drive it → **make it fast** (done last).

### Worked example — classifying by stage

| Work | Category | Why this category (litmus) |
|------|----------|-----------------------------|
| FEAT-001 shared `scripts/lib/` helpers | make it right | Refactors existing duplicated script logic so it is easier to maintain |
| FEAT-002 single command spec → generated adapters | make it right | Refactors three hand-kept adapters into one source — kills drift, no new capability |
| FEAT-003 extension/hook manifest | make it right | Opens a clean, documented extension point in what exists |
| FEAT-004 prompt-optimization ledger + capture metrics | make it fast | Builds the measurement that drives prompt optimization |
| FEAT-005 leading indicators (validate/review counts) | make it fast | Measurement in service of optimization |
| `spdd --metrics` query surface | make it fast | Consumes the ledger to optimize |

Drift signal: if a "make it right" refactor starts adding measurement or optimization
surface, that is the cue to stop and split it into a "make it fast" Work ID — those
come last.

## MVP (delivered)

- Repository structure, REASONS Canvas templates, and assistant command packs
- Init, install, detect, validate, sync, and session scripts
- Three-assistant adapters (Cursor, Copilot, Claude Code) with parity CI
- Spring Boot example workflow and canvas-validation GitHub Action

## Milestone 1 — Make it right (complete)

See [requirements/milestones/milestone-1/MILESTONE-1.md](requirements/milestones/milestone-1/MILESTONE-1.md).
Milestone 1 requirement stubs and canvases were removed from the working tree;
use git history. **Current focus:** storage v3 (`docs/storage-v3.md`).
`harness/skills`, `.sdlc/` runtime, test-suite restructure. Add new Work IDs under
`requirements/milestones/milestone-2/` when formalized.

## Post-MVP backlog

Each item names the Beck stage it serves (see [Delivery posture](#delivery-posture-kent-beck-make-it-work--make-it-right--make-it-fast)). Near-term make-it-right refactors and make-it-fast measurement (FEAT-004/005) are largely complete; remaining make-it-fast work is spikes and acting on metrics.

### Make it right — refactor the existing framework (do first)

| Item | Concern |
|------|---------|
| Shared script library (`scripts/lib/`) for capture/resolve/verify | Maintainability |
| Single canonical command spec → generated Cursor/Copilot/Claude adapters | Maintainability (kills drift) |
| Analysis Scope Lock-In (`/sdlc-spdd-analysis`) | Maintainability (clearer analysis contract) — **FEAT-009 Complete** |
| Jira-compatible requirements format + validator | Maintainability (planning / tracker alignment) — **FEAT-010 Complete** |
| Milestone subdirectory layout (`requirements/milestones/milestone-N/`) | Maintainability (planning layout) — **FEAT-011 Complete** |
| Session-brief rotation (`.sdlc/sessions/` → `archive/`; gitignored runtime) | Maintainability — **FEAT-012 Complete** |
| Golden-path regression dogfood (fixed stub → analysis→plan→architect diff) | Maintainability |
| Completed/cancelled work cleanup (`sdlc.sh archive` removes contracts; git history retains) | Maintainability |
| Python orchestration engine v2 (`engine/sdlc_engine`) with shell compatibility shim | Maintainability / Extensibility |
| Code + docs readability pass (consistent structure, naming, examples) | Readability |
| Phase skills under `harness/skills/` (legacy extensions/playbooks migrate away) | Extensibility |
| Initial `docgen` narrated-docs bundle (`docs/demos/`) | Readability / operator docs (CHORE-001) |

### Make it fast — prompt optimization (do last)

| Item | Concern |
|------|---------|
| Prompt-optimization ledger (`spdd/memory/lessons.jsonl`, kind=metric) | Measurement — **FEAT-004 Complete** |
| Capture metric flags (`--readiness`, `--review-result`, `--rework`, `--context-files`) → indexed rows (Kind: `metric`) | Measurement — **FEAT-004 Complete** |
| Canvas `readiness:` / Metadata readiness + leading indicators (validate/review counts) | Measurement — **FEAT-005 Complete** |
| `spdd --metrics` surface over the ledger and indexes | Optimization |
| Act on metrics: prompt + context optimization | Optimization |
| Context-budget telemetry and enforcement | Optimization |
| DICE hybrid context backend (SPIKE-001): guide/Neo4j — lexical index + embedding discovery + typed domain graph (Domain-Integrated Context Engineering); spike for go/no-go | Optimization (spike) |
| Local models + embedding format (SPIKE-002): local tool-capable LLM (Ollama, OpenAI-compatible) + changed embedding format (e.g. 384→768-dim); spike for go/no-go | Optimization (spike) |
| Embabel context-graph absorption (SPIKE-003): decide durable home for SPIKE-001 graph (`jmjava/guide` vs upstream `embabel/guide` vs module); inventory + recommendation | Optimization (spike) — **Complete** (hybrid accepted) |
| Guide git-incremental on fork (FEAT-013): Layer B kept on `jmjava/guide`; never Embabel PR; pin `sdlc-spdd-projection-v2` | Optimization (follow-on) — **Complete** (fork-only) |

## Dogfooding future work through SPDD

This project drives its own roadmap through the SDLC-SPDD workflow — every backlog
item above becomes a governed Work ID, not an ad-hoc change. The REASONS Canvas is
the contract that moves each item through the stages.

Standard loop for any backlog item:

1. **Requirement** — capture intent in `requirements/milestones/<WORK-ID>.md`
   or `requirements/milestones/milestone-N/<WORK-ID>.md`
   (or map from a milestone via `create-work-from-milestone.sh`).
2. **`/sdlc-spdd-analysis`** — scoped code scan + analysis artifact.
3. **`/sdlc-spdd-plan`** — create the REASONS Canvas (`spdd/canvas/<WORK-ID>.md`).
4. **`/sdlc-spdd-architect`** — harden the canvas; set the `readiness:` value.
5. **`/sdlc-spdd-code`** — implement one approved Operation.
6. **`/sdlc-spdd-review`** → **`/sdlc-spdd-retro`** → capture session memory.

Dogfooding rule: a backlog item is not "started" until it has a Work ID and a
REASONS Canvas. This is how the framework keeps improving itself the same way it
asks target projects to work.

## SPDD Work Map

Framework self-improvement work, governed as Work IDs (dogfooded through SPDD).

Work IDs are numbered in execution order: make-it-right refactors (FEAT-001→003,
FEAT-009→012) first, prompt optimization (FEAT-004→005) next, then spikes.
Milestone 1 feature track is Complete on the integration branch.

| Work ID | Stage | Status |
|---------|-------|--------|
| FEAT-001-shared-script-library | make it right | Complete (git history) |
| FEAT-002-command-spec-generation | make it right | Complete (git history) |
| FEAT-003-extension-hook-manifest | make it right | Complete (git history) |
| FEAT-006-python-orchestration-engine | make it right | Complete (PR #31) |
| FEAT-007-local-sqlite-index | make it right | Complete (PR #38) |
| FEAT-008-commit-message-command | make it right | Complete (PR #42) |
| FEAT-009-analysis-scope-lock | make it right | Complete (2026-07-15) |
| FEAT-010-jira-compatible-requirements | make it right | Complete (2026-07-15) |
| FEAT-011-milestone-subdirectory-layout | make it right | Complete (2026-07-15) |
| FEAT-012-session-brief-archive | make it right | Complete (2026-07-15) |
| FEAT-004-prompt-optimization-ledger | make it fast (measurement) | Complete (T01–T05) |
| FEAT-005-canvas-readiness-indicators | make it fast (measurement) | Complete (T01–T04) |
| SPIKE-001-guide-rag-context-backend | make it fast (spike — DICE hybrid) | Shelved — Guide MCP A/B |
| SPIKE-002-local-llm-and-embedding-format | make it fast (spike — local models) | Shelved |
| SPIKE-003-embabel-context-graph-absorption | make it fast (spike — absorption) | Complete (accepted 2026-08-07) |
| FEAT-013-guide-git-incremental-upstream | make it fast (fork slice) | Complete — fork-only |
| CHORE-001-docgen-initial-documentation | make it right (docs) | Complete (git history) |
| CHORE-002-docgen-video-generation | make it right (docs) | Complete (git history) |

Deferred / residual (not Work IDs yet):

| Item | Notes |
|------|-------|
| Readability pass | Consistent structure/naming across code/docs (milestone residual) |
| `spdd --metrics` query surface | Explicit FEAT-004 non-goal; later make-it-fast |
| Dual milestone root stub | Root `milestone-1.md` + subdirectory both exist; prefer subdir |

Refresh the generated summary table from canvases with:

    ./scripts/sync-roadmap-from-spdd.sh --target .

Completed Milestone 1 canvases were removed from the working tree; the table below
is historical. Use git history for canvas bodies.

<!-- SDLC-SPDD-ROADMAP-SUMMARY:START -->

## SDLC-SPDD Work Summary

Generated: 2026-07-30T12:00:00Z

| Work ID | Title | Type | Status | Milestone | Source | Canvas |
|---------|-------|------|--------|-----------|--------|--------|
| CHORE-001-docgen-initial-documentation | Initial docgen documentation bundle | Chore (documentation tooling) | Complete | milestone-1.md (parallel track — does not block FEAT-001) | TBD | spdd/canvas/CHORE-001-docgen-initial-documentation.md |
| CHORE-002-docgen-video-generation | Docgen video pipeline (TTS + Manim + compose) | Chore (documentation tooling) | Complete | milestone-1.md (parallel track — does not block FEAT-001) | TBD | spdd/canvas/CHORE-002-docgen-video-generation.md |
| FEAT-001-shared-script-library | Shared script library (scripts/lib/) | Feature (refactor) | Complete | milestone-1.md | TBD | spdd/canvas/FEAT-001-shared-script-library.md |
| FEAT-002-command-spec-generation | Single command spec → generated adapters | Feature (refactor) | Complete | milestone-1.md | TBD | spdd/canvas/FEAT-002-command-spec-generation.md |
| FEAT-003-extension-hook-manifest | Extension/hook manifest | Feature (refactor) | Complete | milestone-1.md | TBD | spdd/canvas/FEAT-003-extension-hook-manifest.md |
| FEAT-004-prompt-optimization-ledger | Prompt-optimization ledger + capture metrics | Feature | Draft | milestone-1.md | TBD | spdd/canvas/FEAT-004-prompt-optimization-ledger.md |
| FEAT-005-canvas-readiness-indicators | Canvas readiness + leading indicators | Feature | Draft | milestone-1.md | TBD | spdd/canvas/FEAT-005-canvas-readiness-indicators.md |
| FEAT-006-python-orchestration-engine | Python orchestration engine (v2) | Feature | In Progress | milestone-1.md | https://github.com/jmjava/sdlc-spdd-orchestrator/pull/31 | spdd/canvas/FEAT-006-python-orchestration-engine.md |
| FEAT-007-local-sqlite-index | Local SQLite index (pre-GUIDE) | Feature | Complete | milestone-1.md | https://github.com/jmjava/sdlc-spdd-orchestrator/pull/38 | spdd/canvas/FEAT-007-local-sqlite-index.md |
| FEAT-008-commit-message-command | Slash command: generate commit message from current changes | Feature | Complete | milestone-1.md | https://github.com/jmjava/sdlc-spdd-orchestrator/issues/41 | spdd/canvas/FEAT-008-commit-message-command.md |
| SPIKE-001-guide-rag-context-backend | Guide as a DICE hybrid context backend | Spike | Draft | TBD | TBD | spdd/canvas/SPIKE-001-guide-rag-context-backend.md |
| SPIKE-002-local-llm-and-embedding-format | Local models + embedding format for the retrieval backend | Spike | Draft | TBD | TBD | spdd/canvas/SPIKE-002-local-llm-and-embedding-format.md |
<!-- SDLC-SPDD-ROADMAP-SUMMARY:END -->
