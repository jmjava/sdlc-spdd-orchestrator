#!/usr/bin/env bash
# Shared helpers for bash regression harnesses (storage v3, one Python engine).
#
#   source "$(dirname "${BASH_SOURCE[0]}")/lib/harness.sh"
#   T="$(harness_new_target)"          # installed target with sdlc-spdd/ home
#   harness_sdlc "${T}" claim FEAT-001  # == ${T}/sdlc-spdd/scripts/sdlc.sh claim FEAT-001
#   harness_home "${T}"                 # -> ${T}/sdlc-spdd
#
# Every harness runs the same engine the user runs: the installed
# sdlc-spdd/scripts/sdlc.sh dispatcher, which execs python -m sdlc_engine.
# There is no bash workflow twin to copy into fixtures.

HARNESS_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_REPO_ROOT="$(cd "${HARNESS_LIB_DIR}/../.." && pwd)"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

harness_finish() {
  echo
  echo "Results: ${pass} passed, ${fail} failed"
  (( fail == 0 ))
}

# Make the orchestrator's engine importable for any sdlc.sh copy (installed
# targets have no .venv of their own).
harness_export_engine() {
  if [[ -z "${PYTHON:-}" && -x "${HARNESS_REPO_ROOT}/.venv/bin/python" ]]; then
    export PYTHON="${HARNESS_REPO_ROOT}/.venv/bin/python"
  fi
  export PYTHONPATH="${HARNESS_REPO_ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}"
  unset SDLC_ENGINE SDLC_GATE_ENGINE SDLC_HOME
}

# Fresh installed target (init-project.sh, no IDE adapters). Prints its path.
harness_new_target() {
  local t
  t="$(mktemp -d)"
  harness_export_engine
  "${HARNESS_REPO_ROOT}/scripts/init-project.sh" --target "${t}" >/dev/null 2>&1 \
    || { echo "harness: init-project failed for ${t}" >&2; return 1; }
  printf '%s' "${t}"
}

harness_home() { printf '%s' "$1/sdlc-spdd"; }

harness_sdlc() {
  local t="$1"
  shift
  harness_export_engine
  "${t}/sdlc-spdd/scripts/sdlc.sh" "$@"
}

# Minimal Work ID seed: requirement + canvas with the given Final Status.
# Extra canvas body can be appended by the caller.
harness_seed_work() {
  local t="$1" work_id="$2" final_status="${3:-In Progress}"
  local home
  home="$(harness_home "${t}")"
  mkdir -p "${home}/spdd/canvas" "${home}/requirements/milestones"
  cat > "${home}/requirements/milestones/${work_id}.md" <<EOF
# Requirement: ${work_id}

## Summary

Harness requirement for ${work_id}.
EOF
  cat > "${home}/spdd/canvas/${work_id}.md" <<EOF
# REASONS Canvas: ${work_id}

## Metadata

- Work ID: ${work_id}
- Work Type: Feature
- Status: ${final_status}

## Final Status

- Status: ${final_status}
EOF
}
