# Requirement: CHORE-001-docgen-initial-documentation

## Summary

Bootstrap [documentation-generator](https://github.com/jmjava/documentation-generator)
(`docgen`) in this repo and produce an initial narrated-documentation bundle under
`docs/demos/`, following the course-builder integration pattern.

## Source

- `requirements/milestones/CHORE-001-docgen-initial-documentation.md`
- Analysis: `spdd/analysis/CHORE-001-docgen-initial-documentation-analysis.md`

## User Story

As a framework contributor, I want a docgen bundle and operator docs so I can
produce narrated explainers from existing `docs/` canon and understand how Guide RAG
supports SPDD analysis on this repo.

## Acceptance Criteria

- [ ] `scripts/setup-docgen-venv.sh` + `scripts/docgen-engine.path.example`
- [ ] `docs/demos/` scaffold (`docgen init` + hints + `yaml-generate`)
- [ ] Three narration segments (01–03)
- [ ] `docs/guide-rag-research-and-dogfooding.md` + `docs/README.md` link
- [ ] `docgen.yaml` sources existing `docs/*.md`
- [ ] `docs/demos/README.md`; bundle outputs gitignored
- [ ] `docgen lint` smoke on 01–03

## Non-Goals

- Video CI, GitHub Pages, Playwright, template/posture changes, Manim v1.
