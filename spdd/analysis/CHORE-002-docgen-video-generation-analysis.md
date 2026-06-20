# Analysis: CHORE-002-docgen-video-generation

## Metadata

- **Work ID:** CHORE-002-docgen-video-generation
- **Requirement:** `requirements/milestones/CHORE-002-docgen-video-generation.md`
- **Predecessor:** CHORE-001-docgen-initial-documentation (Complete, synced 2026-06-20)
- **Timestamp:** 2026-06-20T14:05:00Z
- **Research:** embabel-dev MCP (menke-4 on `:21337`) + local `course-builder/docs/demos/` + `documentation-generator` CLI

## Domain Keywords

- docgen video pipeline
- TTS / timestamps / Whisper
- Manim / visual_map / still compose
- generate-all / compose / validate / concat
- ffmpeg / system dependencies
- GitHub Actions / OPENAI_API_KEY
- GitHub Pages / index.html
- recordings commit policy / Git LFS
- scene-spec-generate / yaml-generate discovery
- dogfooding / operator tooling

## Code Areas

- `docs/demos/` — bundle root: add `dependencies.txt`, `animations/`, optional `TOOLING.md`, update README
- `docs/demos/docgen.yaml` — populate `visual_map`, `manim.scenes`, `manim_scene_generation.segments`
- `docs/demos/hints/segment-NN-*.md` — add `docgen.wiring.visual` (+ optional `manim_scene` hints)
- `.gitignore` / `.gitattributes` — shift from “ignore all recordings” to course-builder MP4 policy
- `.github/workflows/` — new `docgen-lint.yml`; optional `docgen-generate-demos.yml`, `pages.yml`
- `docs/index.html` — Pages landing (generated via `docgen pages` or hand-curated)
- `scripts/setup-docgen-venv.sh` — may need `docgen[manim]` install note or post-step `dependencies.txt`

## MCP Research Summary (menke-4)

| Query | Tool | Top hit | Relevance |
|-------|------|---------|-----------|
| `docgen generate-all tts manim compose validate` | vector | `cli.py` `generate_all` → `Pipeline.run` | Full pipeline order: TTS → Manim → compose → validate → concat → **pages** |
| `visual_map still manim_scene_generation` | vector | `yaml_generate.discover_visual_map` | `visual_map` auto-discovered from `animations/scenes.py` `*Scene` classes in file order; `still`/`mixed`/`image` types supported in compose |
| `scene-spec-generate manim_scene_generation` | vector | `cli.py` `scene-spec-generate` | LLM-assisted scene spec → `scene-compile` injects classes into `scenes.py` marker blocks |
| `generate-all.sh compose rebuild-after-audio` | vector | `init.py` wrapper scripts | CHORE-001 already has wrappers; pipeline-ready |

**Corpus strength:** menke-4 covers `documentation-generator/src` deeply. Course-builder **workflow YAML** is not ingested — copy patterns from local `course-builder/.github/workflows/docgen-generate-demos.yml` and `pages.yml` (verified on disk).

**Key docgen contract (MCP):**

1. `generate-all` = TTS → Manim → compose → validate → concat → pages (with `--skip-tts` / `--skip-manim` flags).
2. `yaml-generate --merge-defaults` discovers `visual_map` **only when** `animations/scenes.py` has `*Scene` classes; greenfield stays `{}` until scenes exist.
3. `rebuild-after-audio` skips TTS — useful after narration edits without re-billing TTS.
4. `pages` generates `index.html`, `pages.yml`, `.gitattributes`, `.gitignore` — **overwrites** curated workflows; course-builder restores `pages.yml` from HEAD post-render.

## Existing Concepts

### CHORE-001 deliverables (ready to extend)

| Artifact | State |
|----------|-------|
| `docs/demos/docgen.yaml` | Segments 01–03, `visual_map: {}`, TTS/compose/validation blocks from defaults |
| `docs/demos/narration/01–03*.md` | Hand-authored; `docgen lint` PASS |
| `docs/demos/hints/segment-01–03*.md` | Narration wiring only; **no** `docgen.wiring.visual` yet |
| Wrapper scripts | `generate-all.sh`, `compose.sh`, `validate.sh`, `rebuild-after-audio.sh` |
| `scripts/setup-docgen-venv.sh` | Base `docgen` install; **no** `[manim]` extra yet |
| Root `.gitignore` | Ignores **all** `docs/demos/recordings/` — blocks Pages publish |

### Course-builder reference pattern (local clone)

| Artifact | Pattern for CHORE-002 |
|----------|----------------------|
| `docs/demos/dependencies.txt` | `manim>=0.19.0` after venv bootstrap |
| `docs/demos/TOOLING.md` | System dep checklist + render sequence |
| `docs/demos/animations/scenes.py` | Hand-maintained helpers + `scene-spec-generate` injected scenes |
| `hints/segment-NN-*.md` | `docgen.wiring.visual: { type: manim, class: IntroScene }` |
| `.gitignore` | Ignore `audio/`, `animations/media/`, `timing.json`; **allow** `!docs/demos/recordings/*.mp4` |
| `docgen-generate-demos.yml` | `docgen[manim]` pip install, apt ffmpeg/Cairo/Pango/tesseract, `generate-all`, commit MP4s |
| `pages.yml` | Deploy `docs/` on main push; cache-bust video URLs with `GITHUB_SHA` |

### Orchestrator CI today

Eight workflows (posture, canvas, adapters, session-memory, etc.) — **no** docgen jobs. Adding `docgen lint` fits existing validate-* pattern without secrets.

## New Concepts

| Concept | Introduced by CHORE-002 |
|---------|-------------------------|
| Visual segment wiring | `visual_map` entries for 01–03 (Manim or `still`) |
| Animation scaffold | `docs/demos/animations/scenes.py` (+ optional `specs/`) |
| Manim pip extra | `pip install -r docs/demos/dependencies.txt` or `docgen[manim]` in CI |
| Regenerable vs shipped MP4 policy | Negation rules in `.gitignore`; optional Git LFS for MP4 |
| Render CI | PR lint job + optional dispatch render with `OPENAI_API_KEY` |
| Pages surface | `docs/index.html` + workflow (or artifact-only v2) |
| OpenAI cost gate | TTS + Whisper on every full `generate-all` — workflow_dispatch default |

## Strategic Direction

### Recommended phasing (canvas operations)

**Phase A — Visual wiring (no OpenAI):**

1. Choose visual strategy per segment (see trade-off below).
2. Add `docgen.wiring.visual` to segment hints; run `yaml-generate --merge-defaults`.
3. Add `dependencies.txt` + document system deps in `docs/demos/README.md` or `TOOLING.md`.

**Phase B — Local smoke (developer machine, `OPENAI_API_KEY`):**

4. `docgen tts --segment 01` (then 02, 03) or `docgen tts` for all.
5. `docgen timestamps` → manim (if applicable) → `compose` → `validate`.
6. Prove one MP4 in `recordings/`; iterate narration/hints if validate drift fails.

**Phase C — Automation (optional AC):**

7. PR workflow: `docgen lint` only (matches CHORE-001 gate, zero secret cost).
8. `workflow_dispatch` generate workflow mirroring course-builder (240 min timeout, artifact upload).
9. Git policy + `docgen pages` + Pages workflow — or defer Pages to CHORE-003 if scope pressure.

### Visual strategy trade-off

| Approach | Pros | Cons | Fit for 3 intro segments |
|----------|------|------|--------------------------|
| **`still` images** | No Manim install; fast CI; `--skip-manim` works | Less polished; need static assets per segment | Good MVP if time-boxed |
| **Minimal Manim title cards** | Matches docgen discovery; one scene class per segment | Cairo/Pango deps; scene-spec LLM cost; render time | **Recommended** — course-builder parity at small scale |
| **Full diagram Manim** | Highest quality | High authoring cost (course-builder has 15 complex scenes) | Overkill for v2 |

**Recommendation:** Minimal Manim — three title/diagram scenes via `scene-spec-generate` using hints derived from existing narration topics (SPDD loop, install workflow, Guide RAG). Reuse course-builder `scenes.py` helper patterns (`_TimedScene`, palette constants, `timing.json` pacing).

### Git / artifact policy

CHORE-001 `.gitignore` blocks all `recordings/`. Publishing requires course-builder negation pattern:

- Keep ignoring `audio/`, `animations/media/`, `timing.json`, `.docgen-state.json`
- Allow `!docs/demos/recordings/*.mp4`
- Consider Git LFS for MP4 (course-builder uses LFS) — optional for a 3-segment bundle (~tens of MB)

### CI split (cost vs coverage)

| Job | Trigger | Secret | Purpose |
|-----|---------|--------|---------|
| `docgen-lint` | PR + `docs/demos/**` paths | None | Regression on narration quality |
| `docgen-generate-demos` | `workflow_dispatch` (+ optional main) | `OPENAI_API_KEY` | Full TTS + Manim + compose |

Do **not** run `generate-all` on every PR (course-builder skips draft PRs for render workflows too). Align with orchestrator cost posture.

### Pages

`docgen pages` scaffolds `docs/index.html` and a stock `pages.yml`. Course-builder hand-curates HTML and restores workflow after generate. For orchestrator:

- Start with `docgen pages --force` then edit titles/durations for segments 01–03
- Add `pages.yml` with `docs/**` path filter
- Requires repo Settings → Pages → GitHub Actions (document in README)

### Safeguards (unchanged)

- Docgen remains orchestrator dev tooling — not copied to targets by `setup-agent-prompts.sh`
- No `templates/` changes
- Posture guard must stay green after new workflows/docs

## Risks and Gaps

| Risk | Severity | Mitigation |
|------|----------|------------|
| **OPENAI_API_KEY missing in CI** | High for render | Require secret check step (course-builder pattern); lint job needs no key |
| **Manim system deps on dev laptops** | Medium | Document apt/brew packages; CI uses apt block from course-builder |
| **`.gitignore` blocks MP4 commit** | High for Pages | Explicit AC; negation rules + review in plan |
| **`docgen pages` overwrites workflows** | Medium | `git checkout HEAD -- .github/workflows/pages.yml` post-generate (course-builder) |
| **Freeze guard / A-V drift** | Medium | `validate` + `max_drift_sec: 2.75` already in yaml; `--retry-manim` flag |
| **Manim authoring time** | Medium | Use `scene-spec-generate` not hand-coded 1000-line scenes |
| **Secret leakage in logs** | Low | Never echo API key; use GitHub secrets only |
| **menke-4 missing workflow YAML** | Low | Local course-builder clone is canonical for CI copy |

### AC coverage gaps to resolve in plan

1. **Manim vs still** — requirement allows either; plan must pick one default (recommend minimal Manim).
2. **Pages optional** — clarify minimum: artifact upload on dispatch may satisfy “video proof” without public Pages.
3. **MP4 commit vs artifact-only** — course-builder commits to main; orchestrator may prefer artifact-only for v2 to avoid LFS setup.

## Recommendation

**Proceed to canvas** (`/sdlc-spdd-plan`). No blocking clarifications required.

Suggested canvas scope (~6–8 operations):

- T01 — `dependencies.txt` + tooling docs + venv Manim note
- T02 — Visual hints + `animations/scenes.py` scaffold + `yaml-generate`
- T03 — Local pipeline proof (one segment MP4 minimum)
- T04 — Git policy for recordings (+ optional LFS)
- T05 — CI `docgen lint` workflow
- T06 — Optional CI `generate-all` + artifact upload
- T07 — Optional Pages (`index.html` + workflow)
- T08 — Update `docs/demos/README.md`, `milestone-1.md`, posture verify

Defer full 3-segment Manim polish and public Pages if schedule tight — ship T01–T05 + one MP4 as MVP.

## Next Command

```
/sdlc-spdd-plan @spdd/analysis/CHORE-002-docgen-video-generation-analysis.md
```

After plan acceptance, index analysis:

```
./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id CHORE-002-docgen-video-generation
```
