#!/usr/bin/env bash
# Thin entry point for the SDLC-SPDD engine (one engine: Python sdlc-engine).
# Installed to sdlc-spdd/scripts/sdlc.sh in target projects; lives at
# scripts/sdlc.sh in the orchestrator repo.
#
# Every verb is dispatched to `python -m sdlc_engine`. There is no shell
# workflow implementation and no SDLC_ENGINE switch (REF-003).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$(basename "$(dirname "${SCRIPT_DIR}")")" == "sdlc-spdd" ]]; then
  # Installed target or dogfood home: <root>/sdlc-spdd/scripts/sdlc.sh
  ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
else
  # Orchestrator checkout: <root>/scripts/sdlc.sh
  ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi

# Script-derived ROOT finds the .venv + engine source. --target/--root only
# changes the project the engine operates on.
PROJECT_ROOT="${ROOT}"
_forward=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target|--root)
      if [[ -z "${2:-}" || ! -d "${2:-}" ]]; then
        echo "sdlc: $1 requires an existing directory" >&2
        exit 2
      fi
      PROJECT_ROOT="$(cd "$2" && pwd)"
      shift 2
      ;;
    --target=*|--root=*)
      _p="${1#*=}"
      if [[ ! -d "${_p}" ]]; then
        echo "sdlc: ${1%%=*} is not a directory: ${_p}" >&2
        exit 2
      fi
      PROJECT_ROOT="$(cd "${_p}" && pwd)"
      shift
      ;;
    *)
      _forward+=("$1")
      shift
      ;;
  esac
done
if ((${#_forward[@]} > 0)); then
  set -- "${_forward[@]}"
else
  set --
fi

export SDLC_ROOT="${ROOT}"

if [[ -f "${SCRIPT_DIR}/lib/python.sh" ]]; then
  # shellcheck source=scripts/lib/python.sh
  source "${SCRIPT_DIR}/lib/python.sh"
elif [[ -f "${ROOT}/scripts/lib/python.sh" ]]; then
  # shellcheck source=scripts/lib/python.sh
  source "${ROOT}/scripts/lib/python.sh"
else
  echo "sdlc: scripts/lib/python.sh not found next to $0" >&2
  exit 1
fi

if [[ -n "${SDLC_ENGINE:-}" || -n "${SDLC_GATE_ENGINE:-}" ]]; then
  echo "sdlc: SDLC_ENGINE / SDLC_GATE_ENGINE were removed; the Python engine is the only engine (REF-003)" >&2
  exit 2
fi

resolve_engine_python || exit 1

_pypath=""
if [[ -d "${ROOT}/engine/src/sdlc_engine" ]]; then
  _pypath="${ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}"
fi

if ! PYTHONPATH="${_pypath:-${PYTHONPATH:-}}" "${SDLC_PY}" -c 'import sdlc_engine' 2>/dev/null; then
  echo "sdlc: sdlc_engine is not importable by ${SDLC_PY}" >&2
  echo "Install with: ./scripts/setup-engine-venv.sh  # Python 3.12 (or: pip install -e ./engine)" >&2
  exit 1
fi

cmd="${1:-next}"
if [[ $# -gt 0 ]]; then
  shift
fi

# Hyphen aliases kept for chat commands and older docs.
args=()
case "${cmd}" in
  help|-h|--help) args=("--help") ;;
  local-*) args=("local" "${cmd#local-}" "$@") ;;
  db-*) args=("db" "${cmd#db-}" "$@") ;;
  work-init-from-adf|init-from-adf) args=("work" "init-from-adf" "$@") ;;
  guide-query) args=("context" "guide-query" "$@") ;;
  *) args=("${cmd}" "$@") ;;
esac

if [[ -n "${_pypath}" ]]; then
  PYTHONPATH="${_pypath}" exec "${SDLC_PY}" -m sdlc_engine --root "${PROJECT_ROOT}" "${args[@]}"
fi
exec "${SDLC_PY}" -m sdlc_engine --root "${PROJECT_ROOT}" "${args[@]}"
