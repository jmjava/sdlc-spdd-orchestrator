# Demo bundle (`docs/demos`)

This folder holds **`docgen.yaml`**, narration scripts, Manim visuals, hints, and composed
recordings for narrated documentation about SDLC-SPDD Orchestrator. The CLI is the
**`docgen`** package from [**documentation-generator**](https://github.com/jmjava/documentation-generator).

This bundle is **orchestrator dev tooling only** — it does not install into target
projects via `setup-agent-prompts.sh`. See
[DICE projection runbook](../dice-projection-runbook.md) and
[MCP Guide for agents](../mcp-guide-for-agents.md) for the optional Guide stack.

**Current scope:** three segments with **declarative Manim scene specs**
(`animations/specs/*.scene.yaml` → compiled `scenes.py`), composed MP4s under
`recordings/` (gitignored on `main`), GitHub **Pages** via
**`scripts/deploy-docs-pages-local.sh`**. Video regeneration is **manual** locally — no CI render workflow.
Default regen: **`./generate-all.sh --retry-manim`** (auto scene-spec on first run; retime thereafter).

**CI:** `docgen-lint.yml` runs narration lint on PRs only (no TTS/Manim/ffmpeg in CI).

## Segments

| ID | Narration | Visual | Topic |
|----|-----------|--------|--------|
| 01 | `narration/01-sdlc-spdd-intro.md` | `SdlcSpddIntroScene` | SDLC-SPDD intro and REASONS loop | `recordings/01-sdlc-spdd-intro.mp4` |
| 02 | `narration/02-install-and-workflow.md` | `InstallWorkflowScene` | Install into a target + workflow steps 1–6 | `recordings/02-install-and-workflow.mp4` |
| 03 | `narration/03-guide-rag-dogfood.md` | `GuideRagDogfoodScene` | Guide RAG research and dogfooding | `recordings/03-guide-rag-dogfood.mp4` |

Recordings are **not committed on `main`** — regenerate locally, then publish with
**`./scripts/deploy-docs-pages-local.sh`** (see **System deps and render sequence** below).

## Bootstrap (repository root)

| Step | Command |
|------|---------|
| Install `docgen` into **`.venv`** | `./scripts/setup-docgen-venv.sh` |
| Optional: local editable engine | `DOCGEN_SRC` or **`scripts/docgen-engine.path`** (see **`scripts/docgen-engine.path.example`**) |
| Manim extra (video pipeline) | `.venv/bin/pip install -r docs/demos/dependencies.txt` — see **System deps** below |
| OpenAI key (TTS / timestamps) | **`../../.env`** at repo root (gitignored) |

Then:

```bash
source .venv/bin/activate
cd docs/demos
docgen --config docgen.yaml lint
```

## Maintainer workflow

After editing hint files under **`hints/`** or scene specs under **`animations/specs/`**
(prefer specs — do not hand-edit generated scene classes):

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

Full render sequence (segment 01 example):

```bash
cd docs/demos
set -a && source ../../.env && set +a

docgen --config docgen.yaml tts --segment 01
docgen --config docgen.yaml timestamps
docgen --config docgen.yaml manim --scene SdlcSpddIntroScene
docgen --config docgen.yaml compose 01
docgen --config docgen.yaml validate
```

Or `./generate-all.sh --retry-manim` for all segments.

## System deps and render sequence

Install **`docgen`** from repo root: `./scripts/setup-docgen-venv.sh` (optional local engine via `scripts/docgen-engine.path`).

Manim extra: `.venv/bin/pip install -r docs/demos/dependencies.txt`

Ubuntu/Debian system packages: `ffmpeg`, `libcairo2-dev`, `libpango1.0-dev`, `pkg-config`, `python3-dev`, `fonts-liberation`, optional `tesseract-ocr`.

OpenAI key for TTS: `../../.env` at repo root (gitignored).

Default regen: `./generate-all.sh --retry-manim` (declarative specs under `animations/specs/*.scene.yaml`).

Manual Pages publish: `./scripts/deploy-docs-pages-local.sh` from repo root after local MP4 regen (recordings gitignored on `main`).

## Related docs

| Doc | Role |
|-----|------|
| [documentation-generator](https://github.com/jmjava/documentation-generator) | CLI reference |
| [DICE projection runbook](../dice-projection-runbook.md) | Run Guide + Neo4j locally |
| [MCP Guide for agents](../mcp-guide-for-agents.md) | CLI and MCP retrieval for agents |
| [docs/README.md](../README.md) | Full documentation hub |
