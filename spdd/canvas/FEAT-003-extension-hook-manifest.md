# REASONS Canvas: FEAT-003-extension-hook-manifest - Extension/hook manifest

## Metadata

- Work ID: FEAT-003-extension-hook-manifest
- Work Type: Feature (refactor)
- Status: Draft
- Readiness: Needs Analysis
- Created: 2026-06-19
- Updated: 2026-06-19
- Owner:
- Target Project: sdlc-spdd-orchestrator (self / dogfood)
- Stack: Bash + Markdown
- Source System: Roadmap
- Roadmap: ROADMAP.md
- Milestone: milestone-1.md
- Delivery stage: make it right (extensibility)
- Related PR:

## R - Requirements

### User Goal

Understand and add framework extension points (phase extensions, skills, hooks) from
one explicit manifest instead of inferring them from script behavior.

### Business / Product Goal

Make the existing extension mechanism legible and safe to extend, so future features
and target projects can plug in without reverse-engineering `resolve-agent-context.sh`.

### Acceptance Criteria

- [ ] A manifest declares extension points: phase extensions, skills, hooks (path, phase/trigger, description).
- [ ] `resolve-agent-context.sh` reads the manifest and resolves the same set of files it does today (no behavior change).
- [ ] When no manifest exists, current convention-based resolution still works (backward compatible).
- [ ] An example extension exercises the manifest end to end.
- [ ] The manifest format is documented for contributors.

### Non-Goals

- No hook execution runtime beyond declaring hook points (keep MVP declarative).
- No change to skill authoring.

### Assumptions

- Today's extension dirs (`_all-agents`, `*-agent`, `extensions/skills/`) are the points to formalize.
- Markdown-first/declarative is acceptable; no new datastore.

### Open Questions

- Manifest format/location (`agent-context/extensions/manifest.md` table vs. front matter) — decide in analysis.
- Whether hooks are only *declared* now and *executed* in a later make-it-fast Work ID.

## E - Entities

### Application Components

- New: extension manifest file
- Existing consumer: `scripts/resolve-agent-context.sh` (`collect_extension_md`, skills discovery)

### Files Likely Affected

- `agent-context/extensions/` (manifest + example)
- `scripts/resolve-agent-context.sh`
- docs describing extensions

## A - Approach

### Proposed Approach

1. Inventory how `resolve-agent-context.sh` currently discovers extensions/skills/phases.
2. Define a manifest that captures those points explicitly; keep convention fallback.
3. Teach the resolver to prefer the manifest, asserting identical resolution to today.
4. Add an example extension + contributor docs.

### Alternatives Considered

- Keep pure convention (rejected: not legible/extensible).
- Structured YAML/JSON manifest (consider vs. markdown table in analysis; prefer markdown-first).

### Trade-Offs

- A manifest is one more file to keep current, but it documents the contract that is currently implicit.

### Risks

- Manifest and convention diverging → resolver treats manifest as source of truth, convention as fallback only.

### Failure Modes

- A malformed manifest must fall back to convention (or fail loudly), never silently drop extensions.

## S - Structure

### Files To Add

- `agent-context/extensions/manifest.md` (format TBD in analysis)
- An example extension under `agent-context/extensions/`

### Files To Modify

- `scripts/resolve-agent-context.sh`
- extension docs

### Test Structure

- Resolution test: manifest vs. convention produce the same set for the example.

## O - Operations

### T01 - Inventory current extension resolution

- Status: Not Started
- Description: Document how phases/skills/hooks are discovered today.
- Files: spdd/analysis/FEAT-003-extension-hook-manifest-analysis.md
- Tests: Not applicable
- Validation: Analysis review

### T02 - Define the manifest format

- Status: Not Started
- Description: Specify the manifest declaring phase extensions, skills, and hook points.
- Files: agent-context/extensions/manifest.md
- Tests: Not applicable
- Validation: Format documented + reviewed

### T03 - Read the manifest in resolve-agent-context.sh

- Status: Not Started
- Description: Resolve from manifest with convention fallback; assert identical results to today.
- Files: scripts/resolve-agent-context.sh
- Tests: resolution parity test (manifest vs. convention)
- Validation: same resolved set; no behavior change without a manifest

### T04 - Example extension + docs

- Status: Not Started
- Description: Add a worked example and contributor documentation.
- Files: agent-context/extensions/*, docs/*
- Tests: example resolves via manifest
- Validation: doc consistency

## N - Norms

### General

- Backward compatible: no manifest = today's behavior.
- Update this canvas before behavior changes.
- Markdown-first; no new datastore for MVP.

### Testing

- Resolution parity test is the gate.

## S - Safeguards

- Do not code until this canvas is Ready For Coding.
- Manifest is declarative for MVP; do not add a hook execution runtime under this Work ID.
- Do not let implementation drift from this canvas without running `/sdlc-spdd-sync`.

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
- [ ] Documentation updated if needed

## Sync Notes

Builds on the existing `agent-context/extensions/` convention. Needs an analysis pass
before coding. Use sync notes to track drift.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
