# Vue3 ops console (`console-ui`)

Vite + Vue3 shell that talks to the existing Flask installer JSON API (`/api/*`).

## First slice

- **Persistence** tab → `POST /api/persistence/status`
- **Templates** tab → `POST /api/templates` + `/api/templates/render`
- Other tabs stubbed until ported from `engine/src/sdlc_engine/installer/pages.py`

## Dev

```bash
# terminal 1 — Flask BFF (repo root / engine)
python -m sdlc_engine console --target . --no-browser --port 5051

# terminal 2 — Vue3
cd console-ui
npm install
npm run dev
# open http://127.0.0.1:5173/ (proxies /api → :5051)
```

Smoke against a running console:

```bash
CONSOLE_API=http://127.0.0.1:5051 CONSOLE_TARGET=/path/to/project npm run smoke
```

## Build

```bash
npm run build   # → console-ui/dist
```

Serve the build from Flask (same origin as `/api/*`):

```bash
SDLC_VUE_CONSOLE_DIST=$PWD/dist python -m sdlc_engine console --target .. --no-browser --port 5051
# open http://127.0.0.1:5051/
```

## Playwright

From the repo root (builds `dist` if needed):

```bash
SDLC_CONSOLE_E2E=1 pytest -q engine/tests/test_vue3_console_playwright.py -m console_e2e
```
