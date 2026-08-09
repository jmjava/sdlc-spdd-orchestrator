# ADF template library

Reusable **header / body / footer** markdown parts assembled by named **combos**,
then rendered to Jira Cloud ADF via `sdlc_engine.adf_templates`.

## Layout

```text
parts/     # markdown fragments with {{variable}} placeholders
combos/    # JSON manifests listing part ids + work-type hints
schemas/   # JSON Schema for combo manifests + rendered ADF docs
```

## Render

```bash
# from orchestrator / consumer root
python -m sdlc_engine template list
python -m sdlc_engine template render --work-id FEAT-001-shared-script-library --combo feature
python -m sdlc_engine template render --work-id SPIKE-089-guide-projection --combo spike -o adf/SPIKE-089.adf.json
```

Ops console (Vue3 + Flask API):

- `POST /api/templates` — list combos
- `POST /api/templates/render` — render for a Work ID

See [docs/adf-template-library-and-vue3-console.md](../../docs/adf-template-library-and-vue3-console.md).
