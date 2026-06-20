# Demo pipeline tooling (`docs/demos`)

This directory holds the **SDLC-SPDD Orchestrator** narrated demo bundle: **`docgen.yaml`**,
narration scripts, Manim visuals, and composed recordings. The CLI comes from
[**documentation-generator**](https://github.com/jmjava/documentation-generator) (`docgen`).

This bundle is **orchestrator dev tooling only** — it does not install into target projects
via `setup-agent-prompts.sh`.

## Install `docgen` (project `.venv`)

From the **sdlc-spdd-orchestrator** repository root:

```bash
./scripts/setup-docgen-venv.sh
```

**Where the package comes from** (first match):

1. **`DOCGEN_SRC`** — absolute path to a local **`documentation-generator`** checkout (editable install).
2. **`scripts/docgen-engine.path`** — copy **`scripts/docgen-engine.path.example`** → **`docgen-engine.path`**, one line: that absolute path (gitignored).
3. Otherwise **`pip install`** from **`https://github.com/jmjava/documentation-generator.git`**.

Use **`./.venv/bin/docgen`**, **`source .venv/bin/activate`**, or **`python -m docgen`** from that venv.

**Manim extra (required for video pipeline):** after **`setup-docgen-venv.sh`**:

```bash
.venv/bin/pip install -r docs/demos/dependencies.txt
```

Verify: `python -c "import manim"`.

**Secrets (`OPENAI_API_KEY`):** add to **`../../.env`** at the repo root (gitignored). Load before pipeline commands:

```bash
set -a && source ../../.env && set +a
```

**`docgen`** can also read **`env_file`** from **`docgen.yaml`** when set. To force keys from the file to override an already-exported shell value, set **`DOCGEN_ENV_OVERRIDES=1`**.

## Segment 01 smoke (MVP proof)

From **`docs/demos/`** after venv + Manim deps + **`.env`**:

```bash
ROOT=$(git rev-parse --show-toplevel)
export PATH="$ROOT/.venv/bin:$PATH"
cd "$ROOT/docs/demos"
set -a && source ../../.env && set +a

docgen --config docgen.yaml tts --segment 01
docgen --config docgen.yaml timestamps
docgen --config docgen.yaml manim --scene SdlcSpddIntroScene
docgen --config docgen.yaml compose 01
docgen --config docgen.yaml validate
```

Output: **`audio/01-sdlc-spdd-intro.mp3`**, **`animations/timing.json`**, **`recordings/01-sdlc-spdd-intro.mp4`**
(gitignored until T04 policy update). Segment 01 should PASS **`av_drift`**, **`freeze_ratio`**, and **`narration_lint`**.

## Typical render sequence

Run from **`docs/demos/`** (required cwd — lint and config discovery expect the bundle directory):

```bash
ROOT=$(git rev-parse --show-toplevel)
export PATH="$ROOT/.venv/bin:$PATH"
cd "$ROOT/docs/demos"
set -a && source ../../.env && set +a

docgen --config docgen.yaml lint
docgen --config docgen.yaml tts --segment 01
docgen --config docgen.yaml timestamps
docgen --config docgen.yaml manim --scene SdlcSpddIntroScene
docgen --config docgen.yaml compose 01
docgen --config docgen.yaml validate
```

For all segments, repeat with `--segment 02` / `InstallWorkflowScene`, `--segment 03` /
`GuideRagDogfoodScene`, or use **`./generate-all.sh`** locally.

Adjust flags and skips per **`docgen --help`** and **`docgen.yaml`**.

## Manual publish to GitHub Pages

There is **no CI workflow for video generation**. Recordings stay **gitignored on `main`**.

After regenerating locally:

1. Commit source changes only (`narration/`, `hints/`, `scenes.py`, `docs/index.html` if needed).
2. Run **`./scripts/deploy-docs-pages-local.sh`** from the repo root — copies local **`recordings/*.mp4`** into a staging tree and force-pushes **`gh-pages`** (MP4s never land on **`main`**).
3. One-time repo setup: **Settings → Pages → Deploy from branch → `gh-pages` / root**.

Narration-only changes can merge via PR; **`docgen-lint.yml`** runs lint without OpenAI.

## Dependencies (checklist)

| Tool | Role | Install |
|------|------|---------|
| **Python `.venv`** | `docgen` CLI | `./scripts/setup-docgen-venv.sh` |
| **Manim** | Segment visuals | `pip install -r docs/demos/dependencies.txt` |
| **ffmpeg** | Compose / concat | `apt install ffmpeg` / `brew install ffmpeg` |
| **Cairo / Pango** | Manim text rendering | `apt install libcairo2-dev libpango1.0-dev pkg-config python3-dev` |
| **tesseract-ocr** | Optional OCR in **`docgen validate`** | `apt install tesseract-ocr` |
| **OpenAI API key** | TTS + Whisper timestamps | **`../../.env`** — not committed |

### Ubuntu / Debian (CI and local)

```bash
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
  ffmpeg \
  libcairo2-dev \
  libpango1.0-dev \
  pkg-config \
  python3-dev \
  fonts-liberation \
  tesseract-ocr
```

## Engine bugs and features

Report or follow **`docgen`** changes in
[**documentation-generator**](https://github.com/jmjava/documentation-generator). This repo
carries **`docgen.yaml`**, hints, narration, and Manim scenes only.
