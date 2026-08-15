# Vue3 ops console (`console-ui`)

Vite + Vue3 shell that talks to the existing Flask installer JSON API (`/api/*`).

## Tabs (Vue3 parity)

- **Dashboard** (default) → status / activity / suggestions (`/api/dashboard/*`)
- **Persistence** → status + save + ledger parity (`/api/persistence/*`)
- **Templates** → list/render/write ADF (`/api/templates/*`)
- **Install** → detect + run/verify (`/api/detect`, `/api/run`)
- **SQLite** → status + rebuild (`/api/sqlite/*`)
- **Rollback** → backups + restore (`/api/backups`, `/api/rollback`)
- **Guide** → config/probe/lifecycle (`/api/guide/*`)
- **Issues** → integrations save + link/sync (`/api/integrations/*`, `/api/issues/*`)
- **ADF** → viewer lifecycle + browse/init (`/api/adf/*`)

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
pytest -q engine/tests_e2e/test_vue3_console_playwright.py
```
