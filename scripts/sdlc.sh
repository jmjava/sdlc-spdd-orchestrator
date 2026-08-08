#!/usr/bin/env bash
# Short entry point for SDLC pointer + workflow helpers.
# Installed to sdlc-spdd/scripts/sdlc.sh in target projects (storage v3);
# lives at scripts/sdlc.sh in the orchestrator repo.
#
# Engine selection (v2):
#   SDLC_ENGINE=shell   Legacy bash workflow scripts (default — stable)
#   SDLC_ENGINE=python  Require Python engine
#   SDLC_ENGINE=auto    Prefer Python engine when importable
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "${SCRIPT_DIR}/../agent-context/sdlc-workflow.sh" ]]; then
  # Orchestrator repo: scripts/sdlc.sh next to agent-context/.
  ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
  WORKFLOW="${ROOT}/agent-context/sdlc-workflow.sh"
elif [[ -f "${SCRIPT_DIR}/sdlc-workflow.sh" ]]; then
  # Storage v3 install: <root>/sdlc-spdd/scripts/sdlc.sh.
  ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
  WORKFLOW="${SCRIPT_DIR}/sdlc-workflow.sh"
elif [[ -f "${SCRIPT_DIR}/../../agent-context/sdlc-workflow.sh" ]]; then
  # Legacy sprawled install: <root>/scripts/sdlc-spdd/sdlc.sh.
  ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
  WORKFLOW="${ROOT}/agent-context/sdlc-workflow.sh"
else
  ROOT="$(git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null || pwd)"
  WORKFLOW="${ROOT}/sdlc-spdd/scripts/sdlc-workflow.sh"
  if [[ ! -f "${WORKFLOW}" ]]; then
    WORKFLOW="${ROOT}/agent-context/sdlc-workflow.sh"
  fi
fi

export SDLC_ROOT="${ROOT}"
ENGINE_MODE="${SDLC_ENGINE:-shell}"

_python_engine_available() {
  if [[ -d "${ROOT}/engine/src/sdlc_engine" ]]; then
    PYTHONPATH="${ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
      python3 -c 'import sdlc_engine' 2>/dev/null
    return $?
  fi
  python3 -c 'import sdlc_engine' 2>/dev/null
}

_run_python_engine() {
  local args=("$@")
  if [[ -d "${ROOT}/engine/src/sdlc_engine" ]]; then
    PYTHONPATH="${ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
      exec python3 -m sdlc_engine --root "${ROOT}" "${args[@]}"
  fi
  exec python3 -m sdlc_engine --root "${ROOT}" "${args[@]}"
}

cmd="${1:-next}"
if [[ $# -gt 0 ]]; then
  shift
fi

# Python-engine-only commands that must work even when SDLC_ENGINE=shell.
# Normalize hyphen aliases: local-* → local <verb>, db-* → db <verb>.
_py_only_args=()
case "${cmd}" in
  local)
    _py_only_args=("local" "$@")
    ;;
  local-start) _py_only_args=("local" "start" "$@") ;;
  local-list) _py_only_args=("local" "list" "$@") ;;
  local-status) _py_only_args=("local" "status" "$@") ;;
  local-capture) _py_only_args=("local" "capture" "$@") ;;
  local-shelf) _py_only_args=("local" "shelf" "$@") ;;
  local-resume) _py_only_args=("local" "resume" "$@") ;;
  local-promote) _py_only_args=("local" "promote" "$@") ;;
  local-abandon) _py_only_args=("local" "abandon" "$@") ;;
  quick)
    _py_only_args=("quick" "$@")
    ;;
  db)
    _py_only_args=("db" "$@")
    ;;
  db-rebuild) _py_only_args=("db" "rebuild" "$@") ;;
  db-status) _py_only_args=("db" "status" "$@") ;;
  db-path) _py_only_args=("db" "path" "$@") ;;
  db-query) _py_only_args=("db" "query" "$@") ;;
  db-lookup) _py_only_args=("db" "lookup" "$@") ;;
  db-export) _py_only_args=("db" "export" "$@") ;;
  commit-message)
    _py_only_args=("commit-message" "$@")
    ;;
  viewer)
    _py_only_args=("viewer" "$@")
    ;;
  work)
    _py_only_args=("work" "$@")
    ;;
  work-init-from-adf|init-from-adf)
    _py_only_args=("work" "init-from-adf" "$@")
    ;;
  installer|console|dashboard)
    _py_only_args=("${cmd}" "$@")
    ;;
esac
if ((${#_py_only_args[@]} > 0)); then
  if ! _python_engine_available; then
    echo "sdlc: '${_py_only_args[0]}' requires the Python engine (engine/sdlc_engine)" >&2
    echo "Install with: python3 -m pip install -e '${ROOT}/engine'" >&2
    exit 1
  fi
  _run_python_engine "${_py_only_args[@]}"
fi

case "${ENGINE_MODE}" in
  python)
    if ! _python_engine_available; then
      echo "sdlc: SDLC_ENGINE=python but sdlc_engine is not importable" >&2
      echo "Install with: python3 -m pip install -e '${ROOT}/engine'" >&2
      exit 1
    fi
    _run_python_engine "${cmd}" "$@"
    ;;
  auto)
    if _python_engine_available; then
      _run_python_engine "${cmd}" "$@"
    fi
    ;;
  shell)
    ;;
  *)
    echo "sdlc: unknown SDLC_ENGINE='${ENGINE_MODE}' (use auto|python|shell)" >&2
    exit 2
    ;;
esac

if [[ ! -x "${WORKFLOW}" ]]; then
  echo "sdlc: workflow not installed (${WORKFLOW})" >&2
  echo "Run setup-agent-prompts.sh or upgrade-project.sh from the orchestrator repo." >&2
  exit 1
fi

exec "${WORKFLOW}" "${cmd}" "$@"
