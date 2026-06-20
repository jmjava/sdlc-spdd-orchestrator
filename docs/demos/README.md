# Demo bundle (`docs/demos`)

This folder holds **`docgen.yaml`**, narration scripts, Manim visuals, hints, and composed
recordings for narrated documentation about SDLC-SPDD Orchestrator. The CLI is the
**`docgen`** package from [**documentation-generator**](https://github.com/jmjava/documentation-generator).

This bundle is **orchestrator dev tooling only** — it does not install into target
projects via `setup-agent-prompts.sh`. See
[Guide RAG research and dogfooding](../guide-rag-research-and-dogfooding.md) for why we
dogfood docgen here.

**Current scope:** three segments with Manim visuals, composed MP4s under
`recordings/` (gitignored on `main`), GitHub **Pages** via
**`scripts/deploy-docs-pages-local.sh`**. Video regeneration is **manual** locally — no CI render workflow.

**CI:** `docgen-lint.yml` runs narration lint on PRs only (no TTS/Manim/ffmpeg in CI).

## Segments

| ID | Narration | Visual | Topic |
|----|-----------|--------|--------|
| 01 | `narration/01-sdlc-spdd-intro.md` | `SdlcSpddIntroScene` | SDLC-SPDD intro and REASONS loop | `recordings/01-sdlc-spdd-intro.mp4` |
| 02 | `narration/02-install-and-workflow.md` | `InstallWorkflowScene` | Install into a target + workflow steps 1–6 | `recordings/02-install-and-workflow.mp4` |
| 03 | `narration/03-guide-rag-dogfood.md` | `GuideRagDogfoodScene` | Guide RAG research and dogfooding | `recordings/03-guide-rag-dogfood.mp4` |

Recordings are **not committed on `main`** — regenerate locally, then publish with
**`./scripts/deploy-docs-pages-local.sh`** (see **`TOOLING.md`**).

## Bootstrap (repository root)

| Step | Command |
|------|---------|
| Install `docgen` into **`.venv`** | `./scripts/setup-docgen-venv.sh` |
| Optional: local editable engine | `DOCGEN_SRC` or **`scripts/docgen-engine.path`** (see **`scripts/docgen-engine.path.example`**) |
| Manim extra (video pipeline) | `.venv/bin/pip install -r docs/demos/dependencies.txt` — see **`TOOLING.md`** |
| OpenAI key (TTS / timestamps) | **`../../.env`** at repo root (gitignored) |

Then:

```bash
source .venv/bin/activate
cd docs/demos
docgen --config docgen.yaml lint
```

## Maintainer workflow

After editing hint files under **`hints/`** or **`animations/scenes.py`**:

```bash
cd docs/demos
docgen --config docgen.yaml yaml-generate --merge-defaults
docgen --config docgen.yaml lint
```

See **`hints/README.md`** for the hint file layout. **`hints/project-context.md`** documents
project-wide narration intent; per-segment wiring lives in **`hints/segment-NN-*.md`**.

Prose canon for narration content lives in **`docs/`** (not duplicated here). Segment
`narration_from_source.context.paths` in **`docgen.yaml`** point at those sources.

## Video pipeline

Full render sequence (segment 01 example) — see **`TOOLING.md`** for system deps and details:

```bash
cd docs/demos
set -a && source ../../.env && set +a

docgen --config docgen.yaml tts --segment 01
docgen --config docgen.yaml timestamps
docgen --config docgen.yaml manim --scene SdlcSpddIntroScene
docgen --config docgen.yaml compose 01
docgen --config docgen.yaml validate
```

Wrapper scripts: **`generate-all.sh`**, **`compose.sh`**, **`validate.sh`**, **`rebuild-after-audio.sh`**.

**Git policy:** all regenerable outputs gitignored (`audio/`, `animations/media/`, `timing.json`, **`recordings/*.mp4`**). Only source (narration, hints, scenes) commits on `main`.

**CI:** `.github/workflows/docgen-lint.yml` — narration lint only. **No CI video render.**

**Pages:** `./scripts/deploy-docs-pages-local.sh` pushes `docs/` + local MP4s to **`gh-pages`**. Boundary enforced by **`scripts/verify-docgen-dev-boundary.sh`**.

## Related docs

| Doc | Role |
|-----|------|
| [TOOLING.md](TOOLING.md) | System deps, render sequence, Manim install |
| [documentation-generator](https://github.com/jmjava/documentation-generator) | CLI reference |
| [Guide RAG research and dogfooding](../guide-rag-research-and-dogfooding.md) | Research backend + dogfood loop |
| [docs/README.md](../README.md) | Full documentation hub |
