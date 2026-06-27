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
echo "== Test 8: next command gives actionable output =="
T="${WORK}/next"
work_id="FEAT-005-next"
setup_feature "${T}" "${work_id}"
printf '# canvas\nReady For Coding\n' > "${T}/spdd/canvas/${work_id}.md"
wf "${T}" resume "${work_id}" >/dev/null
out="$(wf "${T}" next)"
if grep -q 'Do now (assistant):' <<< "${out}" && grep -q 'When this phase is done:' <<< "${out}"; then
  ok "next output is actionable"
else
  bad "next output missing sections"
fi

# ---------------------------------------------------------------------------
echo "== Test 9: status --json for agents =="
json="$(wf "${T}" status --json)"
if grep -q '"phase":"code"' <<< "${json}" && grep -q '"recommended_command"' <<< "${json}"; then
  ok "json status includes phase and command"
else
  bad "json status incomplete: ${json}"
fi

# ---------------------------------------------------------------------------
echo "== Test 10: sdlc.sh wrapper delegates =="
T="${WORK}/wrapper"
work_id="FEAT-005-wrap"
setup_feature "${T}" "${work_id}"
mkdir -p "${T}/scripts/sdlc-spdd"
cp "${REPO_ROOT}/scripts/sdlc.sh" "${T}/scripts/sdlc-spdd/sdlc.sh"
chmod +x "${T}/scripts/sdlc-spdd/sdlc.sh"
SDLC_ROOT="${T}" "${T}/scripts/sdlc-spdd/sdlc.sh" resume "${work_id}" >/dev/null
out="$(SDLC_ROOT="${T}" "${T}/scripts/sdlc-spdd/sdlc.sh" next)"
if grep -q "${work_id}" <<< "${out}"; then ok "sdlc.sh wrapper works"; else bad "sdlc.sh wrapper failed"; fi

# ---------------------------------------------------------------------------
echo "== Test 11: session brief includes workflow state =="
T="${WORK}/brief"
work_id="FEAT-006-brief"
setup_feature "${T}" "${work_id}"
"${START}" --target "${T}" --work-id "${work_id}" --phase plan >/dev/null
if grep -q '## Workflow State' "${T}/agent-context/sessions/current-session.md" \
  && grep -q 'Assistant command' "${T}/agent-context/sessions/current-session.md"; then
  ok "session brief embeds workflow state"
else
  bad "session brief missing workflow state"
fi

# ---------------------------------------------------------------------------
echo "== Test 12: infers next canvas operation from REASONS Canvas =="
T="${WORK}/ops"
work_id="FEAT-007-ops"
setup_feature "${T}" "${work_id}"
cp "${REPO_ROOT}/examples/spring-boot-order-api/spdd/canvas/FEAT-001-order-status-api.md" \
  "${T}/spdd/canvas/${work_id}.md"
wf "${T}" resume "${work_id}" >/dev/null
wf "${T}" sync "${work_id}" >/dev/null
op="$(grep '^operation=' "${T}/.sdlc/workflows/${work_id}.state" | cut -d= -f2)"
if [[ "${op}" == "T03" ]]; then ok "sync infers next operation T03"; else bad "expected T03, got ${op}"; fi
out="$(wf "${T}" next)"
if grep -q 'operation T03' <<< "${out}"; then ok "next recommends T03 in code command"; else bad "next missing T03 command"; fi
json="$(wf "${T}" status --json)"
if grep -q '"operation":"T03"' <<< "${json}" && grep -q '"operation_title"' <<< "${json}"; then
  ok "json includes operation and title"
else
  bad "json missing operation fields"
fi

# ---------------------------------------------------------------------------
echo "== Test 13: capture wrapper guards pointer =="
T="${WORK}/capture-guard"
work_id="FEAT-008-cap"
setup_feature "${T}" "${work_id}"
mkdir -p "${T}/scripts/sdlc-spdd"
cp "${REPO_ROOT}/scripts/sdlc.sh" "${T}/scripts/sdlc-spdd/sdlc.sh"
cp "${CAPTURE}" "${T}/scripts/sdlc-spdd/capture-session-memory.sh"
chmod +x "${T}/scripts/sdlc-spdd/sdlc.sh" "${T}/scripts/sdlc-spdd/capture-session-memory.sh"
SDLC_ROOT="${T}" "${T}/scripts/sdlc-spdd/sdlc.sh" resume "${work_id}" >/dev/null
if SDLC_ROOT="${T}" "${T}/scripts/sdlc-spdd/sdlc.sh" capture --summary "ok" >/dev/null 2>&1; then
  ok "capture succeeds when pointer matches"
else
  bad "capture should succeed for active pointer"
fi
SDLC_ROOT="${T}" "${T}/scripts/sdlc-spdd/sdlc.sh" resume FEAT-999-other >/dev/null 2>&1 || true
if SDLC_ROOT="${T}" "${T}/scripts/sdlc-spdd/sdlc.sh" capture --work-id "${work_id}" --summary "bad" >/dev/null 2>&1; then
  bad "capture should refuse mismatched work-id"
else
  ok "capture refuses stale work-id"
fi

# ---------------------------------------------------------------------------
echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
