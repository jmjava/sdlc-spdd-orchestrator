#!/usr/bin/env bash
# T01 prereq check for SPIKE-001 Guide ingest (local operator script).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GUIDE_ROOT="${GUIDE_ROOT:-${HOME}/github/jmjava/orch-guide}"
GUIDE_PORT="${GUIDE_PORT:-21337}"

pass=0
fail=0
warn=0
ok() { echo "  OK: $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL: $1" >&2; fail=$((fail + 1)); }
note() { echo "  NOTE: $1"; warn=$((warn + 1)); }

echo "SPIKE-001 Guide setup verification"
echo "  Repo:  ${REPO_ROOT}"
echo "  Guide: ${GUIDE_ROOT}"
echo ""

echo "== Spike branch fixture tests =="
if "${REPO_ROOT}/tests/test-retrieval-fixture-resolver.sh"; then
  ok "fixture gold test"
else
  bad "fixture gold test"
fi

echo ""
echo "== Guide checkout =="
if [[ -d "${GUIDE_ROOT}" ]]; then
  ok "guide directory exists"
  branch="$(git -C "${GUIDE_ROOT}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  # Detached HEAD is expected when pinned to tag sdlc-spdd-projection-v2.
  if [[ "${branch}" == "main" || "${branch}" == "HEAD" || "${branch}" == "sdlc-spdd-projection-v1" || "${branch}" == "sdlc-spdd-projection-v2" ]]; then
    ok "guide on main or sdlc-spdd-projection-v2 pin (leg 2+3)"
  elif [[ "${branch}" == "ingest-to-hub" ]]; then
    ok "guide branch ingest-to-hub (leg 2 only)"
    note "checkout sdlc-spdd-projection-v2 (or main) for leg 3 entity projection"
  else
    note "guide on branch '${branch}' (prefer sdlc-spdd-projection-v2 or main)"
  fi
else
  bad "guide not found at ${GUIDE_ROOT} — set GUIDE_ROOT"
fi

echo ""
echo "== Guide profiles =="
for profile in menke-5 menke-fixture; do
  f="${GUIDE_ROOT}/scripts/user-config/application-${profile}.yml"
  if [[ -f "${f}" ]]; then
    ok "profile ${profile}"
  else
    example="${REPO_ROOT}/templates/guide-profiles/application-${profile}-orchestrator-context.yml.example"
    [[ "${profile}" == "menke-fixture" ]] && example="${REPO_ROOT}/templates/guide-profiles/application-menke-fixture.yml.example"
    if [[ -f "${example}" ]]; then
      note "copy ${example} → ${f}"
    else
      bad "missing profile template for ${profile}"
    fi
  fi
done

echo ""
echo "== Guide runtime (optional) =="
if curl -sf --max-time 3 "http://localhost:${GUIDE_PORT}/actuator/health" >/dev/null 2>&1; then
  ok "Guide health on :${GUIDE_PORT}"
  echo "  MCP SSE: http://localhost:${GUIDE_PORT}/sse"
  if curl -sf --max-time 3 "http://localhost:${GUIDE_PORT}/api/v1/data/spdd-projection/stats" >/dev/null 2>&1; then
    ok "spdd-projection API (leg 3)"
    entity_count="$(curl -s "http://localhost:${GUIDE_PORT}/api/v1/data/spdd-projection/stats" | jq -r '.totalEntities // 0' 2>/dev/null || echo 0)"
    if [[ "${entity_count}" =~ ^[0-9]+$ ]] && (( entity_count > 0 )); then
      ok "__Entity__ count ${entity_count}"
    else
      note "run ./scripts/guide/project-spdd-entities.sh after enabling spdd-projection"
    fi
  else
    note "spdd-projection API missing — use guide tag sdlc-spdd-projection-v2 (or main)"
  fi
else
  note "Guide not running on :${GUIDE_PORT} — start before ingest/MCP"
fi

echo ""
if (( fail > 0 )); then
  echo "${fail} failed, ${pass} passed, ${warn} notes" >&2
  exit 1
fi
echo "Setup check: ${pass} passed, ${warn} notes. See docs/spike-guide-ingest-agent-context.md"
