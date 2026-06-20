# Analysis: CHORE-001-docgen-initial-documentation

## Metadata

- **Work ID:** CHORE-001-docgen-initial-documentation
- **Requirement:** `requirements/milestones/CHORE-001-docgen-initial-documentation.md`
- **Canvas:** `spdd/canvas/CHORE-001-docgen-initial-documentation.md`
- **Timestamp:** 2026-06-20T13:20:00Z
- **Research:** embabel-dev MCP (menke-4 corpus live on `:21337`) + local course-builder reference tree

## Domain Keywords

- documentation-generator (`docgen`)
- narrated-demo bundle
- hints / yaml-generate
- narration_from_source
- REASONS canvas / SPDD workflow
- Guide RAG / menke profiles
- dogfooding
- operator documentation
- docgen venv bootstrap
- posture boundary (non-shipped research infra)

## Code Areas

- `docs/` — prose canon + new `guide-rag-research-and-dogfooding.md`
- `docs/demos/` — new docgen bundle root (`docgen.yaml`, `hints/`, `narration/`)
- `scripts/` — `setup-docgen-venv.sh`, `docgen-engine.path.example`
- `.gitignore` — repo has **no** root `.gitignore` today; bundle output rules needed
- `spdd/analysis/` — this artifact (meta; not shipped to targets)

## MCP Research Summary (menke-4)

| Query | Tool | Top hit | Relevance |
|-------|------|---------|-----------|
| `docgen init yaml-generate hints` | vector | *Hints for docgen* / *yaml-generate hybrid* | Confirms hint-driven segment declaration + merge workflow |
| `setup-docgen-venv docgen-engine.path` | text | *AGENTS.md embeddable generator* | Editable install pattern; venv script not in menke-4 ingest — use local `course-builder/scripts/` |
| `validate narration-generate` | vector | *CLI commands* / *narrate_from_source.py* | Scaffold can stop at `lint` / `validate` without TTS |
| `SPDD REASONS canvas` | vector | Fowler SPDD article / mgks.dev workflow | Segment 01 narration sources |

**Corpus gap:** menke-4 ingests `documentation-generator/src` and course-builder **text** `docs/` paths only — not `course-builder/scripts/setup-docgen-venv.sh`. Plan/architect must copy that script from the local clone (already verified on disk).

**Design note from docgen AGENTS.md (MCP chunk):** the library intentionally has **no in-repo dogfood bundle**; consumer repos (course-builder) are the integration test. Orchestrator adopting `docs/demos/` is deliberate dogfood — document this explicitly in `guide-rag-research-and-dogfooding.md`.

## Existing Concepts

### Orchestrator prose canon (strong, no duplication needed)

| Doc | Role for narration |
|-----|-------------------|
| `docs/ten-thousand-foot-view.md` | Segment 01 — big idea, three parts, core loop |
| `docs/workflow.md` | Segment 02 — 15-step sequence, Work ID prefixes |
| `docs/first-day-with-sdlc-spdd.md` | Segment 02 — hands-on install → first operation |
| `docs/installing-into-your-project.md` | Segment 02 — setup-agent-prompts, verify |
| `docs/README.md` | Hub; add link to demos + guide-rag doc |
| `docs/context-loading-and-scaling.md` | Segment 03 — tier-1 vs on-demand loading |
| `spdd/analysis/SPIKE-retrieval-reference-corpus.md` | Segment 03 — menke-2 URL catalog |
| `spdd/canvas/SPIKE-001-guide-rag-context-backend.md` | Segment 03 — DICE hybrid architecture |

### Course-builder consumer pattern (reference, ingested via menke-4)

| Artifact | Pattern |
|----------|---------|
| `scripts/setup-docgen-venv.sh` | `.venv` + `DOCGEN_SRC` / `docgen-engine.path` resolution |
| `scripts/docgen-engine.path.example` | One-line absolute path, gitignored `docgen-engine.path` |
| `docs/demos/README.md` | Bootstrap table: venv → `cd docs/demos` → `docgen --config docgen.yaml` |
| `docs/demos/hints/README.md` | `project-context.md` + per-segment `segment-NN-*.md` |
| `docs/demos/hints/segment-01-intro.md` | YAML front matter: `docgen.segment`, `docgen.wiring`, `context.paths` |
| `docs/demos/docgen.yaml` | `repo_root: ../..`, `narration_from_source`, segments from hints |
| `.gitignore` (course-builder) | `docs/demos/audio/`, `animations/media/`, `media/`; recordings optional LFS |

### Docgen CLI contract (from menke-4 `documentation-generator` corpus)

1. **`docgen init`** — structure only; no hardcoded segment wiring (MCP: `init.py` docstring).
2. **`docgen yaml-generate --merge-defaults`** — merges hints front matter into `docgen.yaml`; discovers `visual_map` only when Manim scenes exist.
3. **`docgen narration-generate --segment NN`** — optional; uses `narration_from_source` hints + `context.paths` relative to `repo_root`.
4. **`docgen lint` / `docgen validate`** — smoke without OpenAI TTS for scaffold PR.
5. **`docgen pages`** — can append bundle `.gitignore` rules (`audio/*.mp3`, `animations/media/`).

Playwright/VHS paths are **removed** from docgen — aligns with chore non-goals.

## New Concepts

| Concept | Location | Notes |
|---------|----------|-------|
| `docs/demos/` bundle | new | First orchestrator docgen consumer |
| `docs/guide-rag-research-and-dogfooding.md` | new | Operator doc for Guide layers + MCP + self-dogfood |
| `scripts/setup-docgen-venv.sh` | new | Adapt from course-builder; point default engine to `~/github/jmjava/documentation-generator` |
| `scripts/docgen-engine.path.example` | new | Same one-line pattern as course-builder |
| `hints/project-context.md` | new | Project-wide `narration_from_source` + `env_file` for orchestrator |
| `hints/segment-01-*.md` | new | REASONS / three-part model |
| `hints/segment-02-*.md` | new | Install + daily workflow |
| `hints/segment-03-*.md` | optional | Guide RAG + dogfooding meta-narrative |
| Root or bundle `.gitignore` | new | Exclude regenerable audio/media; no binary commits in v1 |

## Strategic Direction

### Recommended bootstrap sequence

1. **Copy and adapt** `setup-docgen-venv.sh` + `docgen-engine.path.example` from course-builder (local reference — not in menke-4 corpus).
2. **`docgen init docs/demos --defaults`** from repo root venv — creates dirs + skeleton `docgen.yaml` + wrapper scripts.
3. **Add `hints/project-context.md`** with orchestrator-specific `narration_from_source.hints`:
   - Audience: framework contributors and adopters.
   - Product: SDLC-SPDD orchestrator (not a target app).
   - Emphasize: Planning + SPDD + SDLC hybrid; REASONS loop; no duplicate prose from `docs/`.
   - Segment 03: explain Guide menke layers and MCP during analysis (dogfood story).
4. **Add segment hint files** with YAML front matter (`docgen.segment.create: true`) — **do not hand-edit** `visual_map` for v1.
5. **Run `docgen yaml-generate --merge-defaults`** — produces merged `docgen.yaml`.
6. **Draft narration** — hand-author for v1 (reviewable, no API key required) OR `narration-generate` when `OPENAI_API_KEY` set.
7. **Smoke:** `docgen --config docgen.yaml lint` on segments 01–02 (and 03 if added).

### Segment plan (resolves open questions)

| ID | Stem | Primary sources (`repo_root`-relative) | Visual (v1) |
|----|------|----------------------------------------|-------------|
| 01 | `01-sdlc-spdd-intro` | `README.md`, `docs/ten-thousand-foot-view.md`, `docs/what-spdd-brings.md` | **Unmapped** (narration-only) |
| 02 | `02-install-and-workflow` | `docs/first-day-with-sdlc-spdd.md`, `docs/installing-into-your-project.md`, `docs/workflow.md` | **Unmapped** |
| 03 | `03-guide-rag-dogfood` (optional) | `docs/guide-rag-research-and-dogfooding.md`, `spdd/analysis/SPIKE-retrieval-reference-corpus.md` | **Unmapped** |

**v1 visual strategy:** narration-only segments. `yaml-generate` leaves `visual_map` empty until Manim exists — matches non-goal of deferring video CI. CHORE-002 can add one `still` or simple Manim scene.

### `narration_from_source.context.paths` (project-level)

Relative to `repo_root` (`../..` from bundle):

```yaml
context:
  paths:
    - README.md
    - docs/ten-thousand-foot-view.md
    - docs/workflow.md
    - docs/installing-into-your-project.md
    - docs/first-day-with-sdlc-spdd.md
    - docs/guide-rag-research-and-dogfooding.md
```

### `guide-rag-research-and-dogfooding.md` outline

Document for contributors (also narration source for segment 03):

1. **Why Guide** — curated RAG corpus for analysis without pasting external docs into prompts.
2. **menke profile layers** — menke (code) → menke-2 (SPDD/evals refs) → menke-3 (make-it-right) → menke-4 (docgen).
3. **Append-ingest** — one profile at a time on `:21337`; configs under `guide/scripts/user-config/`.
4. **MCP during `/sdlc-spdd-analysis`** — `docs_vectorSearch` / `docs_textSearch`; cite chunk URIs in analysis.
5. **Dogfood table** — SPDD on self, docgen on self, Guide on self, posture guard.
6. **What not to ship** — Guide YAML, Neo4j, MCP wiring stay local; targets get docs/scripts only.
7. **Link** — SPIKE-001 for architecture; this doc for operator how-to.

### Engine install decision

**Recommend editable local install** via `docgen-engine.path` defaulting to `~/github/jmjava/documentation-generator` in the example file. Matches active docgen development and menke-4 corpus. GitHub pip pin remains fallback when path file absent (same as course-builder).

## Risks and Gaps

| Risk / gap | Severity | Mitigation |
|------------|----------|------------|
| No root `.gitignore` in orchestrator | Medium | Add repo-level rules for `docs/demos/{audio,media,recordings}` + `scripts/docgen-engine.path`; or run `docgen pages` |
| menke-4 missing `scripts/` from course-builder | Low | Copy bootstrap scripts from local clone; note in plan |
| Duplicate prose if narration drifts from `docs/` | Medium | Single-source via `narration_from_source.context.paths`; review narrations in Git |
| Segment 03 references `spdd/` paths in narration context | Low | Paths are repo-relative; valid for orchestrator dogfood only — document that targets don't get `spdd/` |
| OpenAI key not required for scaffold AC | None | Hand-authored narration + `lint` smoke satisfies AC |
| Posture boundary | Low | No changes under `templates/`; run `check-posture-boundary.sh` in PR |
| docgen `yaml-generate` rewrites `docgen.yaml` | Low | Treat hints as source of truth; review Git diff after merge |

### AC coverage check

| Acceptance criterion | Analysis verdict |
|---------------------|------------------|
| `setup-docgen-venv.sh` + `docgen-engine.path.example` | Ready — copy/adapt from course-builder |
| `docs/demos/` scaffold | Ready — `init` + hints + `yaml-generate` |
| Two narration segments | Ready — sources mapped above |
| `guide-rag-research-and-dogfooding.md` | Ready — outline above |
| Optional segment 03 | Recommended — fulfills meta-documentation goal |
| `narration_from_source` → existing `docs/` | Ready — path list above |
| `docs/demos/README.md` | Ready — mirror course-builder bootstrap table |
| `.gitignore` bundle outputs | Ready — adopt course-builder patterns |

## Recommendation

**Proceed to `/sdlc-spdd-plan`.**

Analysis is complete. No blocking clarifications. Suggested plan operations: T01 venv scripts → T02 guide-rag doc → T03 `docgen init` → T04 hints + yaml-generate → T05 narration drafts → T06 gitignore + demos README → T07 `docgen lint` smoke.

Update canvas **Readiness** to `Ready For Plan` when plan is accepted.

Next command:

```
/sdlc-spdd-plan @spdd/analysis/CHORE-001-docgen-initial-documentation-analysis.md
```
