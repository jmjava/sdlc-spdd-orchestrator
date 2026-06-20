#!/usr/bin/env bash
# Install docgen into sdlc-spdd-orchestrator .venv (orchestrator dev tooling only).
#
# Resolution order for the engine source:
#   1) DOCGEN_SRC environment variable (absolute path), or
#   2) scripts/docgen-engine.path — copy from docgen-engine.path.example; one line, your machine only, or
#   3) pip install from GitHub (no local clone).
#
# Onboarding: docs/demos/README.md (after CHORE-001 bundle scaffold).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
BIN="$VENV/bin"
PYTHON="${PYTHON:-python3}"
ENGINE_PATH_FILE="$ROOT/scripts/docgen-engine.path"

echo "==> docgen venv (ROOT=$ROOT)"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "error: $PYTHON not found" >&2
  exit 1
fi

if [[ ! -d "$VENV" ]]; then
  echo "==> creating $VENV"
  "$PYTHON" -m venv "$VENV"
fi

"$BIN/pip" install -U pip wheel

DOCGEN_SRC="${DOCGEN_SRC-}"
if [[ -z "$DOCGEN_SRC" && -f "$ENGINE_PATH_FILE" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" || "$line" == \#* ]] && continue
    DOCGEN_SRC="$line"
    break
  done <"$ENGINE_PATH_FILE"
fi

if [[ -n "$DOCGEN_SRC" ]]; then
  DOCGEN_SRC="$(cd "$DOCGEN_SRC" && pwd)"
  if [[ ! -f "$DOCGEN_SRC/pyproject.toml" ]] || ! grep -q 'name = "docgen"' "$DOCGEN_SRC/pyproject.toml" 2>/dev/null; then
    echo "error: engine root $DOCGEN_SRC is not a documentation-generator (docgen) pyproject" >&2
    echo "Set DOCGEN_SRC or fix scripts/docgen-engine.path (see docgen-engine.path.example)" >&2
    exit 1
  fi
  echo "==> pip install -e $DOCGEN_SRC"
  "$BIN/pip" install -e "$DOCGEN_SRC"
else
  echo "==> pip install from GitHub (for editable: export DOCGEN_SRC or add scripts/docgen-engine.path)"
  "$BIN/pip" install "git+https://github.com/jmjava/documentation-generator.git"
fi

echo ""
echo "OK: docgen at $BIN/docgen"
"$BIN/docgen" --help >/dev/null
"$BIN/python" -m docgen --help >/dev/null
echo ""
echo "Optional Manim extra (video pipeline — CHORE-002):"
echo "  $BIN/pip install -r $ROOT/docs/demos/dependencies.txt"
echo ""
echo "Activate and run from the demo bundle:"
echo "  source $VENV/bin/activate"
echo "  export PATH=\"$BIN:\$PATH\""
echo "  cd $ROOT/docs/demos && docgen --config docgen.yaml lint"
echo "See docs/demos/TOOLING.md for system deps and render sequence."
