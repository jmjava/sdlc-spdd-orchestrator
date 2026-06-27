#!/usr/bin/env bash
# Simple pointer manager for SDLC chores/tasks
# Usage:
#   source agent-context/sdlc-pointer.sh
#   sdlc_init                          # call on initialization
#   sdlc_set_pointer ID                # sets pointer
#   sdlc_get_pointer                   # prints pointer or empty
#   sdlc_reset_pointer                 # clears pointer
#   run_against_pointer "<expected>" -- <command...>
#
# Default storage: .sdlc/pointer in the repository root.

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  set -euo pipefail
fi

SDLC_ROOT="${SDLC_ROOT:-$(git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null || pwd)}"
SDLC_DIR="${SDLC_DIR:-${SDLC_ROOT}/.sdlc}"
SDLC_POINTER="${SDLC_DIR}/pointer"
SDLC_LOCK="${SDLC_DIR}/pointer.lock"

mkdir -p "${SDLC_DIR}"

_have_flock() {
  command -v flock >/dev/null 2>&1
}

sdlc_get_pointer() {
  if [[ ! -f "${SDLC_POINTER}" ]]; then
    printf ""
    return 0
  fi
  cat "${SDLC_POINTER}"
}

sdlc_set_pointer() {
  local new="${1:-}"
  if [[ -z "${new}" ]]; then
    echo "sdlc_set_pointer: missing pointer id" >&2
    return 2
  fi
  if _have_flock; then
    flock --exclusive --timeout 5 "${SDLC_LOCK}" \
      bash -c 'printf "%s" "$1" > "$2"' _ "${new}" "${SDLC_POINTER}"
  else
    local tmpfile="${SDLC_POINTER}.$(date +%s).tmp"
    printf '%s' "${new}" > "${tmpfile}"
    mv -f "${tmpfile}" "${SDLC_POINTER}"
  fi
  echo "pointer set to: ${new}"
}

sdlc_reset_pointer() {
  if _have_flock; then
    flock --exclusive --timeout 5 "${SDLC_LOCK}" \
      bash -c 'rm -f "$1"' _ "${SDLC_POINTER}"
  else
    rm -f "${SDLC_POINTER}" 2>/dev/null || true
  fi
  echo "pointer cleared"
}

sdlc_init() {
  if [[ -n "${SDLC_POINTER_OVERRIDE:-}" ]]; then
    sdlc_set_pointer "${SDLC_POINTER_OVERRIDE}"
  fi
}

run_against_pointer() {
  local expected="${1:-}"
  shift || true
  if [[ "${1:-}" == "--" ]]; then
    shift
  fi
  if [[ -z "${expected}" ]]; then
    echo "run_against_pointer: expected pointer id required" >&2
    return 2
  fi
  local current=""
  if _have_flock; then
    current="$(flock --shared --timeout 5 "${SDLC_LOCK}" \
      bash -c 'cat "$1" 2>/dev/null || true' _ "${SDLC_POINTER}")"
  else
    current="$(cat "${SDLC_POINTER}" 2>/dev/null || true)"
  fi
  if [[ "${current}" != "${expected}" ]]; then
    echo "Pointer mismatch: current='${current}' expected='${expected}' — refusing to run" >&2
    return 3
  fi
  "$@"
}

# CLI when script executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  cmd="${1:-}"
  shift || true
  case "${cmd}" in
    set|/sdlc-set-pointer)
      sdlc_set_pointer "$@"
      ;;
    get|/sdlc-get-pointer)
      sdlc_get_pointer
      ;;
    reset|/sdlc-reset-pointer)
      sdlc_reset_pointer
      ;;
    init|/sdlc-init)
      sdlc_init
      ;;
    run|/sdlc-run)
      expected="${1:-}"
      shift || true
      run_against_pointer "${expected}" -- "$@"
      ;;
    *)
      echo "Usage: $0 {set|get|reset|init|run} ..." >&2
      exit 2
      ;;
  esac
fi
