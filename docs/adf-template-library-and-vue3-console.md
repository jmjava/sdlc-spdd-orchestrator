# ADF template library + Vue3 ops console

**Branch:** `cursor/adf-templates-vue3-console-decf` (off `v2.0.0a6` / `main`)  
**Status:** first slice implemented  
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
| Template library | `templates/adf/` + `sdlc_engine.adf_templates` |
| Vue3 shell | `console-ui/` (Vite) |

## Shape

```text
templates/
  adf/
    parts/           # header_*, body_*, footer_* fragments
    combos/          # named combinations (JSON manifests)
    schemas/         # JSON Schema for rendered ADF + combo manifests
engine/…/adf_templates.py  # load + render + validate
console-ui/          # Vue3 app (Vite) — Templates + Persistence (+ stubs)
```

Render pipeline:

1. Collect planning inputs for a Work ID (requirement, analysis, progress excerpt, …).
2. Select combo (manual or by work-type heuristic).
3. Bind `{{variables}}` → assemble parts → emit ADF JSON (+ markdown preview).
4. Validate against schema; optional write under `adf/`; push only on explicit action.

## CLI / API

```bash
python -m sdlc_engine template list --json
python -m sdlc_engine template validate
python -m sdlc_engine template render --work-id FEAT-001-shared-script-library --combo feature
python -m sdlc_engine template render --work-id SPIKE-089-x --combo spike -o adf/SPIKE-089.adf.json
```

Flask BFF (ops console):

- `POST /api/templates` — list combos
- `POST /api/templates/render` — `{ target, work_id, combo?, type?, write?, output? }`

## Vue3 migration approach

1. Keep Flask as JSON API (`/api/*`) initially. ✅
2. Stand up `console-ui/` Vue3 + Vite; proxy to API in dev. ✅
3. Port tabs: Install, Persistence, SQLite, Rollback, Guide, ADF, **Templates**.
   - Done: Persistence + Templates
   - Stubbed: Install, SQLite, Rollback, Guide, ADF
4. Retire Flask `pages.py` HTML once parity + e2e smoke exist. ✅ (`sdlc.sh console` serves Vue3; stub if dist is missing)

Dev: see [`console-ui/README.md`](../console-ui/README.md).

## Acceptance (first slice)

- [x] Combo manifest format + 2–3 stock templates (feature / spike / bug)
- [x] CLI or engine API: `template render --work-id … --combo … → ADF`
- [x] Schema validation test
- [x] Vue3 shell loads against live `/api/persistence/status` (smoke)
- [x] Docs + draft PR off this branch
- [x] Playwright GUI coverage for full Vue3 console (all tabs + Persistence save + Templates write)

## Playwright (Vue3)

Build once, then run opt-in e2e (same marker as the legacy Flask console suite):

```bash
cd console-ui && npm ci && npm run build && cd ..
pip install -e './engine[dev,viewer-e2e]'
playwright install chromium
SDLC_CONSOLE_E2E=1 pytest -q engine/tests/test_vue3_console_playwright.py -m console_e2e
```

Flask can serve the Vite build when `SDLC_VUE_CONSOLE_DIST=console-ui/dist` (or
`create_app(..., vue_dist=...)`). The suite builds/serves that path automatically.

## Next slices

- Default `console` to Vue dist when present (retire Flask `pages.py` HTML) ✅
- Chore / milestone-sync combos
- Explicit “open viewer after write” affordance (still no auto Jira push)

## Vue3 tab parity (this branch)

| Tab | Vue3 | Playwright |
|-----|------|------------|
| Dashboard (status + suggestions + configure) | ✅ | ✅ |
| Persistence (load + save + parity) | ✅ | ✅ |
| Templates (feature/spike/bug + write) | ✅ | ✅ |
| Install | ✅ | ✅ |
| SQLite | ✅ | ✅ |
| Rollback | ✅ | ✅ list + dry-run restore |
| Guide | ✅ | ✅ stubbed probe + config save + dual-env defaults; **live** via `guide_live` |
| Issues (integrations + link/sync dry-run) | ✅ | ✅ Jira tracker select + link/sync |
| ADF viewer + init-from-ADF | ✅ | ✅ stubbed lifecycle; **live** via `adf_viewer_live` |

### Live dual-repo gates (the former “no” gaps)

```bash
# Needs sibling ../guide + Neo4j Bolt (:7687). Starts Guide JVM (slow first time).
SDLC_CONSOLE_E2E=1 SDLC_GUIDE_STACK_LIVE=1 \
  pytest -q engine/tests/test_vue3_console_live_playwright.py -m guide_live \
  --run-console-e2e --run-guide-live

# Real ADF viewer process (port 5050 free).
SDLC_CONSOLE_E2E=1 SDLC_ADF_VIEWER_LIVE=1 \
  pytest -q engine/tests/test_vue3_console_live_playwright.py -m adf_viewer_live \
  --run-console-e2e --run-adf-viewer-live
```

Also wired into `.github/workflows/test-guide-stack-experimental.yml`.

## Related open work

- #103 PR Playback / report — complementary (decision report); keep separate unless
  templates become the shared rendering layer
- #89 Guide projection contract — still open (not this branch)
