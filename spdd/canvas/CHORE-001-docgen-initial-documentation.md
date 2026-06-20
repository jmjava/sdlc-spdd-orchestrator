# REASONS Canvas: CHORE-001-docgen-initial-documentation - Initial docgen documentation bundle

## Metadata

- Work ID: CHORE-001-docgen-initial-documentation
- Work Type: Chore (documentation tooling)
- Status: Complete
- Readiness: Reviewed — Approved With Notes
- Created: 2026-06-20
- Updated: 2026-06-20 (sync)
- Owner:
- Target Project: sdlc-spdd-orchestrator (self / dogfood)
- Stack: Python (`docgen`), Bash (setup scripts), Markdown/YAML (bundle)
- Source System: User request + course-builder reference
- Analysis: `spdd/analysis/CHORE-001-docgen-initial-documentation-analysis.md`
- Roadmap: ROADMAP.md (make it right — readability / operator docs)
- Milestone: milestone-1.md (parallel track — does not block FEAT-001)
- Delivery stage: make it right (documentation clarity)
- Related PR:

## R - Requirements

### User Goal

Produce initial narrated-documentation scaffolding for the framework using the shared
`documentation-generator` (`docgen`) toolchain, mirroring how course-builder maintains
`docs/demos/`.

### Business / Product Goal

Give contributors and adopters a second consumption format (narrated demos) without
forking content away from the existing `docs/` markdown canon. Document the meta-process:
Guide RAG + MCP research and SPDD/docgen dogfooding on this repo.

### Acceptance Criteria

- [x] `scripts/setup-docgen-venv.sh` + `scripts/docgen-engine.path.example`; `docgen-engine.path` gitignored.
- [x] `docs/demos/` bundle: `docgen.yaml`, `hints/`, `narration/`, wrapper scripts from `docgen init`.
- [x] Three narration segments (01 intro/REASONS, 02 install + workflow, 03 Guide RAG + dogfood).
- [x] `docs/guide-rag-research-and-dogfooding.md` + link from `docs/README.md`.
- [x] `docgen.yaml` `narration_from_source.context.paths` point at existing `docs/*.md` (no prose duplication).
- [x] `docs/demos/README.md` bootstrap guide; regenerable outputs gitignored.
- [x] `docgen lint` passes on segments 01–03 without TTS.

### Non-Goals

- CI video render, GitHub Pages publish, Playwright/VHS capture.
- Manim scenes or composed recordings in v1 (narration-only segments).
- Changes under shipped `templates/` or posture-boundary surfaces.
- Installing the docgen bundle into target projects via `setup-agent-prompts.sh`.

### Assumptions

- Local clone: `~/github/jmjava/documentation-generator`.
- Editable engine install via `docgen-engine.path` (GitHub pip pin as fallback).
- Hand-authored narration for v1 (no `OPENAI_API_KEY` required for AC).
- Guide menke-4 corpus available locally for contributor research (not shipped to targets).
- Repo root `.venv/` for docgen (orchestrator dev only; not part of target install).

### Open Questions

- **Resolved:** three segments; narration-only v1; editable local engine preferred.
- **Resolved (architect):** hand-written **repo-root** `.gitignore` — not `docgen pages` (Pages is non-goal; `pages` only appends bundle-local rules anyway).

## E - Entities

### Application Components

- New: `docs/demos/` — docgen bundle root (orchestrator-only dev artifact)
- New: `scripts/setup-docgen-venv.sh`, `scripts/docgen-engine.path.example`
- New: `docs/guide-rag-research-and-dogfooding.md`
- New: `.gitignore` (repo root — currently absent)
- New: `.venv/` (repo root — gitignored; created by setup script)
- Reference: `~/github/jmjava/documentation-generator` (external library)
- Reference: `course-builder/docs/demos/` + `course-builder/scripts/setup-docgen-venv.sh`

### Data / Persistence

| Artifact | Role |
|----------|------|
| `docgen.yaml` | Merged config (`yaml-generate` output; hints are source of truth) |
| `hints/project-context.md` | `docgen.project` block: `env_file`, project-wide `narration_from_source` |
| `hints/segment-NN-*.md` | Per-segment `docgen.segment` + `docgen.wiring.narration.context.paths` |
| `narration/NN-*.md` | Spoken scripts (hand-authored v1; plain paragraphs) |
| `.gitignore` | `.venv/`, `scripts/docgen-engine.path`, `docs/demos/{audio,media,recordings,animations/media}` |

### Files Likely Affected

- `docs/demos/**` (new)
- `docs/guide-rag-research-and-dogfooding.md` (new)
- `scripts/setup-docgen-venv.sh`, `scripts/docgen-engine.path.example` (new)
- `.gitignore` (new at repo root)
- `docs/README.md` (links under *If You Are Contributing or Editing Docs*)

## A - Approach

### Proposed Approach

1. Adapt course-builder venv bootstrap scripts (local reference — not in menke-4 ingest).
2. Add repo-root `.gitignore` early (`.venv/`, engine path) before venv creation.
3. `docgen init docs/demos --defaults` after venv install.
4. Write `docs/guide-rag-research-and-dogfooding.md` **before** hints merge (segment 03 context path).
5. Add `hints/project-context.md` (`docgen.project` front matter) + three segment hints.
6. Run `docgen yaml-generate --merge-defaults` — do **not** hand-edit `visual_map` for v1.
7. Hand-author narration markdown (plain spoken paragraphs; no `#` headings).
8. Write `docs/demos/README.md`; smoke `docgen lint` + posture guard.

### Alternatives Considered

| Alternative | Why not now |
|-------------|-------------|
| `docgen pages` for `.gitignore` | Non-goal (no Pages); writes bundle-local file only; repo has no root ignore today |
| `narration-generate` for v1 | Requires API key; hand-author is more reviewable for framework canon |
| Full video pipeline | Deferred to CHORE-002 |

### Trade-Offs

- Narration-only v1 ships faster; no visual demo until CHORE-002.
- Hints-driven `docgen.yaml` adds indirection but prevents manual YAML drift.
- Orchestrator-only bundle: simplifies posture (no target-install surface) but dogfood is self-contained.

### Risks

| Risk | Mitigation |
|------|------------|
| Narration drifts from `docs/` canon | Single-source `context.paths`; review in Git |
| `yaml-generate` overwrites `docgen.yaml` | Hints are source of truth; review diff |
| Binary commits | Root `.gitignore` before any generate; no `generate-all` in v1 PR |
| Posture leak | No `templates/` changes; `check-posture-boundary.sh` gate |
| `docgen lint` expects recordings | v1 lint is narration-only; no `validate` full pipeline |

## S - Structure

### Files To Add

```
.gitignore                         # repo root (new)
scripts/setup-docgen-venv.sh
scripts/docgen-engine.path.example
docs/guide-rag-research-and-dogfooding.md
docs/demos/
  README.md
  docgen.yaml                      # generated — review after yaml-generate
  hints/
    README.md
    project-context.md             # docgen.project YAML front matter
    segment-01-sdlc-spdd-intro.md
    segment-02-install-and-workflow.md
    segment-03-guide-rag-dogfood.md
  narration/
    01-sdlc-spdd-intro.md
    02-install-and-workflow.md
    03-guide-rag-dogfood.md
  audio/                           # empty, gitignored
  animations/                      # empty scaffold from init, gitignored media/
  recordings/                      # empty, gitignored in v1
```

### Files To Modify

- `docs/README.md` — new row in *If You Are Contributing or Editing Docs*:
  - `guide-rag-research-and-dogfooding.md`
  - `demos/README.md` (narrated docgen bundle)

### `project-context.md` front matter (orchestrator-specific)

```yaml
docgen:
  project:
    env_file: ../../.env          # optional; OpenAI only for future TTS
    narration_from_source:
      hints:
        - "Audience: SDLC-SPDD framework contributors and adopters."
        - "Product: the orchestrator repo itself — not a target application install."
        - "Source canon lives in docs/ — do not contradict ten-thousand-foot-view or workflow."
        - "Demo bundle is narration-only v1 — no Manim or browser capture."
      context:
        paths: [README.md, docs/ten-thousand-foot-view.md, ...]
```

### Test Structure

- No new unit tests.
- Quality gates (T07): `docgen lint`, `check-posture-boundary.sh`.

## O - Operations

### T01 - Venv bootstrap + root `.gitignore` stub

- Status: Complete
- Description: Copy `setup-docgen-venv.sh` and `docgen-engine.path.example` from course-builder; adapt for orchestrator. Create repo-root `.gitignore` with `.venv/` and `scripts/docgen-engine.path` **before** running setup.
- Files: `scripts/setup-docgen-venv.sh`, `scripts/docgen-engine.path.example`, `.gitignore`
- Tests: `./scripts/setup-docgen-venv.sh`; `.venv/bin/docgen --help`
- Validation: Editable install when engine path present; GitHub pip fallback otherwise
- Depends on: —

### T02 - Guide RAG + dogfooding operator doc

- Status: Complete
- Description: Write `docs/guide-rag-research-and-dogfooding.md` (menke layers, append-ingest, MCP analysis workflow, dogfood table, what-not-to-ship, SPIKE-001 link). Add links in `docs/README.md` contributing table.
- Files: `docs/guide-rag-research-and-dogfooding.md`, `docs/README.md`
- Tests: Not applicable
- Validation: Relative links resolve; no W/R/F posture language
- Depends on: —

### T03 - `docgen init` bundle scaffold

- Status: Complete
- Description: From activated venv at repo root: `docgen init docs/demos --defaults`. Verify wrapper scripts and empty dirs. Extend `.gitignore` with `docs/demos/{audio,media,recordings,animations/media}`.
- Files: `docs/demos/**`, `.gitignore`
- Tests: `cd docs/demos && ../../.venv/bin/docgen --config docgen.yaml --help`
- Validation: Bundle tree present; no committed binaries
- Depends on: T01

### T04 - Hints + `yaml-generate`

- Status: Complete
- Description: Add `hints/README.md`, `project-context.md` (`docgen.project`), three `segment-NN-*.md` with `docgen.segment.create: true` and per-segment `narration.context.paths`. Run `docgen yaml-generate --merge-defaults`; review `docgen.yaml` diff in Git.
- Files: `docs/demos/hints/*.md`, `docs/demos/docgen.yaml`
- Tests: `docgen yaml-generate --list-gaps` — no missing narration stems
- Validation: Segments 01–03 declared; `repo_root: ../..`; `visual_map` empty; `narration_from_source.context.paths` include guide-rag doc
- Depends on: T02, T03

### T05 - Draft narration scripts

- Status: Complete
- Description: Hand-author ~60–90s spoken paragraphs per segment: 01 (SPDD/REASONS/three-part), 02 (install + workflow steps 1–6), 03 (Guide RAG dogfood). No markdown headings; align with source docs.
- Files: `docs/demos/narration/01-sdlc-spdd-intro.md`, `02-install-and-workflow.md`, `03-guide-rag-dogfood.md`
- Tests: Not applicable
- Validation: Fact-check against `docs/` canon; TTS-friendly plain text
- Depends on: T04

### T06 - `docs/demos/README.md`

- Status: Complete
- Description: Operator README mirroring course-builder bootstrap table (venv → `cd docs/demos` → `yaml-generate` → `lint`). Document optional future `generate-all` path as non-goal for v1.
- Files: `docs/demos/README.md`
- Tests: Not applicable
- Validation: A new contributor can follow steps without reading course-builder
- Depends on: T03

### T07 - Lint smoke + posture guard

- Status: Complete
- Description: `../../.venv/bin/docgen --config docgen.yaml lint` for segments 01–03; `./scripts/check-posture-boundary.sh`.
- Files: none (verification)
- Tests: `docgen lint`; `check-posture-boundary.sh`
- Validation: Lint exit 0; posture guard green
- Depends on: T05, T06

## N - Norms

### General

- Hints are the source of truth for `docgen.yaml` — re-run `yaml-generate` after hint edits.
- Do not duplicate prose from `docs/`; `guide-rag-research-and-dogfooding.md` is the only new prose doc.
- One canvas operation per coding session.
- Stage: **make it right** (operator documentation clarity).
- Docgen bundle is orchestrator dev tooling — never added to `setup-agent-prompts.sh` target install.

### Testing

- `docgen lint` is the bundle smoke test for v1 (not full `validate` — no recordings).
- `check-posture-boundary.sh` required before merge.

## S - Safeguards

- Do not run `generate-all`, `tts`, or `manim` in v1 PR.
- Do not hand-edit `visual_map` or segment lists in `docgen.yaml`.
- Do not commit `audio/`, `media/`, `recordings/`, `.venv/`, or `scripts/docgen-engine.path`.
- Do not ship Guide YAML, Neo4j data, or MCP config to target projects.
- Do not modify `templates/` or installed target surfaces.
- Do not let implementation drift without `/sdlc-spdd-sync`.

## Architecture Notes

- **Orchestrator-only scope:** `docs/demos/` and `.venv/` are framework self-improvement
  artifacts. Target projects keep `docs/sdlc-spdd/` prose; they do not receive the docgen
  bundle. This avoids expanding the install footprint and posture-boundary surface.
- **`.gitignore` decision:** repo has no root ignore file today. Hand-write at repo root
  (course-builder pattern with `docs/demos/` path prefixes). Defer `docgen pages` to
  CHORE-002 when Pages publish is in scope.
- **Hint contract:** `project-context.md` uses `docgen.project` front matter (course-builder
  pattern from menke-4 MCP). Segment files use `docgen.segment` + `docgen.wiring.narration`
  only — no `visual` wiring in v1.
- **Lint scope:** `docgen lint` checks narration scripts without requiring TTS audio or
  composed MP4 — correct gate for narration-only scaffold.
- **Sequencing:** T01+T02 parallelizable; T04 blocked on T02 (guide-rag path); T05 blocked on
  T04 (segment stems). Implement one operation per session.
- **Quality gates:** T07 is the merge gate. No new CI workflow in v1 — local smoke only.
- **Readiness rationale:** operations are small, independently verifiable, no external
  service dependency for AC, reference implementation exists (course-builder), analysis
  gaps documented. **Ready For Coding.**

## Review Checklist

- [x] Requirements satisfied
- [x] Entities updated correctly
- [x] Approach followed or synced
- [x] Structure followed or synced
- [x] Operations completed
- [x] Norms followed
- [x] Safeguards respected
- [x] `docgen lint` green
- [x] Posture guard green
- [x] Documentation updated

## Sync Notes

Plan derived from analysis (MCP menke-4). Architect hardened: repo-root `.gitignore`,
orchestrator-only scope, T01/T06 split, T04 depends on T02, `docgen.project` front matter
contract. CHORE-002: Manim + CI + optional Pages.

**Sync (2026-06-20):** Review approved with notes. All T01–T07 verified against repo.
Requirement AC checkboxes marked complete. Reconciled drift:

| Item | Resolution |
|------|------------|
| Canvas metadata | Status `Complete`; Readiness `Reviewed — Approved With Notes` |
| Top-level `narration_from_source.context.paths` | Only `README.md` at project level; full `docs/*.md` paths live under `narration_from_source.segments.*` — satisfies AC intent; documented in requirement |
| `hints/project-context.md` `docgen.project` | docgen v0.2.0 does not merge project-level front matter; only per-segment `docgen.wiring.narration` merges — accepted; optional upstream follow-up |
| `docgen lint` cwd | Must run from `docs/demos/` (not repo root) |

No stale operations. No missing tasks within CHORE-001 scope.

## Final Status

- Status: Complete (T01–T07) — synced 2026-06-20
- Completed Date: 2026-06-20
- PR:
- Follow-Up Tasks: **CHORE-002** — TTS, Manim scenes, `generate-all`/`compose`, optional CI `docgen lint` + Pages; optional docgen `docgen.project` merge upstream
