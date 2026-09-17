#!/usr/bin/env bash
# Prereq check for Guide DICE ingest (local operator script).
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

echo "Guide DICE setup verification"
echo "  Repo:  ${REPO_ROOT}"
echo "  Guide: ${GUIDE_ROOT}"
echo ""

echo "== Guide checkout =="
if [[ -d "${GUIDE_ROOT}" ]]; then
  ok "guide directory exists"
  if ! git -C "${GUIDE_ROOT}" rev-parse --git-dir >/dev/null 2>&1; then
    bad "GUIDE_ROOT is not a git checkout"
  else
    # Leftover #20: the pin is the *tag* refs/tags/spdd-projection-v3.
    # `rev-parse --abbrev-ref HEAD` is "HEAD" on any detached checkout, so
    # treating that name (or a local branch named sdlc-spdd-projection-v3 /
    # spdd-projection-v3) as the pin passed by luck. Compare peeled SHAs.
    tag_ref="refs/tags/spdd-projection-v3"
    if ! git -C "${GUIDE_ROOT}" rev-parse --verify --quiet "${tag_ref}" >/dev/null; then
      bad "missing tag spdd-projection-v3 — a local branch of that name is not the pin"
    else
      tag_sha="$(git -C "${GUIDE_ROOT}" rev-parse "${tag_ref}^{commit}")"
      head_sha="$(git -C "${GUIDE_ROOT}" rev-parse HEAD)"
      branch="$(git -C "${GUIDE_ROOT}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
      if [[ "${head_sha}" == "${tag_sha}" ]]; then
        ok "HEAD is the spdd-projection-v3 tag"
      elif [[ "${branch}" == "main" ]]; then
        ok "guide on main (tag spdd-projection-v3 is present)"
      else
        bad "HEAD ${head_sha:0:7} is not tag spdd-projection-v3 (${tag_sha:0:7}); detached HEAD and a local branch named after the pin are not the pin"
      fi
    fi
  fi
else
  bad "guide not found at ${GUIDE_ROOT} — set GUIDE_ROOT"
fi

echo ""
echo "== Guide profiles =="
profile="menke-5"
f="${GUIDE_ROOT}/scripts/user-config/application-${profile}.yml"
if [[ -f "${f}" ]]; then
  ok "profile ${profile}"
else
  example="${REPO_ROOT}/templates/guide-profiles/application-${profile}-orchestrator-context.yml.example"
  if [[ -f "${example}" ]]; then
    note "copy ${example} → ${f}"
  else
    bad "missing profile template for ${profile}"
  fi
fi

echo ""
echo "== Guide runtime (optional) =="
if curl -sf --max-time 3 "http://localhost:${GUIDE_PORT}/actuator/health" >/dev/null 2>&1; then
  ok "Guide health on :${GUIDE_PORT}"
  echo "  MCP SSE: http://localhost:${GUIDE_PORT}/sse"
  if curl -sf --max-time 3 "http://localhost:${GUIDE_PORT}/api/v1/data/spdd-projection/stats" >/dev/null 2>&1; then
    ok "spdd-projection API"
    entity_count="$(curl -s "http://localhost:${GUIDE_PORT}/api/v1/data/spdd-projection/stats" | jq -r '.totalEntities // 0' 2>/dev/null || echo 0)"
    if [[ "${entity_count}" =~ ^[0-9]+$ ]] && (( entity_count > 0 )); then
      ok "__Entity__ count ${entity_count}"
    else
      note "run ./scripts/guide/project-spdd-entities.sh after enabling spdd-projection"
    fi
  else
    note "spdd-projection API missing — use guide tag spdd-projection-v3 (or main)"
  fi
else
  note "Guide not running on :${GUIDE_PORT} — start before ingest/MCP"
fi

echo ""
if (( fail > 0 )); then
  echo "${fail} failed, ${pass} passed, ${warn} notes" >&2
  exit 1
fi
echo "Setup check: ${pass} passed, ${warn} notes. See docs/dice-projection-runbook.md"
