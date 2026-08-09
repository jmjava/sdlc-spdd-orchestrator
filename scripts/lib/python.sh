#!/usr/bin/env bash
# Resolve Python 3.12 for sdlc-engine (single version — no 3.10/3.11 fallbacks).
#
# Usage (after setting ROOT or SDLC_ROOT):
#   source "${ROOT}/scripts/lib/python.sh"
#   resolve_engine_python && exec "$SDLC_PY" -m sdlc_engine ...

resolve_engine_python() {
  local root="${SDLC_ROOT:-${ROOT:-}}"
  local major minor

  if [[ -n "${PYTHON:-}" ]]; then
    SDLC_PY="${PYTHON}"
  elif [[ -n "${root}" && -x "${root}/.venv/bin/python" ]]; then
    SDLC_PY="${root}/.venv/bin/python"
  elif command -v python3.12 >/dev/null 2>&1; then
    SDLC_PY="python3.12"
  else
    SDLC_PY=""
  fi

  if [[ -z "${SDLC_PY}" ]]; then
    echo "error: Python 3.12 required — sudo apt install python3.12 python3.12-venv && ./scripts/setup-engine-venv.sh" >&2
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

pick_bootstrap_python() {
  if [[ -n "${PYTHON:-}" ]]; then
    echo "${PYTHON}"
    return 0
  fi
  if command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12"
    return 0
  fi
  echo ""
}
