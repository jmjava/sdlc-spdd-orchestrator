# ADF template library + Vue3 ops console

**Branch:** `cursor/adf-templates-vue3-console-decf` (off `v2.0.0a6` / `main`)  
**Status:** planning / spike start  
**Supersedes:** Flask-templated ops console + ad-hoc ADF drafts for the planning→Jira path

## Problem

Planning iterations produce ideas in requirements / canvas / analysis, but turning
those into consistent Jira ADF documents is manual. The ops console is still a
Python/Flask multi-page string UI — hard to extend for template composition.

## Goals

1. **Template library** — reusable ADF (and markdown source) templates composed of
   **header / body / footer** parts, with named combinations for common work types
   (feature, spike, bug, chore, milestone sync, …).
2. **Planning → ADF transform** — take artifacts produced through planning mode
   (requirement, analysis, canvas excerpts, decisions) and render a templated Jira
   ADF document at the end of the process (validate schema; optional push stays
   explicit / never auto).
3. **Vue3 ops console** — replace the Flask HTML/JS console with a Vue3 app that
   keeps the existing installer/persistence/Guide/ADF APIs (or thin BFF), including
   template management UI.

## Non-goals (this branch)

- Auto-push to Jira on save/commit
- Upstream PRs to `embabel/guide`
- Full consumer redesign of slash commands

## Existing building blocks

| Piece | Where |
|-------|--------|
| Markdown → ADF / wiki | `engine` issue sync (`issues draft --format adf`) |
| ADF Viewer (Flask) | `sdlc_engine.viewer` + console ADF tab |
| Research notes | `docs/research/jira-adf-and-requirements-sync.md` |
| Requirements templates | `requirements/` CHORE/feature templates |
| Persistence tab (new) | Flask console — port into Vue3 |

## Proposed shape

```text
templates/
  adf/
    parts/           # header_*, body_*, footer_* fragments
    combos/          # named combinations (JSON or YAML manifests)
    schemas/         # JSON Schema for rendered ADF + combo manifests
engine/…/templates/  # load + render + validate
console-ui/          # Vue3 app (Vite) — Templates + existing console tabs
```

Render pipeline (sketch):

1. Collect planning inputs for a Work ID (requirement, analysis, progress excerpt, …).
2. Select combo (manual or by work-type heuristic).
3. Bind variables → assemble parts → emit ADF JSON (+ pretty markdown preview).
4. Validate against schema; write under `adf/` or show in viewer; push only on explicit action.

## Vue3 migration approach

1. Keep Flask (or FastAPI) as JSON API (`/api/*`) initially.
2. Stand up `console-ui/` Vue3 + Vite; proxy to API in dev.
3. Port tabs: Install, Persistence, SQLite, Rollback, Guide, ADF, **Templates**.
4. Retire Flask `pages.py` HTML once parity + e2e smoke exist.

## Acceptance (first slice)

- [ ] Combo manifest format + 2–3 stock templates (feature / spike / bug)
- [ ] CLI or engine API: `template render --work-id … --combo … → ADF`
- [ ] Schema validation test
- [ ] Vue3 shell loads against live `/api/persistence/status` (smoke)
- [ ] Docs + draft PR off this branch

## Related open work

- #103 PR Playback / report — complementary (decision report); keep separate unless
  templates become the shared rendering layer
- #89 Guide dual-read — still open on `jmjava/guide` (not this branch)
