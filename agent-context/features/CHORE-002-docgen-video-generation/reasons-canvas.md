# REASONS Canvas: CHORE-002-docgen-video-generation - Docgen video pipeline (TTS + Manim + compose)

## Metadata

- Work ID: CHORE-002-docgen-video-generation
- Work Type: Chore (documentation tooling)
- Status: Complete
- Readiness: Reviewed — Approved With Notes
- Created: 2026-06-20
- Updated: 2026-06-20 (T08 MVP)
- Owner:
- Target Project: sdlc-spdd-orchestrator (self / dogfood)
- Stack: Python (`docgen`, Manim), Bash (wrappers, CI), YAML/Markdown (bundle), GitHub Actions
- Source System: CHORE-001 follow-up + user request (actual video generation)
- Analysis: `spdd/analysis/CHORE-002-docgen-video-generation-analysis.md`
- Predecessor: CHORE-001-docgen-initial-documentation (Complete)
- Roadmap: ROADMAP.md (make it right — operator documentation)
- Milestone: milestone-1.md (parallel track — does not block FEAT-001)
- Delivery stage: make it right (documentation clarity / dogfood)
- Related PR:

## R - Requirements

### User Goal

Generate **actual narrated demo videos** (MP4) for the three CHORE-001 segments using the
full docgen pipeline — TTS, Manim visuals, ffmpeg compose, and validate — not just
narration scripts that pass `docgen lint`.

### Business / Product Goal

Close the dogfood loop: the orchestrator uses the same `documentation-generator` pipeline
as course-builder. Contributors can preview narrated explainers locally and (optionally)
via CI artifacts or GitHub Pages.

### Acceptance Criteria

- [ ] `docs/demos/dependencies.txt` + system-deps docs (`TOOLING.md` or README section).
- [ ] `visual_map` populated for segments **01–03** (minimal Manim title/diagram scenes).
- [ ] `animations/scenes.py` scaffold with helpers + three `*Scene` classes discoverable by `yaml-generate`.
- [ ] Local pipeline documented and proven: ≥1 composed MP4 under `docs/demos/recordings/`.
- [ ] `.gitignore` updated: ignore intermediates; **allow** `docs/demos/recordings/*.mp4` (LFS optional).
- [ ] CI `docgen lint` on PR when `docs/demos/**` changes (no OpenAI secret).
- [ ] Optional: `workflow_dispatch` `generate-all` CI with artifact upload.
- [ ] Optional: `docs/index.html` + GitHub Pages workflow.

### Non-Goals

- No docgen bundle install into target projects via `setup-agent-prompts.sh`.
- No 15-segment course-builder parity.
- No `docs/rendered/` org-site aggregation (`docgen-render.yml` pattern).
- No committed `audio/*.mp3`, `timing.json`, `animations/media/`, or `.venv/`.
- No `templates/` or posture-boundary changes.

### Assumptions

- CHORE-001 bundle is complete and `docgen lint` green for segments 01–03.
- Local `documentation-generator` clone at `~/github/jmjava/documentation-generator`.
- `OPENAI_API_KEY` in repo-root `.env` for local TTS/timestamps (not committed).
- **Visual strategy:** minimal Manim title/diagram scenes (not `still` images, not full course-builder complexity).
- **CI render policy:** `workflow_dispatch` only for `generate-all` (no per-PR OpenAI spend).
- **MP4 publish policy:** commit final `recordings/*.mp4` allowed; Git LFS optional (skip LFS in MVP if repo size acceptable).
- **Pages:** optional (T07); artifact upload on dispatch satisfies “video proof” without public Pages.

### Open Questions

- **Resolved (analysis):** Manim over `still` — matches docgen discovery and course-builder pattern.
- **Resolved (analysis):** MVP = T01–T05 + one MP4; T06–T07 deferred past MVP merge gate.
- **Resolved (architect):** Scene classes — `SdlcSpddIntroScene`, `InstallWorkflowScene`, `GuideRagDogfoodScene` (file order in `scenes.py` must match segment 01→03).
- **Resolved (architect):** MVP commits **one** smoke MP4 (`01-sdlc-spdd-intro.mp4`); all three scene classes required in T02; segments 02–03 compose is stretch within T03.
- **Resolved (architect):** **No Git LFS** in MVP — plain git for ≤3 short MP4s; add LFS in follow-up if size grows.
- **Resolved (architect):** CI `DOCGEN_REF: main` for lint; generate workflow (T06) uses same pin when implemented.

## E - Entities

### Application Components

| Component | Role |
|-----------|------|
| `docs/demos/` | Existing bundle — extend with animations, deps, recordings policy |
| `docs/demos/animations/scenes.py` | Manim helpers + segment scene classes |
| `docs/demos/dependencies.txt` | `manim>=0.19.0` pip extra |
| `docs/demos/TOOLING.md` | System deps + render sequence (or expanded README section) |
| Wrapper scripts | Existing `generate-all.sh`, `compose.sh`, etc. — document usage |
| `.github/workflows/docgen-lint.yml` | PR lint gate (new) |
| `.github/workflows/docgen-generate-demos.yml` | Optional dispatch render (new) |
| `.github/workflows/pages.yml` | Optional Pages deploy (new) |
| `docs/index.html` | Optional demo landing page |
| Reference: `course-builder/docs/demos/` | Manim scaffold, git policy, CI workflows |

### Data / Persistence

| Artifact | Role |
|----------|------|
| `docgen.yaml` | `visual_map`, `manim.scenes`, `manim_scene_generation.segments` — from hints + yaml-generate |
| `hints/segment-NN-*.md` | Add `docgen.wiring.visual` + `manim_scene` hints per segment |
| `audio/*.mp3` | TTS output — gitignored |
| `animations/timing.json` | Whisper timestamps — gitignored (add explicit rule; missing in CHORE-001 `.gitignore`) |
| `animations/media/` | Manim intermediates — gitignored |
| `recordings/*.mp4` | Composed segment videos — **committed** (negation in `.gitignore`; no LFS in MVP) |
| `.env` | Repo root; `OPENAI_API_KEY` for local TTS — never committed |

### Files Likely Affected

- `docs/demos/dependencies.txt`, `TOOLING.md` (new)
- `docs/demos/animations/scenes.py` (+ optional `specs/`)
- `docs/demos/hints/segment-01–03*.md`
- `docs/demos/docgen.yaml` (via `yaml-generate`)
- `docs/demos/README.md`, `hints/project-context.md`
- `.gitignore` (rewrite docgen section — course-builder negation pattern, no LFS)
- `.github/workflows/docgen-lint.yml`, `docgen-generate-demos.yml`, `pages.yml` (optional)
- `docs/index.html` (optional)
- `scripts/setup-docgen-venv.sh` (Manim install note)
- `milestone-1.md`, `ROADMAP.md` (linked work)

## A - Approach

### Proposed Approach

1. Add `dependencies.txt` and document system deps (ffmpeg, Cairo/Pango, tesseract optional).
2. Scaffold `animations/scenes.py` with course-builder-style helpers (`_TimedScene`, palette, `timing.json` loaders).
3. Extend segment hints with `docgen.wiring.visual` (`type: manim`) and `manim_scene` hints aligned to narration topics.
4. Use `docgen scene-spec-generate --segment NN` (with `OPENAI_API_KEY`) to draft scene specs, then `scene-compile` — or hand-minimal title-card scenes if API unavailable.
5. Run `docgen yaml-generate --merge-defaults` — verify `visual_map` discovers three scene classes.
6. Local smoke: `docgen tts --segment 01` → `timestamps` → `manim --segment 01` → `compose --segment 01` → `validate --segment 01` (or `./generate-all.sh` for all).
7. Update `.gitignore` negation rules for `recordings/*.mp4`.
8. Add PR CI for `docgen lint` only.
9. Optional: dispatch render workflow + Pages.

### Alternatives Considered

| Alternative | Why not default |
|-------------|-----------------|
| `still` images + `--skip-manim` | Faster but less polished; skips Manim dogfood |
| Full diagram Manim (course-builder parity) | 15-segment complexity; overkill for three intros |
| Commit MP4s only via CI bot | Adds LFS/dispatch complexity; local smoke MP4 sufficient for MVP proof |
| `generate-all` on every PR | OpenAI cost; course-builder also avoids draft-PR renders |

### Trade-Offs

- Minimal Manim scenes ship faster than polished diagrams but need Cairo/Pango on dev machines.
- Artifact-only CI (T06) avoids LFS setup; committing MP4s enables Pages without dispatch re-run.
- `docgen pages` overwrites stock workflow — restore curated `pages.yml` from HEAD post-generate.

### Risks

| Risk | Mitigation |
|------|------------|
| Missing `OPENAI_API_KEY` | Lint CI needs none; document `.env`; CI render checks secret |
| Manim deps on laptops | `TOOLING.md` apt/brew block; CI uses course-builder apt packages |
| A/V drift / freeze guard | `validate` + `max_drift_sec: 2.75`; `--retry-manim` on generate-all |
| `.gitignore` blocks MP4 | T04 explicit negation before first MP4 commit |
| `pages` overwrites workflows | `git checkout HEAD -- .github/workflows/pages.yml` after generate |
| Scene authoring time | `scene-spec-generate` + small title cards, not 1000-line scenes |

## S - Structure

### Files To Add

```
docs/demos/
  dependencies.txt                 # manim>=0.19.0
  TOOLING.md                       # system deps + render sequence
  animations/
    scenes.py                      # helpers + SdlcSpddIntroScene, InstallWorkflowScene, GuideRagDogfoodScene
    specs/                         # optional scene-spec-generate output
  recordings/
    01-sdlc-spdd-intro.mp4         # smoke proof (≥1); all three if time permits
.github/workflows/
  docgen-lint.yml                  # PR lint
  docgen-generate-demos.yml        # optional workflow_dispatch
  pages.yml                        # optional Pages
docs/index.html                    # deferred (T07 — post-MVP)
```

### `.gitignore` target (architect — replace docgen block)

```
# docgen bundle — regenerable intermediates (orchestrator dev only)
docs/demos/audio/
docs/demos/animations/media/
docs/demos/animations/timing.json
docs/demos/animations/__pycache__/
docs/demos/media/
docs/demos/.docgen-state.json
# recordings/*.mp4 committed (negation below)

# Block accidental media; allow final demo MP4s only
*.mp3
*.mp4
!docs/demos/recordings/*.mp4
```

Remove blanket `docs/demos/recordings/` directory ignore from CHORE-001.

### Files To Modify

```
.gitignore                         # allow !docs/demos/recordings/*.mp4; keep ignoring audio/timing/media
docs/demos/hints/segment-01–03*.md # add visual + manim_scene wiring
docs/demos/hints/project-context.md # remove "narration-only v1" note
docs/demos/docgen.yaml             # yaml-generate output — review diff
docs/demos/README.md               # v2 pipeline: deps, tts, manim, compose, validate, generate-all
scripts/setup-docgen-venv.sh       # post-step: pip install -r docs/demos/dependencies.txt
milestone-1.md                     # linked work row
```

### Scene class contract (architect — locked)

| Segment | Class name | Scene focus |
|---------|------------|-------------|
| 01 | `SdlcSpddIntroScene` | Title + three-part diagram + REASONS acronym |
| 02 | `InstallWorkflowScene` | Install path: clone → setup-agent-prompts → verify → first session |
| 03 | `GuideRagDogfoodScene` | menke layers + MCP research + dogfood table |

Classes appear in `scenes.py` in segment order. Helpers (`_TimedScene`, palette, `_load_timing`) are underscore-prefixed and excluded from `visual_map` discovery.

### Hint visual wiring (per segment)

```yaml
docgen:
  wiring:
    visual:
      type: manim
      class: SdlcSpddIntroScene   # per segment: InstallWorkflowScene, GuideRagDogfoodScene
    manim_scene:
      hints:
        - "Title card: SDLC-SPDD Orchestrator — three-part framework + REASONS loop diagram."
        - "Use timing.json pacing; one reveal per mobject; stay inside safe content width."
```

### Test Structure

- No new unit tests.
- Gates: `docgen lint` (CI + local); `docgen validate` after local compose; `check-posture-boundary.sh`.

## O - Operations

### T01 - Manim deps + tooling docs

- Status: Complete
- Description: Add `docs/demos/dependencies.txt` (`manim>=0.19.0`). Add `TOOLING.md` (or README section) with system deps checklist (ffmpeg, Cairo/Pango, tesseract) and render sequence mirroring course-builder. Note in `setup-docgen-venv.sh` that Manim extra installs via `pip install -r docs/demos/dependencies.txt` after bootstrap.
- Files: `docs/demos/dependencies.txt`, `docs/demos/TOOLING.md`, `scripts/setup-docgen-venv.sh`, `docs/demos/README.md` (deps pointer)
- Tests: `pip install -r docs/demos/dependencies.txt` in activated venv
- Validation: `python -c "import manim"` succeeds
- Depends on: CHORE-001 complete

### T02 - Animation scaffold + visual hints + yaml-generate

- Status: Complete
- Description: Create `animations/scenes.py` with hand-maintained header (palette, `_TimedScene`, `_load_timing`, safe layout helpers — copy patterns from course-builder, orchestrator palette). Add three scene classes in order: `SdlcSpddIntroScene`, `InstallWorkflowScene`, `GuideRagDogfoodScene`. Prefer `docgen scene-spec-generate --segment NN` + `scene-compile` when `OPENAI_API_KEY` available; otherwise hand-write minimal title-card scenes (~60–100 lines each). Add `docgen.wiring.visual` + `manim_scene` to `hints/segment-01–03*.md`. Run `yaml-generate --merge-defaults`; verify `visual_map` has three manim entries.
- Files: `docs/demos/animations/scenes.py`, `docs/demos/animations/specs/` (if generated), `docs/demos/hints/segment-*.md`, `docs/demos/docgen.yaml`
- Tests: `docgen yaml-generate --list-gaps` — no gaps; `docgen lint` still PASS
- Validation: `visual_map` keys `01`, `02`, `03` with `type: manim` and correct class names; `manim.scenes` synced; do not hand-edit `visual_map`
- Depends on: T01

### T03 - Local pipeline smoke (segment 01 MP4 — MVP gate)

- Status: Complete
- Description: From `docs/demos/` with `OPENAI_API_KEY` in `../../.env`: `docgen tts --segment 01` → `timestamps` → `manim --segment 01` → `compose --segment 01` → `validate --segment 01`. Record commands in `TOOLING.md`. **MVP:** segment 01 MP4 only. Stretch: segments 02–03 or `./generate-all.sh` (do not block merge on 02–03).
- Files: `docs/demos/recordings/01-sdlc-spdd-intro.mp4` (local until T04), `docs/demos/TOOLING.md`
- Tests: `docgen validate --segment 01` exit 0; MP4 exists
- Validation: Drift within `max_drift_sec: 2.75`; no `audio/` or `timing.json` staged
- Depends on: T02

### T04 - Git policy for recordings

- Status: Complete
- Description: Replace CHORE-001 docgen `.gitignore` block with architect negation pattern (see Structure). Add `animations/timing.json` ignore. **No LFS** in MVP. Apply policy **before** `git add` of smoke MP4. Commit `01-sdlc-spdd-intro.mp4` only for MVP PR.
- Files: `.gitignore`, `docs/demos/recordings/01-sdlc-spdd-intro.mp4`
- Tests: `git check-ignore -v docs/demos/recordings/01-sdlc-spdd-intro.mp4` — must NOT be ignored; `git check-ignore -v docs/demos/audio/foo.mp3` — ignored
- Validation: `git status` shows one MP4 trackable; intermediates ignored
- Depends on: T03

### T05 - CI docgen lint workflow

- Status: Complete
- Description: Add `.github/workflows/docgen-lint.yml`: PR + push path filter `docs/demos/**`; Python 3.12; `pip install "docgen @ git+https://github.com/jmjava/documentation-generator.git@main"` (no Manim extra needed for lint); `working-directory: docs/demos`; `docgen lint`. No `OPENAI_API_KEY`.
- Files: `.github/workflows/docgen-lint.yml`
- Tests: Workflow green on PR touching demos
- Validation: Lint passes segments 01–03 in CI
- Depends on: T02 (parallelizable with T03 after T02)

### T06 - CI generate-all (workflow_dispatch) — **Deferred post-MVP**

- Status: Deferred
- Description: Add `.github/workflows/docgen-generate-demos.yml` mirroring course-builder when operator configures `OPENAI_API_KEY` secret. `workflow_dispatch` only; artifact upload; no auto-commit. Out of MVP merge gate.
- Files: `.github/workflows/docgen-generate-demos.yml`
- Depends on: T04, T05

### T07 - GitHub Pages — **Deferred post-MVP**

- Status: Deferred
- Description: `docgen pages --force`; curate `docs/index.html`; add `pages.yml`; restore curated workflow after generate. Requires repo Pages settings. Out of MVP merge gate — follow-up or CHORE-003.
- Files: `docs/index.html`, `.github/workflows/pages.yml`
- Depends on: T04

### T08 - Docs, milestone, posture verify (MVP)

- Status: Complete
- Description: Update `docs/demos/README.md` (v2 pipeline, MVP scope, T06/T07 deferred). Update `hints/project-context.md` — remove "narration-only v1" bullets. Update `milestone-1.md` status. Run `check-posture-boundary.sh` from repo root.
- Files: `docs/demos/README.md`, `docs/demos/hints/project-context.md`, `milestone-1.md`
- Tests: `check-posture-boundary.sh`
- Validation: Posture guard green; links resolve
- Depends on: T05 (minimum)

## N - Norms

### General

- Hints remain source of truth — re-run `yaml-generate` after hint or `scenes.py` changes.
- Do not hand-edit `visual_map` or `manim.scenes` in `docgen.yaml`.
- Run `docgen` from `docs/demos/` (or pass `--config docgen.yaml`) — repo-root cwd fails lint config load (CHORE-001 lesson).
- `scenes.py` header is hand-maintained; `scene-compile` injects only between marker blocks.
- Track `animations/specs/*.scene.yaml` when using `scene-spec-generate`; gitignore only `media/` and `timing.json`.
- Docgen bundle stays orchestrator dev tooling — not in `setup-agent-prompts.sh`.
- Stage: **make it right** (operator documentation / dogfood).
- One canvas operation per coding session.

### Testing

- **MVP merge gate:** T01 → T02 → T03 → T04 → T05 → T08.
- `docgen lint` on every PR touching `docs/demos/**` (T05).
- `docgen validate --segment 01` locally before T04 commit (evidence in progress log).
- `check-posture-boundary.sh` from repo root before merge (T08).
- T06/T07 out of MVP — separate session after secret/Pages setup.

## S - Safeguards

- Do not install docgen bundle into target projects.
- Do not modify `templates/` or shipped adapter surfaces.
- Do not commit `audio/`, `animations/timing.json`, `animations/media/`, `.venv/`, or `docgen-engine.path`.
- Do not run `tts` or `generate-all` in PR CI except T06 dispatch workflow (deferred).
- Do not add `.gitattributes` LFS in MVP without explicit follow-up chore.
- Do not run `generate-all` on every PR (cost control).
- Do not echo `OPENAI_API_KEY` in CI logs.
- Do not let implementation drift without `/sdlc-spdd-sync`.
- Restore curated `pages.yml` after `docgen pages` / `generate-all` if overwritten.

## Architecture Notes

- **Builds on CHORE-001:** narration, hints, wrappers, and lint gates exist; CHORE-001 left `animations/` empty and `recordings/` fully gitignored — CHORE-002 fills both gaps.
- **Minimal Manim:** three title/diagram scenes — exercises discovery, TTS sync, compose without course-builder-scale authoring.
- **Scene authoring path:** try `scene-spec-generate` + `scene-compile` per segment; fallback to hand-minimal scenes if API unavailable (do not block T02 on OpenAI).
- **MVP proof:** one composed MP4 (`01-sdlc-spdd-intro.mp4`) proves pipeline; all three `*Scene` classes still required for AC/visual_map.
- **Git policy shift:** replace directory-level `docs/demos/recordings/` ignore with global `*.mp4` + `!docs/demos/recordings/*.mp4` (course-builder pattern, minus `docs/rendered/`). Add explicit `animations/timing.json` ignore.
- **No LFS in MVP:** three short intros ≪ 50 MB; plain git commit acceptable; LFS deferred to avoid onboarding friction.
- **CI split:** lint (`docgen @ main`, no Manim, no secret) on every PR; full render (T06) deferred until `OPENAI_API_KEY` repo secret exists.
- **CI pin:** `DOCGEN_REF: main` for lint workflow — matches course-builder generate; local dev uses editable clone via `docgen-engine.path`.
- **Sequencing:** T01→T02→T03→T04 linear; T05 parallel after T02; T08 after T05; T06/T07 post-MVP.
- **cwd discipline:** all bundle commands from `docs/demos/` (CHORE-001 sync note).
- **Quality gates (MVP):** `docgen lint` (CI) + `docgen validate --segment 01` (local) + posture guard + `git check-ignore` verification.
- **Readiness rationale:** open questions resolved; reference implementation on disk (course-builder); operations small and ordered; CHORE-001 predecessor complete. **Ready For Coding.**

### Architect decisions (2026-06-20)

| Decision | Choice |
|----------|--------|
| Visual strategy | Minimal Manim (3 scene classes) |
| MVP MP4 | Segment 01 only in first PR |
| LFS | No — plain git |
| CI lint pin | `documentation-generator@main` |
| T06/T07 | Deferred post-MVP |
| `.gitignore` | Course-builder negation pattern (no `docs/rendered/`) |

## Review Checklist

- [x] Requirements satisfied (MVP scope)
- [x] Entities updated correctly
- [x] Approach followed or synced
- [x] Structure followed or synced
- [x] Operations completed (T01–T05, T08; T06/T07 deferred)
- [x] Norms followed
- [x] Safeguards respected
- [x] `docgen lint` green
- [x] `docgen validate` green (segment 01)
- [x] Posture guard green
- [x] Documentation updated

## Sync Notes

Plan derived from analysis (MCP menke-4). Architect hardened: scene class names locked;
MVP = one MP4 (seg 01); no LFS; `.gitignore` negation pattern; T06/T07 deferred;
`DOCGEN_REF: main` for lint CI; `timing.json` explicit ignore.

## Final Status

- Status: Complete (MVP T01–T05, T08)
- Completed Date: 2026-06-20
- PR:
- Follow-Up Tasks: `/sdlc-spdd-review`; T06 dispatch CI; T07 Pages; compose segments 02–03
