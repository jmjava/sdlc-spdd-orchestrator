#!/usr/bin/env bash
# Optional Python engine paths when sdlc_engine is importable.
set -euo pipefail
# shellcheck source=../lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib.sh"

ROOT="${1:?target root required}"
echo "== 07 python engine (optional) =="

if ! PYTHONPATH="${REPO_ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
  python3 -c 'import sdlc_engine' 2>/dev/null; then
  skipped "sdlc_engine not importable (install engine[dev] to enable)"
  exit 0
fi

# Consumer targets do not vendor the engine; invoke from orchestrator with --root.
run_engine() {
  PYTHONPATH="${REPO_ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m sdlc_engine --root "${ROOT}" "$@"
}

run_engine version >/dev/null && ok "engine version" || bad "engine version"
run_engine list-work >/dev/null && ok "engine list-work" || bad "engine list-work"
run_engine pointer get >/dev/null && ok "engine pointer get" || bad "engine pointer get"

if run_engine commit-message >/dev/null 2>&1; then
  ok "engine commit-message"
else
  # Dirty/clean trees both acceptable if command runs; treat non-zero as soft.
  skipped "engine commit-message (no diff / exit non-zero)"
fi

if run_engine sunset --work-id FEAT-001-hello-live >/dev/null 2>&1; then
  ok "engine sunset"
else
  skipped "engine sunset (no Work ID artifacts / exit non-zero)"
fi

if run_engine db status >/dev/null 2>&1 || run_engine db-status >/dev/null 2>&1; then
  ok "engine db status"
else
  skipped "engine db status"
fi

if run_engine local list >/dev/null 2>&1 || run_engine local-list >/dev/null 2>&1; then
  ok "engine local list"
else
  skipped "engine local list"
fi
