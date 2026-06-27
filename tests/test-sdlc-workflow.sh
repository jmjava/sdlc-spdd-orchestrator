#!/usr/bin/env bash
set -euo pipefail

# Regression harness for agent-context/sdlc-workflow.sh
#
# Usage: ./tests/test-sdlc-workflow.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKFLOW="${REPO_ROOT}/agent-context/sdlc-workflow.sh"
POINTER="${REPO_ROOT}/agent-context/sdlc-pointer.sh"
START="${REPO_ROOT}/scripts/start-agent-session.sh"
CAPTURE="${REPO_ROOT}/scripts/capture-session-memory.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

wf() { SDLC_ROOT="${1}" "${WORKFLOW}" "${@:2}"; }

setup_feature() {
  local t="$1"
  local work_id="$2"
  mkdir -p "${t}/agent-context/sessions" \
    "${t}/agent-context/features/${work_id}" \
    "${t}/spdd/canvas" \
    "${t}/spdd/analysis"
  cp "${POINTER}" "${t}/agent-context/sdlc-pointer.sh"
  cp "${WORKFLOW}" "${t}/agent-context/sdlc-workflow.sh"
  chmod +x "${t}/agent-context/sdlc-pointer.sh" "${t}/agent-context/sdlc-workflow.sh"
}

# ---------------------------------------------------------------------------
echo "== Test 1: resume sets pointer and creates workflow state =="
T="${WORK}/resume"
setup_feature "${T}" "FEAT-001-alpha"
wf "${T}" resume FEAT-001-alpha >/dev/null
ptr="$(SDLC_ROOT="${T}" "${T}/agent-context/sdlc-pointer.sh" get)"
if [[ "${ptr}" == "FEAT-001-alpha" ]]; then ok "resume sets pointer"; else bad "pointer not set"; fi
if [[ -f "${T}/.sdlc/workflows/FEAT-001-alpha.state" ]]; then ok "workflow state created"; else bad "missing state file"; fi

# ---------------------------------------------------------------------------
echo "== Test 2: advance moves through phases =="
wf "${T}" advance >/dev/null
phase="$(grep '^phase=' "${T}/.sdlc/workflows/FEAT-001-alpha.state" | cut -d= -f2)"
if [[ "${phase}" == "analysis" ]]; then ok "advance to analysis"; else bad "expected analysis, got ${phase}"; fi

# ---------------------------------------------------------------------------
echo "== Test 3: skip records reason and moves past phase =="
wf "${T}" skip api-test --reason "no HTTP surface" >/dev/null
if grep -q '^skip_api-test=' "${T}/.sdlc/workflows/FEAT-001-alpha.state"; then
  ok "skip recorded in state"
else
  bad "skip not recorded"
fi

# ---------------------------------------------------------------------------
echo "== Test 4: shelf and resume shelved work =="
wf "${T}" shelf --reason "context switch" >/dev/null
ptr="$(SDLC_ROOT="${T}" "${T}/agent-context/sdlc-pointer.sh" get)"
if [[ -z "${ptr}" ]]; then ok "shelf clears pointer"; else bad "pointer should be empty"; fi
active="$(grep '^active=' "${T}/.sdlc/workflows/FEAT-001-alpha.state" | cut -d= -f2)"
if [[ "${active}" == "0" ]]; then ok "shelf marks inactive"; else bad "expected active=0"; fi

setup_feature "${T}" "CHORE-002-beta"
wf "${T}" resume CHORE-002-beta >/dev/null
if wf "${T}" list-shelved | grep -q 'FEAT-001-alpha'; then ok "shelved list includes parked work"; else bad "shelved list missing FEAT-001-alpha"; fi
wf "${T}" resume FEAT-001-alpha >/dev/null
ptr="$(SDLC_ROOT="${T}" "${T}/agent-context/sdlc-pointer.sh" get)"
if [[ "${ptr}" == "FEAT-001-alpha" ]]; then ok "resume restores shelved pointer"; else bad "resume failed"; fi

# ---------------------------------------------------------------------------
echo "== Test 5: sync infers phase from artifacts =="
T="${WORK}/sync"
work_id="FEAT-003-gamma"
setup_feature "${T}" "${work_id}"
mkdir -p "${T}/requirements/milestones"
printf '# req\n' > "${T}/requirements/milestones/${work_id}.md"
printf '# analysis\n' > "${T}/spdd/analysis/${work_id}-analysis.md"
printf '# canvas\nReady For Coding\n' > "${T}/spdd/canvas/${work_id}.md"
wf "${T}" resume "${work_id}" >/dev/null
phase="$(grep '^phase=' "${T}/.sdlc/workflows/${work_id}.state" | cut -d= -f2)"
if [[ "${phase}" == "code" ]]; then ok "sync infers code from artifacts"; else bad "expected code, got ${phase}"; fi
if grep -q '^gate_canvas_exists=passed' "${T}/.sdlc/workflows/${work_id}.state"; then
  ok "sync marks canvas gate passed"
else
  bad "canvas gate not passed"
fi

# ---------------------------------------------------------------------------
echo "== Test 6: status output is human-readable =="
out="$(wf "${T}" status "${work_id}")"
if grep -q 'Quality gates:' <<< "${out}" && grep -q 'Phase track:' <<< "${out}"; then
  ok "status shows gates and phase track"
else
  bad "status output incomplete"
fi

# ---------------------------------------------------------------------------
echo "== Test 7: session scripts update workflow timestamps =="
T="${WORK}/integrate"
work_id="FEAT-004-delta"
setup_feature "${T}" "${work_id}"
"${START}" --target "${T}" --work-id "${work_id}" --phase plan >/dev/null
if grep -q '^last_session_at=' "${T}/.sdlc/workflows/${work_id}.state"; then
  ok "start-agent-session touches workflow"
else
  bad "missing last_session_at"
fi
"${CAPTURE}" --target "${T}" --work-id "${work_id}" --phase plan --summary "planned" >/dev/null
if grep -q '^last_capture_at=' "${T}/.sdlc/workflows/${work_id}.state"; then
  ok "capture-session-memory records workflow capture"
else
  bad "missing last_capture_at"
fi

# ---------------------------------------------------------------------------
echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
