#!/usr/bin/env bash
# Bootstrap repo .venv for sdlc-engine (Python 3.12 only).
#
#   ./scripts/setup-engine-venv.sh              # dev + viewer
#   ./scripts/setup-engine-venv.sh --e2e        # + pytest-playwright
#
# Requires a *runnable* python3.12 (Homebrew python@3.12 or deadsnakes).
# A committed .python-version is not used: pyenv/mise shims fail when that
# version is not installed, and `.venv/bin/python` then looks like
# zsh "permission denied".
#
# Ubuntu 24.04+ / macOS (Homebrew):
#   sudo apt install python3.12 python3.12-venv   # or: brew install python@3.12
#
# Ubuntu 22.04 (Jammy — python3.12 not in default apt):
#   sudo add-apt-repository -y ppa:deadsnakes/ppa && sudo apt update
#   sudo apt install python3.12 python3.12-venv
#
#   ./scripts/setup-engine-venv.sh --e2e
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/python.sh
source "${ROOT}/scripts/lib/python.sh"

VENV="$ROOT/.venv"
BIN="$VENV/bin"
ENGINE="$ROOT/engine"
EXTRAS="dev,viewer"
FORCE_RECREATE="${FORCE_RECREATE:-0}"

for arg in "$@"; do
  case "$arg" in
    --e2e) EXTRAS="dev,viewer,viewer-e2e" ;;
    --help|-h)
      sed -n '1,12p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg (try --e2e)" >&2
      exit 2
      ;;
  esac
done

PY="$(pick_bootstrap_python)"
if [[ -z "$PY" ]]; then
  cat >&2 <<EOF
error: sdlc-engine requires Python 3.12

Ubuntu 22.04:
  sudo add-apt-repository -y ppa:deadsnakes/ppa && sudo apt update
  sudo apt install python3.12 python3.12-venv

Ubuntu 24.04+ / Debian trixie+:
  sudo apt install python3.12 python3.12-venv

macOS (Homebrew):
  brew install python@3.12
  export PATH="\$(brew --prefix python@3.12)/bin:\$PATH"

Then: $0 --e2e
EOF
  exit 1
fi

major="$("$PY" -c 'import sys; print(sys.version_info.major)')"
minor="$("$PY" -c 'import sys; print(sys.version_info.minor)')"
if (( major != 3 || minor != 12 )); then
  cat >&2 <<EOF
error: sdlc-engine requires Python 3.12 (found $($PY --version))
EOF
  exit 1
fi

need_recreate=0
if [[ ! -d "$VENV" ]]; then
  need_recreate=1
elif [[ -f "$VENV/pyvenv.cfg" ]]; then
  venv_py="$("$BIN/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")"
  if [[ "$venv_py" != "3.12" ]]; then
    echo "==> existing .venv is Python $venv_py; recreating with 3.12"
    need_recreate=1
  fi
fi

if [[ "$FORCE_RECREATE" == "1" ]]; then
  need_recreate=1
fi

if [[ "$need_recreate" == "1" ]]; then
  if [[ -d "$VENV" ]]; then
    rm -rf "$VENV"
  fi
  echo "==> creating $VENV with $PY"
  "$PY" -m venv "$VENV"
fi

echo "==> upgrading pip ($("$BIN/python" --version))"
"$BIN/pip" install -U pip wheel setuptools

echo "==> pip install -e '$ENGINE[$EXTRAS]'"
"$BIN/pip" install -e "$ENGINE[$EXTRAS]"

if [[ "$EXTRAS" == *viewer-e2e* ]]; then
  echo "==> playwright install chromium (for E2E)"
  "$BIN/python" -m playwright install chromium
fi

echo ""
echo "Ready. Activate with:"
echo "  source .venv/bin/activate"
echo "Or run CI locally:"
echo "  ./scripts/test-ci-local.sh"
