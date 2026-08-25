#!/usr/bin/env bash
# Resolve Python 3.12 for sdlc-engine (single version — no 3.10/3.11 fallbacks).
#
# Do not rely on a committed .python-version. pyenv/mise auto-switch to a
# missing 3.12 install, then `python3.12` and `.venv/bin/python` fail with
# "command not found" or zsh "permission denied". Prefer a real interpreter
# (Homebrew python@3.12, deadsnakes) over a broken shim.
#
# Usage (after setting ROOT or SDLC_ROOT):
#   source "${ROOT}/scripts/lib/python.sh"
#   resolve_engine_python && exec "$SDLC_PY" -m sdlc_engine ...

_python_is_usable_312() {
  local py="$1"
  local major minor
  [[ -n "${py}" ]] || return 1
  read -r major minor <<<"$("${py}" -c 'import sys; print(sys.version_info.major, sys.version_info.minor)' 2>/dev/null)" || return 1
  (( major == 3 && minor == 12 ))
}

_homebrew_python312() {
  command -v brew >/dev/null 2>&1 || return 1
  local prefix candidate
  prefix="$(brew --prefix python@3.12 2>/dev/null)" || return 1
  candidate="${prefix}/bin/python3.12"
  [[ -x "${candidate}" ]] || return 1
  _python_is_usable_312 "${candidate}" || return 1
  printf '%s' "${candidate}"
}

pick_bootstrap_python() {
  if [[ -n "${PYTHON:-}" ]]; then
    echo "${PYTHON}"
    return 0
  fi
  local brew_py
  if brew_py="$(_homebrew_python312)"; then
    echo "${brew_py}"
    return 0
  fi
  if command -v python3.12 >/dev/null 2>&1 && _python_is_usable_312 python3.12; then
    echo "python3.12"
    return 0
  fi
  echo ""
}

resolve_engine_python() {
  local root="${SDLC_ROOT:-${ROOT:-}}"
  local major minor

  if [[ -n "${PYTHON:-}" ]]; then
    SDLC_PY="${PYTHON}"
  elif [[ -n "${root}" && -x "${root}/.venv/bin/python" ]] && _python_is_usable_312 "${root}/.venv/bin/python"; then
    SDLC_PY="${root}/.venv/bin/python"
  else
    SDLC_PY="$(pick_bootstrap_python)"
  fi

  if [[ -z "${SDLC_PY}" ]]; then
    echo "error: Python 3.12 required — sudo apt install python3.12 python3.12-venv && ./scripts/setup-engine-venv.sh" >&2
    echo "  macOS: brew install python@3.12  (do not add a repo .python-version; it breaks pyenv shims)" >&2
    return 1
  fi

  read -r major minor <<<"$("${SDLC_PY}" -c 'import sys; print(sys.version_info.major, sys.version_info.minor)' 2>/dev/null)" || {
    echo "error: cannot run ${SDLC_PY}" >&2
    return 1
  }
  if (( major != 3 || minor != 12 )); then
    echo "error: ${SDLC_PY} is 3.${minor} — sdlc-engine requires Python 3.12 (./scripts/setup-engine-venv.sh)" >&2
    return 1
  fi
  export SDLC_PY
  return 0
}
