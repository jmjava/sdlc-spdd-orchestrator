#!/usr/bin/env bash
# Cloud Agent Build install for this orchestrator (U2).
# Idempotent. Installs sdlc-engine into .venv and persists PATH on disk.
# Never writes .git/hooks.
#
# PATH must be visible to non-interactive Cloud Agent shells. Ubuntu
# ~/.bashrc returns before the end when $- lacks i; ~/.profile is login-only.
# Prepend the export (and relocate a leftover append) so sourced bashrc
# still puts sdlc-engine on PATH.
# SDLC_INSTALL_SKIP_SYSTEM_DEPS=1 skips apt-get (proving tests).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -n "${SDLC_INSTALL_ROOT:-}" ]]; then
  ROOT="${SDLC_INSTALL_ROOT}"
fi

persist_sdlc_engine_path() {
  local home="${1:-${HOME}}"
  local path_line="export PATH=\"${ROOT}/.venv/bin:\$PATH\""
  local rc tmp
  for rc in "${home}/.profile" "${home}/.bashrc"; do
    mkdir -p "$(dirname "${rc}")"
    touch "${rc}"
    tmp="$(mktemp)"
    {
      printf '%s\n' "${path_line}"
      grep -Fxv "${path_line}" "${rc}" || true
    } > "${tmp}"
    mv "${tmp}" "${rc}"
  done
}

if [[ "${1:-}" == "--path-only" || "${SDLC_INSTALL_PATH_ONLY:-}" == "1" ]]; then
  persist_sdlc_engine_path "${HOME}"
  exit 0
fi

cd "${ROOT}"

if ! command -v python3.12 >/dev/null 2>&1; then
  if [[ "${SDLC_INSTALL_SKIP_SYSTEM_DEPS:-}" == "1" ]]; then
    echo "error: python3.12 is required for sdlc-engine" >&2
    exit 1
  fi
  if command -v sudo >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3.12 python3.12-venv
  else
    echo "error: python3.12 is required for sdlc-engine" >&2
    exit 1
  fi
fi

"${ROOT}/scripts/setup-engine-venv.sh"

persist_sdlc_engine_path "${HOME}"

if [[ ! -x "${ROOT}/.venv/bin/sdlc-engine" ]]; then
  echo "error: sdlc-engine missing after setup-engine-venv.sh" >&2
  exit 1
fi
"${ROOT}/.venv/bin/sdlc-engine" --help >/dev/null
