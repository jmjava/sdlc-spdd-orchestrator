#!/usr/bin/env bash
# Cloud Agent Build install for this orchestrator (U2).
# Idempotent. Installs sdlc-engine into .venv and persists PATH on disk.
# Never writes .git/hooks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if ! command -v python3.12 >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3.12 python3.12-venv
  else
    echo "error: python3.12 is required for sdlc-engine" >&2
    exit 1
  fi
fi

"${ROOT}/scripts/setup-engine-venv.sh"

PATH_LINE="export PATH=\"${ROOT}/.venv/bin:\$PATH\""
for rc in "${HOME}/.profile" "${HOME}/.bashrc"; do
  mkdir -p "$(dirname "${rc}")"
  touch "${rc}"
  if grep -Fqx "${PATH_LINE}" "${rc}"; then
    continue
  fi
  printf '%s\n' "${PATH_LINE}" >> "${rc}"
done

if [[ ! -x "${ROOT}/.venv/bin/sdlc-engine" ]]; then
  echo "error: sdlc-engine missing after setup-engine-venv.sh" >&2
  exit 1
fi
"${ROOT}/.venv/bin/sdlc-engine" --help >/dev/null
