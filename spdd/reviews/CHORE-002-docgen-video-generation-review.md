# Review: CHORE-002-docgen-video-generation

## Result

Approved With Notes

## Summary

MVP operations **T01–T05** and **T08** are complete. The orchestrator now dogfoods the full
docgen video pipeline for segment **01**: Manim scenes for all three segments, TTS +
timestamps + compose + validate locally, a composed **`01-sdlc-spdd-intro.mp4`** (~93s,
drift 0.52s), course-builder-style `.gitignore` negation for recordings, PR **`docgen lint`**
CI, and updated operator docs. **T06** (dispatch render) and **T07** (Pages) are explicitly
deferred per architect scope. Safeguards respected — no `templates/` or target-install changes.

## Findings

### Requirements and operations

| Check | Verdict |
|-------|---------|
| T01 `dependencies.txt` + tooling docs | Met — `dependencies.txt`, `TOOLING.md`, `setup-docgen-venv.sh` hint |
| T02 Manim scaffold + visual hints + yaml-generate | Met — `scenes.py` + 3 classes; `visual_map` 01–03; lint PASS |
| T03 local pipeline smoke (seg 01 MP4) | Met — MP4 exists; seg 01 validate checks PASS |
| T04 git policy for recordings | Met — negation pattern; audio/timing ignored; MP4 addable |
| T05 CI docgen lint | Met — `.github/workflows/docgen-lint.yml`; local CI smoke PASS |
| T06 dispatch generate-all | Deferred (documented) |
| T07 GitHub Pages | Deferred (documented) |
| T08 docs + posture | Met — README, `project-context.md`, milestone updated; posture green |

### Acceptance criteria (MVP)

| AC | Verdict |
|----|---------|
| `dependencies.txt` + system deps docs | Met |
| `visual_map` for 01–03 (Manim) | Met |
| `animations/scenes.py` scaffold | Met |
| Local pipeline documented | Met — `TOOLING.md`, `README.md` |
| ≥1 composed MP4 | Met — `recordings/01-sdlc-spdd-intro.mp4` |
| `.gitignore` recordings policy | Met — no LFS (architect decision) |
| CI `docgen lint` on PR | Met |
| Optional dispatch CI / Pages | Deferred — acceptable |

### Safeguards and norms

- No changes under `templates/` or `setup-agent-prompts.sh`.
- `.env` gitignored; not committed.
- No committed `audio/`, `timing.json`, or `animations/media/`.
- Hints-driven `docgen.yaml`; `visual_map` from hints + discovery, not hand-edited.
- Orchestrator-only dev tooling scope maintained.

### Tests (re-run during review)

- `docgen lint` — PASS segments 01, 02, 03.
- `docgen validate` — segment **01** all checks PASS; 02/03 fail `recording_exists` only (MVP scope).
- `check-posture-boundary.sh` — OK (115 shipped surfaces).
- `git add -n docs/demos/recordings/01-sdlc-spdd-intro.mp4` — addable.

### Unrelated changes

None in implementation scope. CHORE-001 + CHORE-002 SPDD artifacts and planning files appear
in the same working tree (expected if not yet split into PRs).

## Required Changes

None blocking approval for **MVP scope**.

Before merge PR: ensure **`docs/demos/recordings/01-sdlc-spdd-intro.mp4`** is staged with
CHORE-002 implementation files (currently untracked along with the rest of the docgen bundle).

## Optional Improvements

1. **Requirement checkbox sync** — `requirements/milestones/CHORE-002-*.md` AC boxes still
   unchecked; align in `/sdlc-spdd-sync`.
2. **`docgen.yaml` `env_file`** — not merged from `hints/project-context.md` (docgen v0.2.0
   limitation); operators must `source ../../.env` per TOOLING. Consider manual `env_file:
   ../../.env` in yaml or upstream `docgen.project` merge.
3. **Segments 02–03 compose** — Manim wired but no recordings yet; stretch or follow-up chore.
4. **T06/T07** — dispatch render CI + Pages when secrets/settings ready.
5. **Canvas metadata** — header shows Complete / pending review; sync after merge.

## Test Gaps

- `docgen-lint.yml` not yet exercised on GitHub Actions (workflow file new; local smoke OK).
- No automated validate in CI (intentionally deferred — needs OpenAI + Manim deps).
- `validate` global exit may report FAIL for 02/03 `recording_exists` until those MP4s exist.

## Drift From Canvas

| Item | Severity | Note |
|------|----------|------|
| Seg 02/03 recordings absent | Low | MVP explicitly seg 01 only |
| T06/T07 deferred | None | Documented in canvas + README |
| MP4 not yet git-tracked | Low | Policy ready; include in PR |
| CLI `manim --segment` vs `--scene` | Low | TOOLING/README use correct `--scene ClassName` |

No implementation mismatch or safeguard violations.

## Recommended Next Command

```
/sdlc-spdd-sync @spdd/canvas/CHORE-002-docgen-video-generation.md
```

Then open a PR including the smoke MP4 and run **`docgen-lint`** workflow on the PR.
