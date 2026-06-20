# Progress Log: CHORE-002-docgen-video-generation

## 2026-06-20

- Requirement drafted (CHORE-001 follow-up: actual video generation)
- `/sdlc-spdd-analysis` complete — MCP menke-4 + course-builder CI patterns indexed
- `/sdlc-spdd-plan` complete — REASONS canvas T01–T08 (MVP: T01–T05 + one MP4)
- `/sdlc-spdd-architect` complete — **Ready For Coding**
- Architect decisions: `SdlcSpddIntroScene` / `InstallWorkflowScene` / `GuideRagDogfoodScene`; MVP = seg 01 MP4 only; no LFS; course-builder `.gitignore` negation; T06/T07 deferred; CI lint `@main`
## 2026-06-20 (T08)

- T08 complete: `docs/demos/README.md` v2 scope; `project-context.md` updated; `milestone-1.md` CHORE-002 Complete (MVP)
- Posture guard green (115 files)
- MVP merge gate done (T01–T05, T08); T06/T07 deferred
## 2026-06-20 (operator steer)

- Generated recordings 02–03 locally; all three MP4s ready for Pages
- Added `docs/index.html` + `.github/workflows/pages.yml` (deploy only)
- T06 video-render CI cancelled; manual regen + git push workflow documented

## 2026-06-20 (T05)

- T05 complete: `.github/workflows/docgen-lint.yml`
- Triggers: PR + main push on `docs/demos/**`; Python 3.12; `docgen @ main`; no secrets
- Local CI smoke: fresh venv + lint PASS 01–03

## 2026-06-20 (T04)

- T04 complete: `.gitignore` course-builder negation pattern (`*.mp4` + `!docs/demos/recordings/*.mp4`)
- Added `animations/timing.json` ignore; removed blanket `recordings/` ignore
- Validation: MP4 addable via `git add -n`; audio/timing still ignored
- `docs/demos/recordings/01-sdlc-spdd-intro.mp4` ready to track (no LFS)

## 2026-06-20 (T03)

- T03 complete: segment 01 pipeline smoke (tts → timestamps → manim → compose → validate)
- Output: `recordings/01-sdlc-spdd-intro.mp4` (~1.9 MB, ~93s); drift 0.52s (max 2.75)
- Fixed ASCII in `scenes.py` docstrings for manim_scene_lint
- TOOLING.md: `.env` sourcing, correct CLI (`manim --scene`, `compose 01`)
- Regenerable artifacts local only (audio/, timing.json) — not committed per T03 scope

## 2026-06-20 (T02)

- T02 complete: `animations/scenes.py` (helpers + 3 scene classes)
- Visual + manim_scene hints on segment-01–03; `yaml-generate --merge-defaults`
- `visual_map` keys 01–03 type manim; `docgen lint` PASS 01–03; `--list-gaps` clean

## 2026-06-20 (T01)

- T01 complete: `docs/demos/dependencies.txt`, `docs/demos/TOOLING.md`
- Updated `scripts/setup-docgen-venv.sh` (Manim install hint + TOOLING link)
- Updated `docs/demos/README.md` (bootstrap row + TOOLING link)
- Validation: `pip install -r docs/demos/dependencies.txt`; `import manim` OK (0.19.1)
