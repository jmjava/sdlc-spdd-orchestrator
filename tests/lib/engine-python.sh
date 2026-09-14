#!/usr/bin/env bash
# Shared Python 3.12 resolution for shell harnesses.
# shellcheck shell=bash
#
# Harnesses drive the dispatcher against a temporary SDLC_ROOT, so the repo
# venv is never auto-discovered and each harness must pass PYTHON explicitly.
# CI installs the engine into the job interpreter and never creates a repo
# venv, so a hardcoded .venv path is not portable.

_ENGINE_PYTHON_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../scripts/lib/python.sh
source "$(cd "${_ENGINE_PYTHON_LIB_DIR}/../.." && pwd)/scripts/lib/python.sh"

sdlc_harness_python() {
  local repo_root="${1:?repo root required}"
  local venv_python="${repo_root}/.venv/bin/python"
  if [[ -x "${venv_python}" ]] && _python_is_usable_312 "${venv_python}"; then
    printf '%s\n' "${venv_python}"
    return 0
  fi
  local bootstrap
  bootstrap="$(PYTHON='' pick_bootstrap_python)"
  if [[ -z "${bootstrap}" ]]; then
    echo "harness: Python 3.12 not found — run ./scripts/setup-engine-venv.sh" >&2
    return 1
  fi
  printf '%s\n' "${bootstrap}"
}
