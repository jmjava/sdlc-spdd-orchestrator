#!/usr/bin/env bash
# Fail on dead code vulture reports outside config/vulture-whitelist.py.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHITELIST="${VULTURE_WHITELIST:-$ROOT/config/vulture-whitelist.py}"
MIN="${VULTURE_MIN_CONFIDENCE:-60}"
if [[ $# -eq 0 ]]; then
  echo "usage: check-vulture.sh <path>..." >&2
  exit 2
fi
exec python3 -m vulture "$@" "$WHITELIST" --min-confidence "$MIN"
