# Hints for docgen (`docs/demos/hints`)

Committed Markdown inputs merged into **`docgen.yaml`** by **`docgen yaml-generate`**.
See [documentation-generator](https://github.com/jmjava/documentation-generator)
**README** / **AGENTS.md** for CLI rules.

This bundle is **narration-only v1** (no Manim `visual_map`). Per-segment hints declare
segments and `narration_from_source` wiring only.

| File | Role |
|------|------|
| **`project-context.md`** | **`docgen.project`**: `env_file`, project-wide `narration_from_source` hints + context paths. |
| **`segment-NN-*.md`** | Per-segment `docgen.segment` + `docgen.wiring.narration` hints and context. |

After changing any hint file:

```bash
cd docs/demos
docgen --config docgen.yaml yaml-generate --merge-defaults
```
