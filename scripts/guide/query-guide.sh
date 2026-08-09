#!/usr/bin/env bash
# Delegate a retrieval question to Guide spdd_* tools (for Cursor, Copilot, scripts).
#
# Uses the same payloads as native MCP at /sse — REST parity when the IDE is not
# connected to Guide MCP directly.
#
# Usage:
#   ./scripts/guide/query-guide.sh --work-id FEAT-001-order-status-api
#   ./scripts/guide/query-guide.sh --area engine/tests
#   ./scripts/guide/query-guide.sh --lesson-id 'pitfall:FEAT-001:engine:retro'
#   ./scripts/guide/query-guide.sh --stats
#   ./scripts/guide/query-guide.sh --text --work-id FEAT-001-order-status-api
#   ./scripts/guide/query-guide.sh --tool spdd_getLesson --json '{"id":"pitfall:..."}'
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_PY="${ROOT}/.venv/bin/python"
ENGINE_ARGS=(--root "${ROOT}")

if [[ -x "${VENV_PY}" ]]; then
  PY="${VENV_PY}"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
  export PYTHONPATH="${ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}"
else
  echo "error: python3 or .venv required" >&2
  exit 1
fi

exec "${PY}" -m sdlc_engine "${ENGINE_ARGS[@]}" context guide-query "$@"
