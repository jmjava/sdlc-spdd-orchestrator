# Requirement: CHORE-002-docgen-video-generation

## Summary

Extend the CHORE-001 `docs/demos/` bundle from narration-only scaffold to a **working video
pipeline**: TTS audio, segment visuals (Manim or `still`), ffmpeg compose, validate, and
optional `generate-all` automation. Add contributor tooling (`dependencies.txt`, animation
scaffold) and optional GitHub Actions (lint on PR; full render on `workflow_dispatch` or
main). Optionally publish composed MP4s via GitHub Pages.

## Source

- CHORE-001 follow-up (`spdd/sync/CHORE-001-docgen-initial-documentation-sync.md`)
- User request (2026-06-20): confirm CHORE-002 generates actual videos (TTS/Manim/ffmpeg)
- Reference consumer: `courseforge/course-builder/docs/demos/` + `.github/workflows/docgen-generate-demos.yml`

## Motivation

CHORE-001 shipped narration scripts, hints, and `docgen lint` smoke gates. Contributors can
read the prose canon but cannot preview narrated video without manual pipeline steps and
system deps. This chore closes the loop so the orchestrator dogfoods the **full** docgen
pipeline — the same toolchain course-builder uses — for its three intro segments.

## Preconditions

- CHORE-001 complete: `docs/demos/` bundle, `setup-docgen-venv.sh`, root `.gitignore`
- Local `documentation-generator` clone or git pin (menke-4 corpus)
- For TTS/render: `OPENAI_API_KEY` in repo-root `.env` (not committed)

## Acceptance Criteria

- [ ] `docs/demos/dependencies.txt` documents Manim extra; `TOOLING.md` or README section
      lists system deps (ffmpeg, Cairo/Pango, optional tesseract).
- [ ] Segment visuals exist for segments **01–03** via `visual_map` in `docgen.yaml`
      (Manim scenes **or** `still` images — approach chosen in analysis/plan).
- [ ] `animations/scenes.py` scaffold (if Manim) with helpers + scene classes discoverable
      by `yaml-generate`; or `still` assets under `docs/demos/` if not using Manim.
- [ ] Local pipeline documented: `docgen tts` → timestamps → manim (if applicable) →
      `compose` → `validate` (or `./generate-all.sh` wrapper).
- [ ] At least one segment produces a composed MP4 under `docs/demos/recordings/` locally
      (smoke proof; may use `--skip-manim` only if `still` visuals are used).
- [ ] `.gitignore` / `.gitattributes` policy updated for **committed** `recordings/*.mp4`
      (course-builder pattern: ignore intermediates, allow final MP4s; LFS optional).
- [ ] CI workflow runs `docgen lint` on PRs when `docs/demos/**` changes (no OpenAI secret).
- [ ] Optional: CI workflow `workflow_dispatch` (and/or main path filter) runs
      `docgen generate-all` with `OPENAI_API_KEY` secret; uploads artifact or commits MP4s.
- [ ] Optional: `docs/index.html` + GitHub Pages workflow for demo playback (or document
      why deferred).

## Non-Goals

- No install of docgen bundle into target projects via `setup-agent-prompts.sh`.
- No 15-segment course-builder parity — three segments only.
- No org-site `docs/rendered/` aggregation (course-builder `docgen-render.yml` pattern).
- No committed `.venv/`, `audio/*.mp3`, `timing.json`, or `animations/media/` intermediates.
- No change to shipped `templates/` or posture-boundary content.

## Research / RAG

**Profile:** `menke-4` (docgen `src/` + course-builder `docs/` text paths).

**MCP:** embabel-dev `docs_vectorSearch` / `docs_textSearch` during analysis.

**Starter queries:**

- `docgen generate-all pipeline tts manim compose validate pages`
- `visual_map still manim scene-spec-generate yaml-generate`
- `docgen-generate-demos workflow OPENAI_API_KEY ffmpeg manim`

**Related artifacts:** CHORE-001 analysis/canvas/sync; course-builder `docs/demos/TOOLING.md`.

## Next Step

Analysis and plan complete. Architect hardened — **Ready For Coding**.

Run `/sdlc-spdd-code` for **T01** (one operation per session):

    /sdlc-spdd-code @spdd/canvas/CHORE-002-docgen-video-generation.md T01

MVP merge gate: T01 → T02 → T03 → T04 → T05 → T08. T06/T07 deferred.
