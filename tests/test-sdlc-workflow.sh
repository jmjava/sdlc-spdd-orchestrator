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

registry_file() {
  local t="$1"
  printf '%s' "${t}/spdd/memory/registry.jsonl"
}

registry_matches() {
  local t="$1" work_id="$2" regex="$3"
  local reg
  reg="$(registry_file "${t}")"
  [[ -f "${reg}" ]] && grep -q "\"work_id\": \"${work_id}\"" "${reg}" && grep -Eq "${regex}" "${reg}"
}

wf() { SDLC_ROOT="${1}" "${WORKFLOW}" "${@:2}"; }

setup_feature() {
  local t="$1"
  local work_id="$2"
  mkdir -p "${t}/agent-context/sessions" \
    "${t}/agent-context/features/${work_id}" \
    "${t}/spdd/canvas" \
    "${t}/spdd/analysis" \
    "${t}/scripts/lib"
  cp "${POINTER}" "${t}/agent-context/sdlc-pointer.sh"
  cp "${WORKFLOW}" "${t}/agent-context/sdlc-workflow.sh"
  cp "${REPO_ROOT}/agent-context/sdlc-team-registry.sh" "${t}/agent-context/sdlc-team-registry.sh"
  cp "${REPO_ROOT}/scripts/lib/paths.sh" "${t}/scripts/lib/paths.sh"
  mkdir -p "${t}/spdd/memory"
  : > "${t}/spdd/memory/registry.jsonl"
  cp "${REPO_ROOT}/scripts/lib/readiness.sh" "${t}/scripts/lib/readiness.sh"
  chmod +x "${t}/agent-context/sdlc-pointer.sh" "${t}/agent-context/sdlc-workflow.sh" "${t}/agent-context/sdlc-team-registry.sh"
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
echo "== Test 10b: sdlc.sh claim does not re-enter CLI (exec + nested source) =="
T="${WORK}/wrapper-claim"
work_id="FEAT-005b-claim"
setup_feature "${T}" "${work_id}"
mkdir -p "${T}/scripts/sdlc-spdd" "${T}/spdd/canvas"
printf '%s\n' "# ${work_id}" '' '## Final Status' '' '- Status: In Progress' \
  > "${T}/spdd/canvas/${work_id}.md"
cp "${REPO_ROOT}/scripts/sdlc.sh" "${T}/scripts/sdlc-spdd/sdlc.sh"
chmod +x "${T}/scripts/sdlc-spdd/sdlc.sh"
if SDLC_USER="tester" SDLC_ROOT="${T}" "${T}/scripts/sdlc-spdd/sdlc.sh" claim "${work_id}" >/dev/null 2>"${T}/claim.err"; then
  if registry_matches "${T}" "${work_id}" '"status": "active"'; then
    ok "sdlc.sh claim updates registry without CLI re-entry"
  else
    bad "sdlc.sh claim exited 0 but registry missing row"
  fi
else
  bad "sdlc.sh claim failed (possible CLI re-entry): $(head -3 "${T}/claim.err")"
fi

# ---------------------------------------------------------------------------
echo "== Test 11: session brief includes workflow state =="
T="${WORK}/brief"
work_id="FEAT-006-brief"
setup_feature "${T}" "${work_id}"
"${START}" --target "${T}" --work-id "${work_id}" --phase plan >/dev/null
if grep -q '## Workflow State' "${T}/.sdlc/sessions/current-session.md" \
  && grep -q 'Assistant command' "${T}/.sdlc/sessions/current-session.md"; then
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
echo "== Test 12b: empty Final Status does not keep last op incomplete =="
T="${WORK}/ops-final"
work_id="FEAT-012b-final"
setup_feature "${T}" "${work_id}"
cat > "${T}/spdd/canvas/${work_id}.md" <<'EOF'
# REASONS Canvas: FEAT-012b-final - empty Final Status

## Metadata
- Work ID: FEAT-012b-final
- Status: In Progress
- Readiness: Ready For Coding

## O - Operations

### T01 - First

- Status: Complete

### T02 - Second

- Status: Complete

## Final Status

- Status:
- Completed Date:
EOF
wf "${T}" resume "${work_id}" --phase code >/dev/null
wf "${T}" sync "${work_id}" >/dev/null
op="$(grep '^operation=' "${T}/.sdlc/workflows/${work_id}.state" | cut -d= -f2 || true)"
if [[ -z "${op}" ]]; then
  ok "all-complete canvas has empty next operation"
else
  bad "expected empty operation, got '${op}'"
fi
out="$(wf "${T}" next)"
if grep -q 'all canvas operations complete' <<< "${out}"; then
  ok "next reports all operations complete"
else
  bad "next should say all operations complete: ${out}"
fi

# ---------------------------------------------------------------------------
echo "== Test 12c: code phase with Needs Analysis redirects next to architect =="
T="${WORK}/ops-readiness"
work_id="FEAT-012c-readiness"
setup_feature "${T}" "${work_id}"
cat > "${T}/spdd/canvas/${work_id}.md" <<'EOF'
# REASONS Canvas: FEAT-012c-readiness

## Metadata
- Work ID: FEAT-012c-readiness
- Status: In Progress
- Readiness: Needs Analysis

## O - Operations

### T01 - First

- Status: Not Started

## Final Status

- Status:
EOF
wf "${T}" resume "${work_id}" --phase code >/dev/null
out="$(wf "${T}" next)"
if grep -q 'sdlc-spdd-architect' <<< "${out}" && grep -q 'not Ready For Coding' <<< "${out}"; then
  ok "next redirects to architect when readiness blocks coding"
else
  bad "next should recommend architect when Needs Analysis: ${out}"
fi
json="$(wf "${T}" status --json)"
if grep -q '"readiness":"needs-analysis"' <<< "${json}" \
  && grep -q 'sdlc-spdd-architect' <<< "${json}"; then
  ok "json readiness + recommended_command reflect gate"
else
  bad "json missing readiness gate fields: ${json}"
fi

# ---------------------------------------------------------------------------
echo "== Test 12d: advance to code refused when readiness blocks coding =="
T="${WORK}/advance-readiness"
work_id="FEAT-012d-advance"
setup_feature "${T}" "${work_id}"
cat > "${T}/spdd/canvas/${work_id}.md" <<'EOF'
# REASONS Canvas: FEAT-012d-advance

## Metadata
- Work ID: FEAT-012d-advance
- Status: In Progress
- Readiness: Needs Clarification

## O - Operations

### T01 - First

- Status: Not Started

## Final Status

- Status:
EOF
wf "${T}" resume "${work_id}" --phase architect >/dev/null
if wf "${T}" advance >/dev/null 2>"${WORK}/advance-err.txt"; then
  bad "advance architect→code should fail when Needs Clarification"
else
  if grep -q "not Ready For Coding" "${WORK}/advance-err.txt"; then
    ok "advance refuses code when readiness blocks"
  else
    bad "advance error missing readiness message: $(cat "${WORK}/advance-err.txt")"
  fi
fi
phase="$(grep '^phase=' "${T}/.sdlc/workflows/${work_id}.state" | cut -d= -f2)"
if [[ "${phase}" == "architect" ]]; then
  ok "phase stays architect after refused advance"
else
  bad "expected phase architect, got ${phase}"
fi
if wf "${T}" advance --force >/dev/null; then
  ok "advance --force overrides readiness gate"
else
  bad "advance --force should succeed"
fi
phase="$(grep '^phase=' "${T}/.sdlc/workflows/${work_id}.state" | cut -d= -f2)"
if [[ "${phase}" == "code" ]]; then
  ok "force advance reaches code"
else
  bad "expected phase code after --force, got ${phase}"
fi

# ---------------------------------------------------------------------------
echo "== Test 12e: resume --phase code warns when readiness blocks =="
T="${WORK}/resume-readiness"
work_id="FEAT-012e-resume"
setup_feature "${T}" "${work_id}"
cat > "${T}/spdd/canvas/${work_id}.md" <<'EOF'
# REASONS Canvas: FEAT-012e-resume

## Metadata
- Work ID: FEAT-012e-resume
- Readiness: Blocked

## O - Operations

### T01 - First
- Status: Not Started
EOF
out="$(wf "${T}" resume "${work_id}" --phase code)"
if grep -q 'not Ready For Coding' <<< "${out}" && grep -q 'sdlc-spdd-architect' <<< "${out}"; then
  ok "resume warns and recommends architect when blocked"
else
  bad "resume missing readiness warning: ${out}"
fi
out="$(wf "${T}" next)"
if grep -q 'Readiness: blocked' <<< "${out}"; then
  ok "next prints Readiness line"
else
  bad "next missing Readiness line: ${out}"
fi

# ---------------------------------------------------------------------------
echo "== Test 12f: advance to code succeeds when Ready For Coding =="
T="${WORK}/advance-ok"
work_id="FEAT-012f-ok"
setup_feature "${T}" "${work_id}"
cat > "${T}/spdd/canvas/${work_id}.md" <<'EOF'
# REASONS Canvas: FEAT-012f-ok

## Metadata
- Work ID: FEAT-012f-ok
- Readiness: Ready For Coding

## O - Operations

### T01 - First
- Status: Not Started
EOF
wf "${T}" resume "${work_id}" --phase architect >/dev/null
if wf "${T}" advance >/dev/null; then
  ok "advance architect→code when Ready For Coding"
else
  bad "advance should succeed when Ready For Coding"
fi
phase="$(grep '^phase=' "${T}/.sdlc/workflows/${work_id}.state" | cut -d= -f2)"
if [[ "${phase}" == "code" ]]; then ok "phase is code after ready advance"; else bad "expected code, got ${phase}"; fi
out="$(wf "${T}" next)"
if grep -q 'sdlc-spdd-code' <<< "${out}"; then ok "next recommends code when ready"; else bad "next should recommend code: ${out}"; fi

# ---------------------------------------------------------------------------
echo "== Test 12g: absent readiness still allows advance to code (compat) =="
T="${WORK}/advance-absent"
work_id="FEAT-012g-absent"
setup_feature "${T}" "${work_id}"
cat > "${T}/spdd/canvas/${work_id}.md" <<'EOF'
# REASONS Canvas: FEAT-012g-absent

## Metadata
- Work ID: FEAT-012g-absent
- Status: In Progress

## O - Operations

### T01 - First
- Status: Not Started
EOF
wf "${T}" resume "${work_id}" --phase architect >/dev/null
if wf "${T}" advance >/dev/null; then
  ok "advance allowed when readiness absent"
else
  bad "absent readiness should not block advance"
fi

# ---------------------------------------------------------------------------
echo "== Test 12h: YAML readiness + brief Readiness row + gate inference =="
T="${WORK}/yaml-ready"
work_id="FEAT-012h-yaml"
setup_feature "${T}" "${work_id}"
cat > "${T}/spdd/canvas/${work_id}.md" <<'EOF'
---
readiness: needs-redesign
---
# REASONS Canvas: FEAT-012h-yaml

## Metadata
- Work ID: FEAT-012h-yaml

## O - Operations

### T01 - First
- Status: Not Started
EOF
wf "${T}" resume "${work_id}" --phase code >/dev/null
wf "${T}" sync "${work_id}" >/dev/null
json="$(wf "${T}" status --json)"
if grep -q '"readiness":"needs-redesign"' <<< "${json}"; then
  ok "json reads YAML readiness"
else
  bad "json YAML readiness: ${json}"
fi
brief="$(SDLC_ROOT="${T}" bash -c "source '${T}/agent-context/sdlc-workflow.sh'; sdlc_workflow_brief_markdown '${work_id}'")"
if grep -q '| Readiness | needs-redesign |' <<< "${brief}"; then
  ok "brief includes Readiness row"
else
  bad "brief missing Readiness: ${brief}"
fi
# Sync should not mark architect_review passed for needs-redesign
gate="$(grep '^gate_architect_review=' "${T}/.sdlc/workflows/${work_id}.state" | cut -d= -f2 || true)"
if [[ "${gate}" != "passed" ]]; then
  ok "architect_review not auto-passed for needs-redesign"
else
  bad "architect_review should not be passed for needs-redesign (got ${gate})"
fi

# ---------------------------------------------------------------------------
echo "== Test 12i: start-agent-session recommends architect when code blocked =="
T="${WORK}/start-ready"
work_id="FEAT-012i-start"
setup_feature "${T}" "${work_id}"
mkdir -p "${T}/scripts/lib"
cp "${REPO_ROOT}/scripts/lib/"*.sh "${T}/scripts/lib/"
cat > "${T}/spdd/canvas/${work_id}.md" <<'EOF'
# REASONS Canvas: FEAT-012i-start

## Metadata
- Work ID: FEAT-012i-start
- Readiness: Needs Analysis

## O - Operations
### T01 - First
- Status: Not Started
EOF
# Point SDLC_ROOT at T so workflow readiness lib resolves; start uses TARGET workflow copy
out="$("${START}" --target "${T}" --work-id "${work_id}" --phase code 2>&1)"
brief="${T}/.sdlc/sessions/current-session.md"
if grep -q 'sdlc-spdd-architect' "${brief}" && grep -q 'Readiness | needs-analysis' "${brief}"; then
  ok "session brief readiness-gates code recommendation"
else
  bad "brief should recommend architect + show readiness: $(grep -E 'Recommended|Readiness' "${brief}" || true)"
fi

# ---------------------------------------------------------------------------
echo "== Test 12j: advance --to code from plan refused when blocked =="
T="${WORK}/advance-to"
work_id="FEAT-012j-to"
setup_feature "${T}" "${work_id}"
cat > "${T}/spdd/canvas/${work_id}.md" <<'EOF'
# REASONS Canvas: FEAT-012j-to

## Metadata
- Work ID: FEAT-012j-to
- Readiness: Blocked

## O - Operations
### T01 - First
- Status: Not Started
EOF
wf "${T}" resume "${work_id}" --phase plan >/dev/null
if wf "${T}" advance --to code >/dev/null 2>"${WORK}/advance-to-err.txt"; then
  bad "advance --to code should refuse when Blocked"
else
  if grep -q "not Ready For Coding" "${WORK}/advance-to-err.txt"; then
    ok "advance --to code refuses when Blocked"
  else
    bad "missing readiness error: $(cat "${WORK}/advance-to-err.txt")"
  fi
fi
phase="$(grep '^phase=' "${T}/.sdlc/workflows/${work_id}.state" | cut -d= -f2)"
if [[ "${phase}" == "plan" ]]; then ok "phase stays plan after refused --to code"; else bad "expected plan, got ${phase}"; fi

# Ready For Coding Metadata passes architect_review on sync (no analysis file required)
T="${WORK}/gate-meta"
work_id="FEAT-012j-gate"
setup_feature "${T}" "${work_id}"
cat > "${T}/spdd/canvas/${work_id}.md" <<'EOF'
# REASONS Canvas: FEAT-012j-gate

## Metadata
- Work ID: FEAT-012j-gate
- Readiness: Ready For Coding

## O - Operations
### T01 - First
- Status: Not Started
EOF
wf "${T}" resume "${work_id}" --phase architect >/dev/null
wf "${T}" sync "${work_id}" >/dev/null
gate="$(grep '^gate_architect_review=' "${T}/.sdlc/workflows/${work_id}.state" | cut -d= -f2 || true)"
if [[ "${gate}" == "passed" ]]; then
  ok "sync passes architect_review from Metadata Ready For Coding"
else
  bad "expected architect_review=passed, got '${gate}'"
fi
gate_c="$(grep '^gate_canvas_exists=' "${T}/.sdlc/workflows/${work_id}.state" | cut -d= -f2 || true)"
if [[ "${gate_c}" == "passed" ]]; then
  ok "sync passes canvas_exists without analysis artifact"
else
  bad "expected canvas_exists=passed without analysis, got '${gate_c}'"
fi

# ---------------------------------------------------------------------------
echo "== Test 13: capture wrapper guards pointer =="
T="${WORK}/capture-guard"
work_id="FEAT-008-cap"
setup_feature "${T}" "${work_id}"
mkdir -p "${T}/scripts/sdlc-spdd/lib"
cp "${REPO_ROOT}/scripts/sdlc.sh" "${T}/scripts/sdlc-spdd/sdlc.sh"
cp "${CAPTURE}" "${T}/scripts/sdlc-spdd/capture-session-memory.sh"
# capture-session-memory.sh sources scripts/sdlc-spdd/lib/*.sh (FEAT-001)
cp "${REPO_ROOT}/scripts/lib/"*.sh "${T}/scripts/sdlc-spdd/lib/"
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
echo "== Test 14: team registry claim and conflict =="
T="${WORK}/team"
work_id="FEAT-009-team"
setup_feature "${T}" "${work_id}"
SDLC_USER="alice" SDLC_ROOT="${T}" wf "${T}" claim "${work_id}" >/dev/null
if registry_matches "${T}" "${work_id}" '"status": "active"'; then
  ok "claim writes team registry"
else
  bad "team registry missing active row"
fi
if SDLC_USER="bob" SDLC_ROOT="${T}" wf "${T}" resume "${work_id}" >/dev/null 2>&1; then
  bad "resume should refuse another owner claim"
else
  ok "resume refuses conflicting team claim"
fi
if SDLC_USER="bob" SDLC_ROOT="${T}" wf "${T}" resume "${work_id}" --force >/dev/null; then
  ok "resume --force allows takeover"
else
  bad "resume --force should succeed"
fi

# ---------------------------------------------------------------------------
echo "== Test 14b: claim --force takes over foreign claim =="
T="${WORK}/team-claim-force"
work_id="FEAT-009b-force"
setup_feature "${T}" "${work_id}"
mkdir -p "${T}/scripts/sdlc-spdd"
cp "${REPO_ROOT}/scripts/sdlc.sh" "${T}/scripts/sdlc-spdd/sdlc.sh"
chmod +x "${T}/scripts/sdlc-spdd/sdlc.sh"
SDLC_USER="alice" SDLC_ROOT="${T}" wf "${T}" claim "${work_id}" >/dev/null
if SDLC_USER="bob" SDLC_ROOT="${T}" "${T}/scripts/sdlc-spdd/sdlc.sh" claim "${work_id}" >/dev/null 2>&1; then
  bad "claim without --force should refuse foreign owner"
else
  ok "claim without --force refuses foreign owner"
fi
if SDLC_USER="bob" SDLC_ROOT="${T}" "${T}/scripts/sdlc-spdd/sdlc.sh" claim "${work_id}" --force >"${T}/claim-force.out" 2>"${T}/claim-force.err"; then
  if registry_matches "${T}" "${work_id}" '"status": "active".*"owner": "bob"'; then
    ok "claim --force takes over via sdlc.sh wrapper"
  else
    bad "claim --force succeeded but owner not bob"
  fi
  takeover_count="$(grep -c 'Taking over' "${T}/claim-force.err" || true)"
  if [[ "${takeover_count}" -eq 1 ]]; then
    ok "claim --force prints Taking over once"
  else
    bad "claim --force Taking over count=${takeover_count} (want 1)"
  fi
else
  bad "claim --force should succeed"
fi

# ---------------------------------------------------------------------------
echo "== Test 15: list-work discovers repo Work IDs =="
T="${WORK}/team"
work_id="FEAT-009-team"
# reuse team fixture from Test 14 (bob owns after --force resume)
out="$(SDLC_ROOT="${T}" wf "${T}" list-work)"
if grep -q 'FEAT-009-team' <<< "${out}"; then ok "list-work shows work id"; else bad "list-work missing id"; fi

# ---------------------------------------------------------------------------
echo "== Test 16: stale claim flagged in team output =="
T="${WORK}/stale"
work_id="FEAT-010-stale"
setup_feature "${T}" "${work_id}"
printf '%s\n' \
  '{"event":"claim","work_id":"FEAT-010-stale","status":"active","phase":"code","operation":"","owner":"alice","note":"","ts":"2020-01-01T00:00:00Z"}' \
  > "${T}/spdd/memory/registry.jsonl"
out="$(SDLC_TEAM_STALE_DAYS=0 SDLC_ROOT="${T}" wf "${T}" team)"
if grep -q 'STALE' <<< "${out}"; then ok "stale claim flagged"; else bad "stale flag missing"; fi

# ---------------------------------------------------------------------------
echo "== Test 17: done status from canvas Final Status =="
T="${WORK}/done"
work_id="CHORE-001-done"
setup_feature "${T}" "${work_id}"
cp "${REPO_ROOT}/spdd/canvas/CHORE-001-docgen-initial-documentation.md" "${T}/spdd/canvas/${work_id}.md"
SDLC_ROOT="${T}" wf "${T}" sync-team >/dev/null
if registry_matches "${T}" "CHORE-001-done" '"status": "done"'; then
  ok "sync-team marks canvas complete as done"
else
  bad "done status not written"
fi

# ---------------------------------------------------------------------------
echo "== Test 18: claim records branch and pr note tokens =="
T="${WORK}/notes"
work_id="FEAT-011-notes"
setup_feature "${T}" "${work_id}"
SDLC_USER="dev1" SDLC_ROOT="${T}" wf "${T}" claim "${work_id}" --branch "cursor/feat-011" --pr "#99" >/dev/null
if registry_matches "${T}" "${work_id}" 'branch:cursor/feat-011' \
  && registry_matches "${T}" "${work_id}" 'pr:#99'; then
  ok "claim stores branch and pr note tokens"
else
  bad "branch/pr tokens missing from registry"
fi

# ---------------------------------------------------------------------------
echo "== Test 19: registry hook fires on claim =="
T="${WORK}/hook"
work_id="FEAT-012-hook"
setup_feature "${T}" "${work_id}"
hook_log="${T}/hook.log"
mkdir -p "${T}/agent-context/hooks"
cat > "${T}/agent-context/hooks/notify.sh" <<EOF
#!/usr/bin/env bash
echo "\$*" >> "${hook_log}"
EOF
chmod +x "${T}/agent-context/hooks/notify.sh"
SDLC_TEAM_REGISTRY_HOOK="${T}/agent-context/hooks/notify.sh" \
  SDLC_USER="hooker" SDLC_ROOT="${T}" wf "${T}" claim "${work_id}" >/dev/null
if [[ -f "${hook_log}" ]] && grep -q 'FEAT-012-hook' "${hook_log}"; then
  ok "registry hook invoked"
else
  bad "registry hook not invoked"
fi

# ---------------------------------------------------------------------------
echo "== Test 20: claim auto-reads jira Key from milestone requirement =="
T="${WORK}/milestone-jira"
work_id="FEAT-013-jira"
setup_feature "${T}" "${work_id}"
mkdir -p "${T}/requirements/milestones"
cat > "${T}/requirements/milestones/${work_id}.md" <<'EOF'
# Requirement: FEAT-013-jira

## Jira

- Key: ORCH-42
- Summary: test issue
EOF
SDLC_USER="dev2" SDLC_ROOT="${T}" wf "${T}" claim "${work_id}" >/dev/null
if registry_matches "${T}" "${work_id}" 'jira:ORCH-42'; then
  ok "claim auto-reads jira key from milestone"
else
  bad "milestone jira key not in registry"
fi
out="$(SDLC_ROOT="${T}" wf "${T}" list-work)"
if grep -q 'jira:ORCH-42' <<< "${out}"; then
  ok "list-work shows milestone jira key"
else
  bad "list-work missing jira key"
fi

# ---------------------------------------------------------------------------
echo "== Test 21: agent-driven Jira ask on missing / draft / present =="
T="${WORK}/jira-ask-missing"
work_id="FEAT-014-jira-ask"
setup_feature "${T}" "${work_id}"
wf "${T}" resume "${work_id}" >/dev/null
out="$(SDLC_ROOT="${T}" wf "${T}" next)"
if grep -q 'Jira: missing' <<< "${out}" && grep -q 'Tracker follow-up:' <<< "${out}" \
  && grep -q 'Ask the user for the issue key' <<< "${out}"; then
  ok "next asks when Jira missing"
else
  bad "next should ask when Jira missing"
fi
"${START}" --target "${T}" --work-id "${work_id}" --phase plan >/dev/null
current="${T}/.sdlc/sessions/current-session.md"
if grep -q '^- Jira: missing$' "${current}" \
  && grep -A20 '## Resume Prompt' "${current}" | grep -q 'Tracker link: Jira key is missing'; then
  ok "session brief Resume Prompt asks when Jira missing"
else
  bad "session brief should ask when Jira missing"
fi

T="${WORK}/jira-ask-draft"
work_id="FEAT-015-jira-draft"
setup_feature "${T}" "${work_id}"
mkdir -p "${T}/requirements/milestones"
cat > "${T}/requirements/milestones/${work_id}.md" <<'EOF'
# Requirement: FEAT-015-jira-draft

## Jira

- Summary: draft without key yet
EOF
wf "${T}" resume "${work_id}" >/dev/null
out="$(SDLC_ROOT="${T}" wf "${T}" next)"
if grep -q 'Jira: draft' <<< "${out}" && grep -q 'Jira draft exists' <<< "${out}"; then
  ok "next asks when Jira draft"
else
  bad "next should ask when Jira draft"
fi
"${START}" --target "${T}" --work-id "${work_id}" --phase plan >/dev/null
current="${T}/.sdlc/sessions/current-session.md"
if grep -A20 '## Resume Prompt' "${current}" | grep -q 'Jira draft exists'; then
  ok "session brief asks when Jira draft"
else
  bad "session brief should ask when Jira draft"
fi

T="${WORK}/jira-ask-present"
work_id="FEAT-016-jira-present"
setup_feature "${T}" "${work_id}"
mkdir -p "${T}/requirements/milestones"
cat > "${T}/requirements/milestones/${work_id}.md" <<'EOF'
# Requirement: FEAT-016-jira-present

## Jira

- Key: ORCH-99
EOF
wf "${T}" resume "${work_id}" >/dev/null
out="$(SDLC_ROOT="${T}" wf "${T}" next)"
if grep -q 'Jira: ORCH-99' <<< "${out}" && ! grep -q 'Tracker follow-up:' <<< "${out}"; then
  ok "next shows key and skips ask when present"
else
  bad "next should not ask when Jira key present"
fi
"${START}" --target "${T}" --work-id "${work_id}" --phase plan >/dev/null
current="${T}/.sdlc/sessions/current-session.md"
if grep -q '^- Jira: ORCH-99$' "${current}" \
  && grep -A20 '## Resume Prompt' "${current}" | grep -q 'Jira: ORCH-99' \
  && ! grep -A20 '## Resume Prompt' "${current}" | grep -q 'Ask the user for the issue key'; then
  ok "session brief records key without ask"
else
  bad "session brief should record key without ask"
fi

T="${WORK}/jira-ask-disabled"
work_id="FEAT-017-jira-off"
setup_feature "${T}" "${work_id}"
wf "${T}" resume "${work_id}" >/dev/null
out="$(SDLC_SESSION_ASK_JIRA=0 SDLC_ROOT="${T}" wf "${T}" next)"
if grep -q 'Jira: missing' <<< "${out}" && ! grep -q 'Tracker follow-up:' <<< "${out}"; then
  ok "SDLC_SESSION_ASK_JIRA=0 suppresses ask"
else
  bad "SDLC_SESSION_ASK_JIRA=0 should suppress ask"
fi
SDLC_SESSION_ASK_JIRA=0 "${START}" --target "${T}" --work-id "${work_id}" --phase plan >/dev/null
current="${T}/.sdlc/sessions/current-session.md"
if ! grep -A20 '## Resume Prompt' "${current}" | grep -q 'Ask the user for the issue key'; then
  ok "start respects SDLC_SESSION_ASK_JIRA=0"
else
  bad "start should honor SDLC_SESSION_ASK_JIRA=0"
fi

# ---------------------------------------------------------------------------
echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
