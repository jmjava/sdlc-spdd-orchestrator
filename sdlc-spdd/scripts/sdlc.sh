#!/usr/bin/env bash
# Short entry point for the mandatory Python SDLC engine.
# Installed to sdlc-spdd/scripts/sdlc.sh in target projects (storage v3);
# lives at scripts/sdlc.sh in the orchestrator repo.
#
# Install/upgrade and selected session/capture utilities remain shell scripts,
# but workflow, registry, pointer, and gate behavior always comes from Python.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$(basename "$(dirname "${SCRIPT_DIR}")")" == "sdlc-spdd" ]]; then
  # Installed or dogfood home: <root>/sdlc-spdd/scripts/sdlc.sh
  ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
else
  # Orchestrator source checkout: <root>/scripts/sdlc.sh
  ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi

# Script-derived ROOT finds the orch .venv + engine source. --target/--root
# only changes the project the engine operates on (otherwise `next` runs
# against the orch clone and prints "no active Work ID").
PROJECT_ROOT="${ROOT}"
_forward=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target|--root)
      if [[ -z "${2:-}" ]]; then
        echo "sdlc: $1 requires a directory path" >&2
        exit 2
      fi
      if [[ ! -d "$2" ]]; then
        echo "sdlc: $1 is not a directory: $2" >&2
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
fi

case "${SDLC_ENGINE:-python}" in
  auto|python) ;;
  shell)
    echo "sdlc: SDLC_ENGINE=shell is no longer supported; the Python engine is required" >&2
    echo "Install with: ./scripts/setup-engine-venv.sh  # Python 3.12" >&2
    exit 2
    ;;
  *)
    echo "sdlc: unknown SDLC_ENGINE='${SDLC_ENGINE}' (Python is the only supported engine)" >&2
    exit 2
    ;;
esac

case "${SDLC_GATE_ENGINE:-python}" in
  python) ;;
  shell)
    echo "sdlc: SDLC_GATE_ENGINE=shell is no longer supported; Python gate semantics are required" >&2
    echo "Install with: ./scripts/setup-engine-venv.sh  # Python 3.12" >&2
    exit 2
    ;;
  *)
    echo "sdlc: unknown SDLC_GATE_ENGINE='${SDLC_GATE_ENGINE}' (Python gates are mandatory)" >&2
    exit 2
    ;;
esac

_python_engine_available() {
  declare -F resolve_engine_python >/dev/null 2>&1 || return 1
  resolve_engine_python || return 1
  if [[ -d "${ROOT}/engine/src/sdlc_engine" ]]; then
    PYTHONPATH="${ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
      "${SDLC_PY}" -c 'import sdlc_engine' 2>/dev/null
    return $?
  fi
  "${SDLC_PY}" -c 'import sdlc_engine' 2>/dev/null
}

_run_python_engine() {
  local args=("$@")
  resolve_engine_python || exit 1
  if [[ -d "${ROOT}/engine/src/sdlc_engine" ]]; then
    PYTHONPATH="${ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
      exec "${SDLC_PY}" -m sdlc_engine --root "${PROJECT_ROOT}" "${args[@]}"
  fi
  exec "${SDLC_PY}" -m sdlc_engine --root "${PROJECT_ROOT}" "${args[@]}"
}

cmd="${1:-next}"
if [[ $# -gt 0 ]]; then
  shift
fi

# Normalize compatibility aliases and bridge only the explicitly retained
# session/capture utilities. All lifecycle behavior remains in sdlc_engine.
_engine_args=()
case "${cmd}" in
  local-start) _engine_args=("local" "start" "$@") ;;
  local-list) _engine_args=("local" "list" "$@") ;;
  local-status) _engine_args=("local" "status" "$@") ;;
  local-capture) _engine_args=("local" "capture" "$@") ;;
  local-shelf) _engine_args=("local" "shelf" "$@") ;;
  local-resume) _engine_args=("local" "resume" "$@") ;;
  local-promote) _engine_args=("local" "promote" "$@") ;;
  local-abandon) _engine_args=("local" "abandon" "$@") ;;
  db-rebuild) _engine_args=("db" "rebuild" "$@") ;;
  db-status) _engine_args=("db" "status" "$@") ;;
  db-path) _engine_args=("db" "path" "$@") ;;
  db-query) _engine_args=("db" "query" "$@") ;;
  db-lookup) _engine_args=("db" "lookup" "$@") ;;
  db-export) _engine_args=("db" "export" "$@") ;;
  work-init-from-adf|init-from-adf)
    _engine_args=("work" "init-from-adf" "$@")
    ;;
  guide-query)
    _engine_args=("context" "guide-query" "$@")
    ;;
  start|/sdlc-workflow-start)
    _engine_args=("shell" "start-agent-session.sh" "--target" "${PROJECT_ROOT}" "$@")
    ;;
  capture|/sdlc-workflow-capture)
    _engine_args=("shell" "capture-session-memory.sh" "--target" "${PROJECT_ROOT}" "$@")
    ;;
  complete|/sdlc-workflow-complete)
    _engine_args=("shell" "capture-session-memory.sh" "--target" "${PROJECT_ROOT}" "--complete" "$@")
    ;;
  accept|/sdlc-accept-lessons)
    _engine_args=("shell" "accept-lessons.sh" "--target" "${PROJECT_ROOT}" "$@")
    ;;
  /sdlc-workflow-next) _engine_args=("next" "$@") ;;
  /sdlc-workflow-resume) _engine_args=("resume" "$@") ;;
  /sdlc-workflow-advance) _engine_args=("advance" "$@") ;;
  /sdlc-workflow-skip) _engine_args=("skip" "$@") ;;
  /sdlc-workflow-shelf) _engine_args=("shelf" "$@") ;;
  /sdlc-workflow-sync) _engine_args=("sync" "$@") ;;
  /sdlc-workflow-gate) _engine_args=("gate" "$@") ;;
  /sdlc-workflow-list-shelved) _engine_args=("list-shelved" "$@") ;;
  /sdlc-team-status) _engine_args=("team" "$@") ;;
  /sdlc-list-work) _engine_args=("list-work" "$@") ;;
  /sdlc-team-claim) _engine_args=("claim" "$@") ;;
  /sdlc-team-release) _engine_args=("release" "$@") ;;
  /sdlc-team-archive) _engine_args=("archive" "$@") ;;
  help|-h|--help) _engine_args=("--help" "$@") ;;
  *) _engine_args=("${cmd}" "$@") ;;
esac

if ! _python_engine_available; then
  echo "sdlc: the Python engine (sdlc_engine) is required but not importable" >&2
  echo "Install with: ./scripts/setup-engine-venv.sh  # Python 3.12" >&2
  exit 1
fi

_run_python_engine "${_engine_args[@]}"
