# Requirement: CHORE-001-docgen-initial-documentation

## Summary

Bootstrap [documentation-generator](https://github.com/jmjava/documentation-generator)
(`docgen`) in this repo and produce an initial narrated-documentation bundle under
`docs/demos/`, following the course-builder integration pattern. Start with scaffold +
narration + config; defer full video render pipeline to a follow-up if needed.

## Source

- User request (2026-06-20): use docgen for initial framework documentation
- Reference consumer: `courseforge/course-builder/docs/demos/` (ingested via guide `menke-4`)
- Existing prose canon: `docs/README.md`, `docs/ten-thousand-foot-view.md`, `docs/workflow.md`,
  `docs/installing-into-your-project.md`

## Motivation

The orchestrator already has strong markdown docs, but no narrated-demo bundle or
docgen wiring. Adopting docgen here dogfoods the same documentation toolchain used
in course-builder and gives a path to narrated explainers (TTS + Manim + validate)
without hand-maintaining parallel doc sets.

This chore is also a **meta-documentation** opportunity: explain how this repo uses
Embabel Guide + Neo4j as a research backend during SPDD analysis, and how the
orchestrator dogfoods its own workflow while improving itself.

## Dogfooding context

`sdlc-spdd-orchestrator` is the framework **and** its first customer:

| Layer | What we dogfood | Where it shows up |
|-------|-----------------|-------------------|
| **SPDD workflow** | Requirements → canvas → analysis → plan → architect on Work IDs in this repo | `requirements/milestones/`, `spdd/canvas/`, `milestone-1.md` |
| **Docgen toolchain** | Same `documentation-generator` + `docs/demos/` bundle pattern as course-builder | This chore → `docs/demos/` |
| **Guide RAG research** | Curated corpus in Neo4j queried via MCP during `/sdlc-spdd-analysis` | `menke-*` profiles, SPIKE-001, `spdd/analysis/` |
| **Posture guard** | Shipped `templates/` stay clean; W/R/F language lives in dev artifacts only | `scripts/check-posture-boundary.sh` |

CHORE-001 should make this loop **visible to contributors** — not only ship the docgen
scaffold, but document *why* we ingest reference material into Guide and *how* analysis
commands use it.

## Guide RAG research workflow (operator instructions)

Use this during **analysis** and when drafting narration. Full spike design lives in
`spdd/canvas/SPIKE-001-guide-rag-context-backend.md`; reference URL catalog in
`spdd/analysis/SPIKE-retrieval-reference-corpus.md`.

### Corpus layers (append, do not wipe)

Profiles live under `~/github/jmjava/guide/scripts/user-config/`. Each profile is an
**append** pass on the same Neo4j store (one ingest at a time on port `21337`):

| Profile | Purpose | Key content |
|---------|---------|-------------|
| `menke` | Code half of corpus | Local Embabel/DICE fork repos |
| `menke-2` | Reference reading | SPDD, context engineering, evals URLs (24 docs) |
| `menke-3` | Make-it-right depth | Shell, task runners, VS Code manifests, harness, craft, RAG |
| `menke-4` | **This chore** | `documentation-generator/src` + course-builder text `docs/` paths |

Run (example for menke-4):

```bash
cd ~/github/jmjava/guide
GUIDE_PROFILE=menke-4 GUIDE_PORT=21337 SERVER_PORT=21337 \
  GUIDE_INGEST_LOG=/tmp/menke-4-ingest.log ./scripts/append-ingest.sh
```

Confirm startup log: `Starting Guide with profiles: menke-4`. Wait for ingest completion
in the log before relying on MCP search.

### Research during `/sdlc-spdd-analysis`

1. Ensure Guide is running on `:21337` with the corpus that covers your Work ID
   (for CHORE-001: `menke-4` on top of prior menke passes).
2. Connect **embabel-dev MCP** (`docs_vectorSearch`, `docs_textSearch`) in Cursor.
3. During analysis, query for:
   - **Docgen API** — `docgen init`, `yaml-generate`, `narration-generate`, `validate`
   - **Consumer pattern** — course-builder `setup-docgen-venv.sh`, `hints/`, `docgen.yaml`
   - **Bundle layout** — what to gitignore (`audio/`, `media/`, `recordings/`)
4. Record findings in `spdd/analysis/CHORE-001-docgen-initial-documentation-analysis.md`
   with citations to retrieved chunks (URI/title), not hand-wavy memory.
5. Prefer **vector search** for concepts; **text search** for exact CLI flags and paths.

### What not to ship

Guide profiles, Neo4j data, and MCP wiring are **local research infrastructure**.
Target projects receive only the resulting docs, scripts, and templates — never the
ingest configs or graph store.

## Acceptance Criteria

- [x] `scripts/setup-docgen-venv.sh` (or equivalent) installs `docgen` from a local
      `documentation-generator` clone or GitHub pin; documents `scripts/docgen-engine.path.example`.
- [x] `docs/demos/` exists with `docgen.yaml`, `hints/`, and `narration/` scaffold
      (`docgen init` + `yaml-generate` pattern from course-builder).
- [x] At least **two** initial narration segments drafted (markdown under
      `docs/demos/narration/`) covering: (1) what SDLC-SPDD is + REASONS loop,
      (2) installing and daily workflow for a target project.
- [x] **`docs/guide-rag-research-and-dogfooding.md`** (or equivalent under `docs/`)
      explains: layered `menke-*` Guide profiles, append-ingest, MCP research during
      analysis, and how this repo dogfoods SPDD + docgen + Guide (link from `docs/README.md`).
- [x] Optional **third** narration segment (or section in segment 01): "how we build
      this framework" — Guide corpus, REASONS loop on self, docgen as second output format.
- [x] `docgen.yaml` `narration_from_source.context` points at existing `docs/*.md`
      sources (no duplicate prose moved out of `docs/`) — per-segment paths in
      `narration_from_source.segments.*` (see sync notes).
- [x] `docs/demos/README.md` documents bootstrap commands for contributors (venv, init,
      yaml-generate, optional `generate-all`).
- [x] `.gitignore` excludes regenerable bundle outputs (`audio/`, `media/`, `recordings/`)
      per course-builder convention.

## Non-Goals

- No GitHub Actions video render workflow in this chore (**deferred to CHORE-002**).
- No Playwright/VHS demo capture (removed from docgen; out of scope).
- No change to shipped `templates/` or posture-boundary content.
- No requirement to publish GitHub Pages from this repo in v1.

## Research / RAG

**Profile:** `menke-4` (docgen `src/` + course-builder `docs/` text paths).

**MCP:** embabel-dev `docs_vectorSearch` / `docs_textSearch` during `/sdlc-spdd-analysis`.

**Starter queries:**

- `docgen init yaml-generate hints narration_from_source`
- `setup-docgen-venv docgen-engine.path course-builder demos`
- `documentation-generator validate narration-generate`

**Related artifacts:** `SPIKE-001-guide-rag-context-backend`, `SPIKE-retrieval-reference-corpus.md`.

## Next Step

**Complete** (2026-06-20). Review: `spdd/reviews/CHORE-001-docgen-initial-documentation-review.md`.
Sync: `spdd/sync/CHORE-001-docgen-initial-documentation-sync.md`.

Follow-up: **CHORE-002** — TTS, Manim, compose, `generate-all`, optional CI/Pages.

Capture session memory; open PR when ready.
