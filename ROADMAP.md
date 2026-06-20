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
| **Make it right** | **active** | Refactor the *existing* framework for readability, maintainability, and extensibility — clearer code/docs, shared script helpers, drift-proof command generation, and clean extension points. No new optimization features. |
| **Make it fast** | horizon (done last) | Prompt and context optimization — *and* the measurement that drives it (an optimization ledger, leading indicators, a `spdd --metrics` surface, hook-driven efficiency). |

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

## Milestone 1 — Make it right (active)

See [milestone-1.md](milestone-1.md). Goal: take the framework from its current
working state to "right" — refactor the existing code and docs for readability,
maintainability, and extensibility, and ship each refactor as working code. Prompt
optimization is deferred to "make it fast" and comes last.

## Post-MVP backlog

Each item names the Beck stage it serves (see [Delivery posture](#delivery-posture-kent-beck-make-it-work--make-it-right--make-it-fast)). Near-term work is **make it right** (refactors); **make it fast** (prompt optimization and its measurement) comes last.

### Make it right — refactor the existing framework (do first)

| Item | Concern |
|------|---------|
| Shared script library (`scripts/lib/`) for capture/resolve/verify | Maintainability |
| Single canonical command spec → generated Cursor/Copilot/Claude adapters | Maintainability (kills drift) |
| Golden-path regression dogfood (fixed stub → analysis→plan→architect diff) | Maintainability |
| Session-brief archive/rotation (`agent-context/sessions/` → `archive/`; data is already extracted into memory at capture) | Maintainability |
| Code + docs readability pass (consistent structure, naming, examples) | Readability |
| Extension/hook manifest in `agent-context/extensions/` | Extensibility |
| Initial `docgen` narrated-docs bundle (`docs/demos/`) | Readability / operator docs (CHORE-001) |

### Make it fast — prompt optimization (do last)

| Item | Concern |
|------|---------|
| Prompt-optimization ledger (`agent-context/memory/prompt-optimization-log.md`) | Measurement for optimization |
| Capture metric flags (`--readiness`, `--review-result`, `--rework`, `--context-files`) → indexed rows (Kind: `metric`) | Measurement for optimization |
| Canvas `readiness:` front matter + leading indicators (validate/review counts) | Measurement for optimization |
| `spdd --metrics` surface over the ledger and indexes | Optimization |
| Act on metrics: prompt + context optimization | Optimization |
| Context-budget telemetry and enforcement | Optimization |
| DICE hybrid context backend (SPIKE-001): guide/Neo4j — lexical index + embedding discovery + typed domain graph (Domain-Integrated Context Engineering); spike for go/no-go | Optimization (spike) |
| Local models + embedding format (SPIKE-002): local tool-capable LLM (Ollama, OpenAI-compatible) + changed embedding format (e.g. 384→768-dim); spike for go/no-go | Optimization (spike) |

## Dogfooding future work through SPDD

This project drives its own roadmap through the SDLC-SPDD workflow — every backlog
item above becomes a governed Work ID, not an ad-hoc change. The REASONS Canvas is
the contract that moves each item through the stages.

Standard loop for any backlog item:

1. **Requirement** — capture intent in `requirements/milestones/<WORK-ID>.md`
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

Work IDs are numbered in execution order: make-it-right refactors (FEAT-001→003)
first, prompt optimization (FEAT-004→005) last. Only the specced canvas appears below;
the rest are planned.

| Work ID | Canvas | Stage | Status |
|---------|--------|-------|--------|
| FEAT-004-prompt-optimization-ledger | spdd/canvas/FEAT-004-prompt-optimization-ledger.md | make it fast (prompt optimization) | Specced — deferred until make-it-right refactors land |
| SPIKE-001-guide-rag-context-backend | spdd/canvas/SPIKE-001-guide-rag-context-backend.md | make it fast (optimization, spike — DICE hybrid) | Draft — parked behind FEAT-004/005 |
| SPIKE-002-local-llm-and-embedding-format | spdd/canvas/SPIKE-002-local-llm-and-embedding-format.md | make it fast (optimization, spike — local models + embedding format) | Draft — parked behind FEAT-004/005 |

Planned follow-on canvases (not yet specced):

| Planned Work ID | Scope | Stage |
|-----------------|-------|-------|
| FEAT-001-shared-script-library | `scripts/lib/` shared helpers for capture/resolve/verify | make it right (maintainability) — **do first** |
| FEAT-002-command-spec-generation | Single canonical command spec → generated Cursor/Copilot/Claude adapters | make it right (maintainability) |
| FEAT-003-extension-hook-manifest | Extension manifest with phase/skills/hooks | make it right (extensibility) |
| FEAT-005-canvas-readiness-indicators | Machine-parseable canvas `readiness:` + validate/review leading indicators | make it fast (measurement for optimization) |
| CHORE-001-docgen-initial-documentation | Bootstrap `docgen` under `docs/demos/` + two initial narration segments | make it right (operator documentation) |

Refresh this section from canvases with:

    ./scripts/sync-roadmap-from-spdd.sh --target .

<!-- SDLC-SPDD-ROADMAP-SUMMARY:START -->

## SDLC-SPDD Work Summary

Generated: 2026-06-20T13:47:47Z

| Work ID | Title | Type | Status | Milestone | Source | Canvas |
|---------|-------|------|--------|-----------|--------|--------|
| CHORE-001-docgen-initial-documentation | Initial docgen documentation bundle | Chore (documentation tooling) | Complete | milestone-1.md (parallel track — does not block FEAT-001) | TBD | spdd/canvas/CHORE-001-docgen-initial-documentation.md |
| FEAT-001-shared-script-library | Shared script library (scripts/lib/) | Feature (refactor) | Draft | milestone-1.md | TBD | spdd/canvas/FEAT-001-shared-script-library.md |
| FEAT-002-command-spec-generation | Single command spec → generated adapters | Feature (refactor) | Draft | milestone-1.md | TBD | spdd/canvas/FEAT-002-command-spec-generation.md |
| FEAT-003-extension-hook-manifest | Extension/hook manifest | Feature (refactor) | Draft | milestone-1.md | TBD | spdd/canvas/FEAT-003-extension-hook-manifest.md |
| FEAT-004-prompt-optimization-ledger | Prompt-optimization ledger + capture metrics | Feature | Draft | milestone-1.md | TBD | spdd/canvas/FEAT-004-prompt-optimization-ledger.md |
| FEAT-005-canvas-readiness-indicators | Canvas readiness + leading indicators | Feature | Draft | milestone-1.md | TBD | spdd/canvas/FEAT-005-canvas-readiness-indicators.md |
| SPIKE-001-guide-rag-context-backend | Guide as a DICE hybrid context backend | Spike | Draft | TBD | TBD | spdd/canvas/SPIKE-001-guide-rag-context-backend.md |
| SPIKE-002-local-llm-and-embedding-format | Local models + embedding format for the retrieval backend | Spike | Draft | TBD | TBD | spdd/canvas/SPIKE-002-local-llm-and-embedding-format.md |
<!-- SDLC-SPDD-ROADMAP-SUMMARY:END -->
