# Milestone 4 — Documentation truth and release hygiene

## Goal

Every document describes the system as it is: the layout `init` creates, the one engine and one persistence model of Milestone 3, current versions and current work. There is one authoring root for shipped docs, generated grounding for the three assistants, zero broken links enforced in CI, and a registry that is the truth `list-work` reports.

**Stage:** make it right (docs). Runs in parallel with Milestone 3; items that describe purged behavior (DOC-006) wait for the corresponding REF to land.

Analysis that opened this milestone: `spdd/analysis/SPIKE-005-architecture-review-analysis.md` (M11–M13).

## Outcome (definition of done)

- `grep -rn 'docs/sdlc-spdd\|agent-context/harness\|scripts/sdlc-spdd/\|work-registry.tsv' docs templates README.md CONTRIBUTING.md` returns nothing.
- `scripts/verify-doc-links.sh` reports 0 broken and runs in CI.
- `sdlc-spdd/docs/` differs from `docs/` only in the intended installed README and the research trees, and CI proves it.
- Assistant grounding files are generated from one spec + path map, same as command adapters.
- `design-decisions.md` reads as ADRs for storage v3; `STARTER-SPEC.md` is archived.
- Version is declared once; README "Current focus" points at the ROADMAP; CHANGELOG top entry is dated.
- Every Work ID with a canvas has a terminal registry event; Milestone 2 is marked complete.

## Scope

P0 — stop teaching the wrong layout:

- [ ] DOC-004-install-path-vocabulary
- [ ] DOC-005-grounding-path-map-codegen
- [ ] CHORE-007-doc-links-gate

P1 — one source, current facts:

- [ ] CHORE-008-single-docs-authoring-root
- [ ] DOC-006-design-decisions-v3-and-starter-spec-archive
- [ ] CHORE-009-release-version-hygiene
- [ ] CHORE-010-registry-reconciliation

P2 — contributor ergonomics:

- [ ] DOC-007-glossary-and-engine-cli-guide

## Linked Work

| Work ID | Pri | Size | Requirement | Status | Notes |
|---------|-----|------|-------------|--------|-------|
| DOC-004-install-path-vocabulary | P0 | S | [requirement](DOC-004-install-path-vocabulary.md) | To Do | Docs describe the layout init actually creates |
| DOC-005-grounding-path-map-codegen | P0 | M | [requirement](DOC-005-grounding-path-map-codegen.md) | To Do | Generate assistant grounding from one path map |
| CHORE-007-doc-links-gate | P0 | M | [requirement](CHORE-007-doc-links-gate.md) | To Do | Zero broken doc links, enforced in CI |
| CHORE-008-single-docs-authoring-root | P1 | M | [requirement](CHORE-008-single-docs-authoring-root.md) | To Do | `docs/` is the only authoring root |
| DOC-006-design-decisions-v3-and-starter-spec-archive | P1 | M | [requirement](DOC-006-design-decisions-v3-and-starter-spec-archive.md) | To Do | ADRs for storage v3; archive STARTER-SPEC |
| CHORE-009-release-version-hygiene | P1 | S | [requirement](CHORE-009-release-version-hygiene.md) | To Do | One version string; current README focus |
| CHORE-010-registry-reconciliation | P1 | S | [requirement](CHORE-010-registry-reconciliation.md) | To Do | `registry.jsonl` is the truth `list-work` reports |
| DOC-007-glossary-and-engine-cli-guide | P2 | S | [requirement](DOC-007-glossary-and-engine-cli-guide.md) | To Do | Glossary and "add a CLI command" guide |

## Iteration order

1. DOC-004 (small, unblocks everything that quotes paths) → CHORE-007 (fix links, add the gate) → DOC-005 (generated grounding).
2. CHORE-009 and CHORE-010 any time (independent of Milestone 3).
3. CHORE-008 after CHORE-007; DOC-006 after REF-002 lands (it documents the purge).
4. DOC-007 after REF-005 (the CLI guide should describe the command-module layout).

## SDLC-SPDD Flow

For each work item: `/sdlc-spdd-analysis` → `/sdlc-spdd-plan` → `/sdlc-spdd-architect` → `/sdlc-spdd-code` one operation at a time → review, capture, accept, retro.

## Session Updates

2026-09-13 — Milestone opened from SPIKE-005 (docs findings M11–M13).
