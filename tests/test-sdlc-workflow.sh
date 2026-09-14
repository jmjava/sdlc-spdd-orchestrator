#!/usr/bin/env bash
# Workflow-state contract for the Python engine (storage v3, one engine):
#   claim -> next -> advance -> skip -> shelf -> resume -> gate
# Asserts on sdlc-spdd/.sdlc/workflows/<WID>.state / .history, on
# `status --json`, and on the team registry at sdlc-spdd/spdd/memory/registry.jsonl.
#
# Shell gate fallback (SDLC_GATE_ENGINE=shell) removed in REF-003; there is one engine.
#
# Usage: ./tests/test-sdlc-workflow.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/harness.sh
source "${SCRIPT_DIR}/lib/harness.sh"

START="${HARNESS_REPO_ROOT}/scripts/start-agent-session.sh"
EXAMPLE_CANVAS="${HARNESS_REPO_ROOT}/examples/spring-boot-order-api/spdd/canvas/FEAT-001-order-status-api.md"

# All fixture targets are created under one WORK root so a single trap cleans up.
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

new_target() {
  TMPDIR="${WORK}" harness_new_target
}

state_file()   { printf '%s' "$(harness_home "$1")/.sdlc/workflows/$2.state"; }
history_file() { printf '%s' "$(harness_home "$1")/.sdlc/workflows/$2.history"; }
registry_file() { printf '%s' "$(harness_home "$1")/spdd/memory/registry.jsonl"; }

state_val() {
  local t="$1" work_id="$2" key="$3"
  grep "^${key}=" "$(state_file "${t}" "${work_id}")" | head -1 | cut -d= -f2- || true
}

pointer_of() { harness_sdlc "$1" pointer get; }

# Latest registry event for a Work ID must match the regex.
registry_matches() {
  local t="$1" work_id="$2" regex="$3"
  local reg
  reg="$(registry_file "${t}")"
  [[ -f "${reg}" ]] && grep "\"work_id\": \"${work_id}\"" "${reg}" | tail -1 | grep -Eq "${regex}"
}

# Canvas with structured Readiness and one T01 op (Files mapping present so the
# code gate's semantic minima are satisfied when readiness allows coding).
write_canvas() {
  local t="$1" work_id="$2" readiness="$3" op_status="${4:-Not Started}"
  harness_seed_work "${t}" "${work_id}"
  local readiness_line=""
  if [[ -n "${readiness}" ]]; then
    readiness_line="- Readiness: ${readiness}"
  fi
  cat > "$(harness_home "${t}")/spdd/canvas/${work_id}.md" <<EOF
# REASONS Canvas: ${work_id}

## Metadata

- Work ID: ${work_id}
- Status: In Progress
${readiness_line}

## R - Requirements

- Harness requirement for ${work_id}.

## O - Operations

### T01 - First

- Status: ${op_status}
- Files: src/first.py

## Final Status

- Status:
EOF
}

# ---------------------------------------------------------------------------
echo "== Test 1: claim sets pointer and creates workflow state + history =="
T="$(new_target)"
W="FEAT-001-alpha"
harness_seed_work "${T}" "${W}"
SDLC_USER="alice" harness_sdlc "${T}" claim "${W}" >/dev/null
[[ "$(pointer_of "${T}")" == "${W}" ]] && ok "claim sets pointer" || bad "pointer not set by claim"
[[ -f "$(state_file "${T}" "${W}")" ]] && ok "workflow .state created under sdlc-spdd/.sdlc/workflows" || bad "missing state file"
[[ -f "$(history_file "${T}" "${W}")" ]] && ok "workflow .history created" || bad "missing history file"
grep -q $'\tcreate\twork_id='"${W}" "$(history_file "${T}" "${W}")" && ok "history records create" || bad "history missing create"
grep -q $'\tresume\tphase=' "$(history_file "${T}" "${W}")" && ok "history records resume" || bad "history missing resume"
[[ "$(state_val "${T}" "${W}" work_id)" == "${W}" ]] && ok "state work_id" || bad "state work_id wrong"
[[ "$(state_val "${T}" "${W}" active)" == "1" ]] && ok "state active=1 after claim" || bad "expected active=1"
[[ "$(state_val "${T}" "${W}" phase)" == "architect" ]] && ok "canvas-only work infers architect" || bad "expected architect, got $(state_val "${T}" "${W}" phase)"
[[ "$(state_val "${T}" "${W}" gate_canvas_exists)" == "passed" ]] && ok "gate_canvas_exists=passed" || bad "canvas gate not passed"
[[ "$(state_val "${T}" "${W}" gate_requirement_documented)" == "passed" ]] && ok "gate_requirement_documented=passed" || bad "requirement gate not passed"
[[ ! -d "${T}/.sdlc" ]] && ok "no legacy root .sdlc created" || bad "legacy root .sdlc created"
registry_matches "${T}" "${W}" '"status": "active".*"owner": "alice"' && ok "claim writes team registry (active, alice)" || bad "registry row missing"

# ---------------------------------------------------------------------------
echo "== Test 2: next is actionable and re-syncs state =="
out="$(harness_sdlc "${T}" next)"
grep -q "Work ID: ${W}" <<< "${out}" && ok "next names the Work ID" || bad "next missing Work ID"
grep -q 'Do now (assistant):' <<< "${out}" && ok "next has Do now section" || bad "next missing Do now"
grep -q 'When this phase is done:' <<< "${out}" && ok "next has phase-done section" || bad "next missing phase-done"
grep -q 'sdlc-spdd-architect' <<< "${out}" && ok "next recommends architect at architect phase" || bad "next should recommend architect"
grep -q '(moves to: code)' <<< "${out}" && ok "next names the following phase" || bad "next missing moves-to"

# ---------------------------------------------------------------------------
echo "== Test 3: advance architect->code is gated on canvas readiness =="
rc=0
harness_sdlc "${T}" advance >/dev/null 2>"${T}/advance.err" || rc=$?
[[ "${rc}" -ne 0 ]] && ok "advance refused for non-ready canvas (rc=${rc})" || bad "advance should fail on non-ready canvas"
grep -q "not Ready For Coding" "${T}/advance.err" && ok "advance error names readiness" || bad "advance error missing readiness: $(cat "${T}/advance.err")"
grep -q "missing structured Readiness field" "${T}/advance.err" && ok "absent readiness is reported (no compat pass-through)" || bad "expected missing-readiness message"
[[ "$(state_val "${T}" "${W}" phase)" == "architect" ]] && ok "phase stays architect after refusal" || bad "phase changed after refused advance"

write_canvas "${T}" "${W}" "Ready For Coding"
harness_sdlc "${T}" advance >/dev/null && ok "advance succeeds once Ready For Coding" || bad "advance should succeed when ready"
[[ "$(state_val "${T}" "${W}" phase)" == "code" ]] && ok "phase=code after advance" || bad "expected code, got $(state_val "${T}" "${W}" phase)"
grep -q $'\tadvance\tphase=code' "$(history_file "${T}" "${W}")" && ok "history records advance" || bad "history missing advance"
harness_sdlc "${T}" sync >/dev/null
[[ "$(state_val "${T}" "${W}" phase)" == "code" ]] && ok "sync keeps code for Ready For Coding canvas" || bad "sync moved phase to $(state_val "${T}" "${W}" phase)"
[[ "$(state_val "${T}" "${W}" operation)" == "T01" ]] && ok "sync infers operation T01 from canvas" || bad "expected operation T01"

# ---------------------------------------------------------------------------
echo "== Test 4: skip records reason and moves past the phase =="
out="$(harness_sdlc "${T}" skip api-test --reason "no HTTP surface")"
grep -q 'Skipped api-test; now at review' <<< "${out}" && ok "skip reports new phase" || bad "skip output: ${out}"
[[ "$(state_val "${T}" "${W}" skip_api-test)" == "no HTTP surface" ]] && ok "skip reason recorded in state" || bad "skip not recorded"
[[ "$(state_val "${T}" "${W}" phase)" == "review" ]] && ok "skip moved phase to review" || bad "expected review"
grep -q $'\tskip\tphase=api-test reason=no HTTP surface' "$(history_file "${T}" "${W}")" && ok "history records skip" || bad "history missing skip"

# ---------------------------------------------------------------------------
echo "== Test 5: shelf clears pointer; resume restores; auto-shelf on switch =="
harness_sdlc "${T}" shelf --reason "context switch" >/dev/null
[[ -z "$(pointer_of "${T}")" ]] && ok "shelf clears pointer" || bad "pointer should be empty"
[[ "$(state_val "${T}" "${W}" active)" == "0" ]] && ok "shelf marks active=0" || bad "expected active=0"
[[ "$(state_val "${T}" "${W}" shelved_reason)" == "context switch" ]] && ok "shelf stores reason" || bad "shelved_reason wrong"
[[ -n "$(state_val "${T}" "${W}" shelved_at)" ]] && ok "shelf stamps shelved_at" || bad "shelved_at empty"
grep -q $'\tshelf\tcontext switch' "$(history_file "${T}" "${W}")" && ok "history records shelf" || bad "history missing shelf"
harness_sdlc "${T}" list-shelved | grep -q "^${W}"$'\t' && ok "list-shelved includes parked work" || bad "list-shelved missing ${W}"

rc=0
harness_sdlc "${T}" shelf >/dev/null 2>&1 || rc=$?
[[ "${rc}" -ne 0 ]] && ok "shelf with no pointer exits non-zero" || bad "shelf without pointer should fail"

W2="CHORE-002-beta"
harness_seed_work "${T}" "${W2}"
harness_sdlc "${T}" resume "${W2}" >/dev/null
[[ "$(pointer_of "${T}")" == "${W2}" ]] && ok "resume of second work sets pointer" || bad "pointer not ${W2}"
harness_sdlc "${T}" resume "${W}" >/dev/null
[[ "$(pointer_of "${T}")" == "${W}" ]] && ok "resume restores shelved pointer" || bad "resume failed"
[[ "$(state_val "${T}" "${W}" active)" == "1" ]] && ok "resume sets active=1" || bad "expected active=1"
[[ -z "$(state_val "${T}" "${W}" shelved_reason)" ]] && ok "resume clears shelved_reason" || bad "shelved_reason not cleared"
[[ "$(state_val "${T}" "${W2}" active)" == "0" ]] && ok "switching work auto-shelves previous" || bad "${W2} should be auto-shelved"
[[ "$(state_val "${T}" "${W2}" shelved_reason)" == "auto-shelf for resume ${W}" ]] && ok "auto-shelf reason recorded" || bad "auto-shelf reason: '$(state_val "${T}" "${W2}" shelved_reason)'"
harness_sdlc "${T}" list-shelved | grep -q "^${W2}"$'\t' && ok "list-shelved shows auto-shelved work" || bad "list-shelved missing ${W2}"

# ---------------------------------------------------------------------------
echo "== Test 6: sync infers phase from artifacts =="
T="$(new_target)"
W="FEAT-003-gamma"
H="$(harness_home "${T}")"
mkdir -p "${H}/requirements/milestones" "${H}/spdd/analysis" "${H}/spdd/canvas"
printf '# Requirement: %s\n' "${W}" > "${H}/requirements/milestones/${W}.md"
harness_sdlc "${T}" resume "${W}" >/dev/null
[[ "$(state_val "${T}" "${W}" phase)" == "analysis" ]] && ok "requirement only -> analysis" || bad "expected analysis, got $(state_val "${T}" "${W}" phase)"
printf '# analysis\n' > "${H}/spdd/analysis/${W}-analysis.md"
harness_sdlc "${T}" sync >/dev/null
[[ "$(state_val "${T}" "${W}" phase)" == "plan" ]] && ok "+analysis -> plan" || bad "expected plan"
write_canvas "${T}" "${W}" "Needs Analysis"
harness_sdlc "${T}" sync >/dev/null
[[ "$(state_val "${T}" "${W}" phase)" == "architect" ]] && ok "+canvas (not ready) -> architect" || bad "expected architect"
write_canvas "${T}" "${W}" "Ready For Coding"
out="$(harness_sdlc "${T}" sync --work-id "${W}")"
grep -q "Synced ${W} -> phase code" <<< "${out}" && ok "sync --work-id reports code" || bad "sync output: ${out}"
[[ "$(state_val "${T}" "${W}" phase)" == "code" ]] && ok "Ready For Coding canvas -> code" || bad "expected code"
[[ "$(state_val "${T}" "${W}" gate_canvas_exists)" == "passed" ]] && ok "sync marks canvas gate passed" || bad "canvas gate not passed"
[[ "$(state_val "${T}" "${W}" gate_requirement_documented)" == "passed" ]] && ok "sync marks requirement gate passed" || bad "requirement gate not passed"
grep -q $'\tsync\tphase=code' "$(history_file "${T}" "${W}")" && ok "history records sync" || bad "history missing sync"

# ---------------------------------------------------------------------------
echo "== Test 7: status is human-readable; status --json for agents =="
out="$(harness_sdlc "${T}" status)"
grep -q "^Pointer: ${W}" <<< "${out}" && ok "status shows pointer" || bad "status missing Pointer"
grep -q "^Work ID: ${W}" <<< "${out}" && ok "status shows Work ID" || bad "status missing Work ID"
json="$(harness_sdlc "${T}" status --json | tr -d ' \n')"
grep -q "\"pointer\":\"${W}\"" <<< "${json}" && ok "json pointer" || bad "json pointer missing"
grep -q "\"work_id\":\"${W}\"" <<< "${json}" && ok "json work_id" || bad "json work_id missing"
grep -q '"phase":"code"' <<< "${json}" && ok "json phase=code" || bad "json phase wrong: ${json}"
grep -q '"operation":"T01"' <<< "${json}" && ok "json operation=T01" || bad "json operation missing"
grep -q '"operation_title":"First"' <<< "${json}" && ok "json operation_title" || bad "json operation_title missing"
grep -q '"active":true' <<< "${json}" && ok "json active=true" || bad "json active missing"
grep -q '"recommended_command":"/sdlc-spdd-code' <<< "${json}" && ok "json recommended_command is code" || bad "json recommended_command wrong"
grep -q '"gates":{' <<< "${json}" && grep -q '"canvas_exists":"passed"' <<< "${json}" && ok "json gates include canvas_exists=passed" || bad "json gates incomplete"
grep -q '"phases":\["init","analysis","plan","architect","code","api-test","review","prompt-update","retro","sync"\]' <<< "${json}" && ok "json lists phase track" || bad "json phases wrong"
json_other="$(harness_sdlc "${T}" status --json --work-id "${W}" | tr -d ' \n')"
grep -q '"phase":"code"' <<< "${json_other}" && ok "status --json --work-id works" || bad "status --work-id failed"

# ---------------------------------------------------------------------------
echo "== Test 8: status --json / next without a pointer =="
harness_sdlc "${T}" shelf --reason park >/dev/null
json="$(harness_sdlc "${T}" status --json | tr -d ' \n')"
grep -q '"pointer":""' <<< "${json}" && grep -q '"work_id":null' <<< "${json}" && ok "json shows empty pointer / null work_id" || bad "json without pointer: ${json}"
out="$(harness_sdlc "${T}" next)"
grep -q 'No active Work ID pointer' <<< "${out}" && ok "next explains missing pointer" || bad "next without pointer: ${out}"
grep -q 'list-shelved' <<< "${out}" && ok "next hints at list-shelved when work is parked" || bad "next missing list-shelved hint"
rc=0
harness_sdlc "${T}" advance >/dev/null 2>&1 || rc=$?
[[ "${rc}" -ne 0 ]] && ok "advance without pointer exits non-zero" || bad "advance without pointer should fail"
rc=0
harness_sdlc "${T}" gate --phase code >/dev/null 2>&1 || rc=$?
[[ "${rc}" -eq 2 ]] && ok "gate without pointer exits 2" || bad "gate without pointer rc=${rc}"
harness_sdlc "${T}" resume "${W}" >/dev/null

# ---------------------------------------------------------------------------
echo "== Test 9: gate --phase reports OK / BLOCKED with --json =="
out="$(harness_sdlc "${T}" gate --phase code)"
grep -q "gate code: OK for ${W}" <<< "${out}" && ok "gate code OK for ready canvas" || bad "gate output: ${out}"
json="$(harness_sdlc "${T}" gate --phase code --json | tr -d ' \n')"
grep -q '"ok":true' <<< "${json}" && grep -q '"failures":\[\]' <<< "${json}" && ok "gate --json ok=true, no failures" || bad "gate json: ${json}"
grep -q '"advisory":\[{"gate":"architect_review"' <<< "${json}" && ok "gate --json lists advisory gates" || bad "gate json advisory missing"
write_canvas "${T}" "${W}" "Needs Clarification"
rc=0
harness_sdlc "${T}" gate --phase code >"${T}/gate.out" 2>"${T}/gate.err" || rc=$?
[[ "${rc}" -eq 1 ]] && ok "gate exits 1 when blocked" || bad "gate rc=${rc} when blocked"
grep -q "gate code: BLOCKED for ${W}" "${T}/gate.err" && ok "gate prints BLOCKED to stderr" || bad "gate BLOCKED missing"
grep -q "readiness is needs-clarification, not Ready For Coding" "${T}/gate.err" && ok "gate names the readiness failure" || bad "gate failure text: $(cat "${T}/gate.err")"
rc=0
json="$(harness_sdlc "${T}" gate --phase code --json | tr -d ' \n')" || rc=$?
grep -q '"ok":false' <<< "${json}" && ok "gate --json ok=false when blocked" || bad "gate json blocked: ${json}"
json="$(harness_sdlc "${T}" gate --phase review --json --work-id "${W}" | tr -d ' \n' || true)"
grep -q 'noledgerevidence' <<< "${json}" && ok "gate review requires ledger evidence" || bad "gate review json: ${json}"

# ---------------------------------------------------------------------------
echo "== Test 10: session scripts update workflow timestamps + stage captures =="
T="$(new_target)"
W="FEAT-004-delta"
H="$(harness_home "${T}")"
write_canvas "${T}" "${W}" "Ready For Coding"
"${START}" --target "${T}" --work-id "${W}" --phase plan >/dev/null
[[ -n "$(state_val "${T}" "${W}" last_session_at)" ]] && ok "start-agent-session stamps last_session_at" || bad "missing last_session_at"
[[ "$(pointer_of "${T}")" == "${W}" ]] && ok "start-agent-session sets pointer" || bad "pointer not set"
[[ -f "${H}/.sdlc/sessions/current-session.md" ]] && ok "session brief written under sdlc-spdd/.sdlc/sessions" || bad "missing current-session.md"
grep -q '## Workflow State' "${H}/.sdlc/sessions/current-session.md" \
  && grep -q 'Assistant command' "${H}/.sdlc/sessions/current-session.md" \
  && ok "session brief embeds workflow state" || bad "session brief missing workflow state"
"${H}/scripts/capture-session-memory.sh" --target "${T}" --work-id "${W}" --phase plan --summary "planned" >/dev/null
[[ -n "$(state_val "${T}" "${W}" last_capture_at)" ]] && ok "capture-session-memory stamps last_capture_at" || bad "missing last_capture_at"
[[ -s "${H}/.sdlc/staged/lessons.jsonl" ]] && ok "capture stages into sdlc-spdd/.sdlc/staged/lessons.jsonl" || bad "staged ledger empty"
grep -q "\"work_id\": \"${W}\"" "${H}/.sdlc/staged/lessons.jsonl" && ok "staged record carries work_id" || bad "staged record lacks work_id"
[[ ! -f "${T}/.sdlc/staged/lessons.jsonl" ]] && ok "no legacy root staged ledger" || bad "legacy root staged ledger written"
brief="$(harness_sdlc "${T}" session brief)"
grep -q "| Work ID | ${W} |" <<< "${brief}" && grep -q '| Readiness | ready-for-coding |' <<< "${brief}" \
  && ok "session brief has Work ID + Readiness rows" || bad "session brief: ${brief}"

# ---------------------------------------------------------------------------
echo "== Test 11: capture is guarded by the pointer =="
# The Ready For Coding canvas re-syncs the phase to code, where a verify
# receipt is mandatory; pin --phase plan for the plain guarded-capture case.
harness_sdlc "${T}" capture --phase plan --summary "ok" >/dev/null 2>&1 && ok "capture succeeds when pointer matches" || bad "capture should succeed for active pointer"
rc=0
# Engine prints the mismatch on stdout, so capture both streams.
harness_sdlc "${T}" capture --phase plan --work-id FEAT-999-other --summary "bad" >"${T}/cap.err" 2>&1 || rc=$?
[[ "${rc}" -eq 3 ]] && ok "capture refuses stale work-id (rc=3)" || bad "capture mismatch rc=${rc}"
grep -q "does not match pointer" "${T}/cap.err" && ok "capture mismatch names the pointer" || bad "capture error: $(cat "${T}/cap.err")"
[[ "$(grep -c '"work_id"' "${H}/.sdlc/staged/lessons.jsonl")" -eq 2 ]] && ok "refused capture staged nothing" || bad "staged count changed on refused capture"

# ---------------------------------------------------------------------------
echo "== Test 12: code capture / complete without verify receipt refuse =="
harness_sdlc "${T}" resume "${W}" --phase code >/dev/null
rc=0
harness_sdlc "${T}" capture --phase code --summary "T01 complete" >/dev/null 2>"${T}/receipt.err" || rc=$?
[[ "${rc}" -ne 0 ]] && ok "code capture without receipt refuses" || bad "code capture without receipt should refuse"
grep -q "verify receipt required" "${T}/receipt.err" && ok "capture names the receipt requirement" || bad "capture error: $(cat "${T}/receipt.err")"
rc=0
# complete prints its refusal on stdout; capture both streams.
harness_sdlc "${T}" complete >"${T}/complete.err" 2>&1 || rc=$?
[[ "${rc}" -ne 0 ]] && ok "complete without receipt refuses" || bad "complete without receipt should refuse"
grep -q "verify receipt required" "${T}/complete.err" && ok "complete names the receipt requirement" || bad "complete error: $(cat "${T}/complete.err")"

# ---------------------------------------------------------------------------
echo "== Test 13: infers next canvas operation from REASONS Canvas =="
T="$(new_target)"
W="FEAT-007-ops"
H="$(harness_home "${T}")"
harness_seed_work "${T}" "${W}"
cp "${EXAMPLE_CANVAS}" "${H}/spdd/canvas/${W}.md"
harness_sdlc "${T}" resume "${W}" >/dev/null
harness_sdlc "${T}" sync --work-id "${W}" >/dev/null
[[ "$(state_val "${T}" "${W}" operation)" == "T03" ]] && ok "sync infers next operation T03" || bad "expected T03, got $(state_val "${T}" "${W}" operation)"
out="$(harness_sdlc "${T}" next)"
grep -q 'Next canvas operation: T03' <<< "${out}" && ok "next names T03" || bad "next missing T03"
json="$(harness_sdlc "${T}" status --json | tr -d '\n')"
grep -q '"operation": "T03"' <<< "${json}" && grep -q '"operation_title": "' <<< "${json}" && ok "json includes operation and title" || bad "json missing operation fields"

# ---------------------------------------------------------------------------
echo "== Test 14: all-complete canvas has empty next operation =="
W="FEAT-012b-final"
write_canvas "${T}" "${W}" "Ready For Coding" "Complete"
harness_sdlc "${T}" resume "${W}" --phase code >/dev/null
harness_sdlc "${T}" sync --work-id "${W}" >/dev/null
[[ -z "$(state_val "${T}" "${W}" operation)" ]] && ok "all-complete canvas has empty operation" || bad "expected empty operation, got '$(state_val "${T}" "${W}" operation)'"
out="$(harness_sdlc "${T}" next)"
! grep -q 'Next canvas operation' <<< "${out}" && ok "next omits operation when all complete" || bad "next should not name an operation: ${out}"
json="$(harness_sdlc "${T}" status --json | tr -d ' \n')"
grep -q '"operation":""' <<< "${json}" && ok "json operation empty when all complete" || bad "json operation: ${json}"

# ---------------------------------------------------------------------------
echo "== Test 15: code phase with Needs Analysis redirects to architect =="
W="FEAT-012c-readiness"
write_canvas "${T}" "${W}" "Needs Analysis"
rc=0
harness_sdlc "${T}" resume "${W}" --phase code >/dev/null 2>"${T}/resume.err" || rc=$?
[[ "${rc}" -ne 0 ]] && ok "resume --phase code refused when Needs Analysis" || bad "resume --phase code should refuse"
grep -q "not Ready For Coding" "${T}/resume.err" && ok "resume error names readiness" || bad "resume error: $(cat "${T}/resume.err")"
harness_sdlc "${T}" resume "${W}" --phase code --force >/dev/null && ok "resume --phase code --force overrides" || bad "resume --force should succeed"
[[ "$(state_val "${T}" "${W}" phase)" == "code" ]] && ok "forced phase persisted as code" || bad "expected code after --force"
out="$(harness_sdlc "${T}" next)"
grep -q 'sdlc-spdd-architect' <<< "${out}" && grep -q 'Phase: architect' <<< "${out}" && ok "next re-syncs to architect when readiness blocks coding" || bad "next should recommend architect: ${out}"
json="$(harness_sdlc "${T}" status --json | tr -d ' \n')"
grep -q '"phase":"architect"' <<< "${json}" && grep -q 'sdlc-spdd-architect' <<< "${json}" && ok "json phase + recommended_command reflect gate" || bad "json: ${json}"

# ---------------------------------------------------------------------------
echo "== Test 16: advance to code refused when readiness blocks; --force overrides =="
W="FEAT-012d-advance"
write_canvas "${T}" "${W}" "Needs Clarification"
harness_sdlc "${T}" resume "${W}" --phase architect >/dev/null
rc=0
harness_sdlc "${T}" advance >/dev/null 2>"${T}/adv.err" || rc=$?
[[ "${rc}" -ne 0 ]] && ok "advance architect->code refused when Needs Clarification" || bad "advance should fail"
grep -q "not Ready For Coding" "${T}/adv.err" && ok "advance error names readiness" || bad "advance error: $(cat "${T}/adv.err")"
grep -q "pass --force (a human decision" "${T}/adv.err" && ok "advance error explains --force is a human decision" || bad "advance error lacks --force hint"
[[ "$(state_val "${T}" "${W}" phase)" == "architect" ]] && ok "phase stays architect after refusal" || bad "expected architect"
! grep -q $'\tadvance\t' "$(history_file "${T}" "${W}")" && ok "refused advance leaves no history entry" || bad "history has advance despite refusal"
harness_sdlc "${T}" advance --force >/dev/null && ok "advance --force overrides readiness gate" || bad "advance --force should succeed"
[[ "$(state_val "${T}" "${W}" phase)" == "code" ]] && ok "force advance reaches code" || bad "expected code after --force"
grep -q $'\tadvance\tphase=code' "$(history_file "${T}" "${W}")" && ok "history records forced advance" || bad "history missing forced advance"

# ---------------------------------------------------------------------------
echo "== Test 17: advance to code succeeds when Ready For Coding =="
W="FEAT-012f-ok"
write_canvas "${T}" "${W}" "Ready For Coding"
harness_sdlc "${T}" resume "${W}" --phase architect >/dev/null
harness_sdlc "${T}" advance >/dev/null && ok "advance architect->code when Ready For Coding" || bad "advance should succeed when ready"
[[ "$(state_val "${T}" "${W}" phase)" == "code" ]] && ok "phase is code after ready advance" || bad "expected code"
out="$(harness_sdlc "${T}" next)"
grep -q 'sdlc-spdd-code' <<< "${out}" && grep -q 'operation T01' <<< "${out}" && ok "next recommends code operation T01" || bad "next should recommend code: ${out}"

# ---------------------------------------------------------------------------
echo "== Test 18: advance --to code from plan refused when Blocked =="
W="FEAT-012j-to"
write_canvas "${T}" "${W}" "Blocked"
harness_sdlc "${T}" resume "${W}" --phase plan --force >/dev/null
rc=0
harness_sdlc "${T}" advance --to code >/dev/null 2>"${T}/adv-to.err" || rc=$?
[[ "${rc}" -ne 0 ]] && ok "advance --to code refuses when Blocked" || bad "advance --to code should refuse"
grep -q "readiness is blocked, not Ready For Coding" "${T}/adv-to.err" && ok "--to error names blocked readiness" || bad "error: $(cat "${T}/adv-to.err")"
[[ "$(state_val "${T}" "${W}" phase)" == "plan" ]] && ok "phase stays plan after refused --to code" || bad "expected plan"
rc=0
harness_sdlc "${T}" advance --to nowhere >/dev/null 2>&1 || rc=$?
[[ "${rc}" -ne 0 ]] && ok "advance --to unknown phase fails" || bad "unknown phase should fail"

# ---------------------------------------------------------------------------
echo "== Test 19: YAML frontmatter readiness is honored =="
W="FEAT-012h-yaml"
harness_seed_work "${T}" "${W}"
cat > "${H}/spdd/canvas/${W}.md" <<EOF
---
readiness: needs-redesign
---
# REASONS Canvas: ${W}

## Metadata

- Work ID: ${W}

## R - Requirements

- Harness requirement.

## O - Operations

### T01 - First

- Status: Not Started
- Files: src/first.py
EOF
harness_sdlc "${T}" resume "${W}" --phase architect >/dev/null
rc=0
harness_sdlc "${T}" gate --phase code >/dev/null 2>"${T}/yaml.err" || rc=$?
[[ "${rc}" -eq 1 ]] && grep -q "readiness is needs-redesign" "${T}/yaml.err" && ok "gate reads YAML readiness" || bad "gate yaml: $(cat "${T}/yaml.err")"
brief="$(harness_sdlc "${T}" session brief)"
grep -q '| Readiness | needs-redesign |' <<< "${brief}" && ok "brief includes Readiness row from YAML" || bad "brief missing Readiness: ${brief}"
[[ "$(state_val "${T}" "${W}" gate_architect_review)" != "passed" ]] && ok "architect_review not auto-passed for needs-redesign" || bad "architect_review should not be passed"

# ---------------------------------------------------------------------------
echo "== Test 20: team registry claim conflict and --force takeover =="
T="$(new_target)"
W="FEAT-009-team"
harness_seed_work "${T}" "${W}"
SDLC_USER="alice" harness_sdlc "${T}" claim "${W}" >/dev/null
registry_matches "${T}" "${W}" '"status": "active".*"owner": "alice"' && ok "claim writes team registry" || bad "registry missing active row"
rc=0
SDLC_USER="bob" harness_sdlc "${T}" claim "${W}" >/dev/null 2>"${T}/bob.err" || rc=$?
[[ "${rc}" -ne 0 ]] && ok "claim without --force refuses foreign owner" || bad "claim should refuse foreign owner"
grep -q "is active under alice" "${T}/bob.err" && ok "refusal names current owner" || bad "refusal text: $(cat "${T}/bob.err")"
registry_matches "${T}" "${W}" '"owner": "alice"' && ok "refused claim leaves alice as owner" || bad "owner changed despite refusal"
SDLC_USER="bob" harness_sdlc "${T}" claim "${W}" --force >/dev/null && ok "claim --force takes over" || bad "claim --force should succeed"
registry_matches "${T}" "${W}" '"status": "active".*"owner": "bob"' && ok "registry owner is bob after --force" || bad "owner not bob"
[[ "$(grep -c "\"work_id\": \"${W}\"" "$(registry_file "${T}")")" -eq 2 ]] && ok "registry is append-only (2 events)" || bad "registry event count wrong"
team_out="$(harness_sdlc "${T}" team)"
grep -q "${W}" <<< "${team_out}" && grep -q 'bob' <<< "${team_out}" && ok "team view shows bob's claim" || bad "team output: ${team_out}"
list_out="$(harness_sdlc "${T}" list-work)"
grep -q "${W}" <<< "${list_out}" && ok "list-work shows work id" || bad "list-work missing id"

# ---------------------------------------------------------------------------
echo "== Test 21: sync-team marks canvas Complete as done =="
harness_seed_work "${T}" CHORE-001-done Complete
harness_sdlc "${T}" sync-team >/dev/null
registry_matches "${T}" CHORE-001-done '"status": "done"' && ok "sync-team marks canvas complete as done" || bad "done status not written"

# ---------------------------------------------------------------------------
echo "== Test 22: claim records branch / pr / jira note tokens =="
W="FEAT-011-notes"
harness_seed_work "${T}" "${W}"
SDLC_USER="dev1" harness_sdlc "${T}" claim "${W}" --branch "cursor/feat-011" --pr "#99" >/dev/null
registry_matches "${T}" "${W}" 'branch:cursor/feat-011' && registry_matches "${T}" "${W}" 'pr:#99' \
  && ok "claim stores branch and pr note tokens" || bad "branch/pr tokens missing"
W="FEAT-013-jira"
harness_seed_work "${T}" "${W}"
printf '\n## Jira\n\n- Key: ORCH-42\n- Summary: test issue\n' >> "$(harness_home "${T}")/requirements/milestones/${W}.md"
SDLC_USER="dev2" harness_sdlc "${T}" claim "${W}" >/dev/null
registry_matches "${T}" "${W}" 'jira:ORCH-42' && ok "claim auto-reads jira key from milestone" || bad "milestone jira key not in registry"
[[ "$(harness_sdlc "${T}" session jira-status --work-id "${W}")" == "ORCH-42" ]] && ok "session jira-status reports key" || bad "jira-status wrong"
harness_sdlc "${T}" release >/dev/null
[[ -z "$(pointer_of "${T}")" ]] && ok "release clears pointer" || bad "release should clear pointer"

# ---------------------------------------------------------------------------
echo "== Test 23: agent-driven Jira ask on missing / draft / present =="
T="$(new_target)"
H="$(harness_home "${T}")"
W="FEAT-014-jira-missing"
mkdir -p "${H}/spdd/canvas"
printf '# %s\n\n## Final Status\n\n- Status: In Progress\n' "${W}" > "${H}/spdd/canvas/${W}.md"
[[ "$(harness_sdlc "${T}" session jira-status --work-id "${W}")" == "missing" ]] && ok "jira-status missing without requirement" || bad "expected missing"
harness_sdlc "${T}" session jira-ask --work-id "${W}" | grep -q 'Ask the user for the issue key' && ok "jira-ask asks when missing" || bad "jira-ask should ask when missing"
"${START}" --target "${T}" --work-id "${W}" --phase plan >/dev/null
current="${H}/.sdlc/sessions/current-session.md"
grep -q '^- Jira: missing$' "${current}" \
  && grep -A20 '## Resume Prompt' "${current}" | grep -q 'Jira key is missing' \
  && ok "session brief Resume Prompt asks when Jira missing" || bad "brief should ask when Jira missing"

W="FEAT-015-jira-draft"
harness_seed_work "${T}" "${W}"
printf '\n## Jira\n\n- Summary: draft without key yet\n' >> "${H}/requirements/milestones/${W}.md"
[[ "$(harness_sdlc "${T}" session jira-status --work-id "${W}")" == "draft" ]] && ok "jira-status draft without Key" || bad "expected draft"
harness_sdlc "${T}" session jira-ask --work-id "${W}" | grep -q 'Jira draft exists' && ok "jira-ask asks when draft" || bad "jira-ask should ask when draft"
"${START}" --target "${T}" --work-id "${W}" --phase plan >/dev/null
grep -A20 '## Resume Prompt' "${current}" | grep -q 'Jira draft exists' && ok "session brief asks when Jira draft" || bad "brief should ask when draft"

W="FEAT-016-jira-present"
harness_seed_work "${T}" "${W}"
printf '\n## Jira\n\n- Key: ORCH-99\n' >> "${H}/requirements/milestones/${W}.md"
[[ "$(harness_sdlc "${T}" session jira-status --work-id "${W}")" == "ORCH-99" ]] && ok "jira-status returns key when present" || bad "expected ORCH-99"
[[ -z "$(harness_sdlc "${T}" session jira-ask --work-id "${W}")" ]] && ok "jira-ask is silent when key present" || bad "jira-ask should be empty"
"${START}" --target "${T}" --work-id "${W}" --phase plan >/dev/null
grep -q '^- Jira: ORCH-99$' "${current}" \
  && ! grep -A20 '## Resume Prompt' "${current}" | grep -q 'Ask the user for the issue key' \
  && ok "session brief records key without ask" || bad "brief should record key without ask"

W="FEAT-017-jira-off"
harness_seed_work "${T}" "${W}"
[[ -z "$(SDLC_SESSION_ASK_JIRA=0 harness_sdlc "${T}" session jira-ask --work-id "${W}")" ]] && ok "SDLC_SESSION_ASK_JIRA=0 suppresses ask" || bad "SDLC_SESSION_ASK_JIRA=0 should suppress"
SDLC_SESSION_ASK_JIRA=0 "${START}" --target "${T}" --work-id "${W}" --phase plan >/dev/null
! grep -A20 '## Resume Prompt' "${current}" | grep -q 'Ask the user for the issue key' \
  && ok "start respects SDLC_SESSION_ASK_JIRA=0" || bad "start should honor SDLC_SESSION_ASK_JIRA=0"

# ---------------------------------------------------------------------------
echo "== Test 24: installed dispatcher has no bash twins and rejects removed env =="
[[ ! -e "${H}/scripts/sdlc-workflow.sh" && ! -e "${H}/scripts/sdlc-team-registry.sh" && ! -e "${H}/scripts/sdlc-pointer.sh" ]] \
  && ok "no bash workflow twins installed" || bad "retired twin installed"
rc=0
SDLC_GATE_ENGINE=shell "${H}/scripts/sdlc.sh" version >/dev/null 2>"${T}/env.err" || rc=$?
[[ "${rc}" -eq 2 ]] && grep -q "removed" "${T}/env.err" && ok "SDLC_GATE_ENGINE=shell exits 2 (removed)" || bad "SDLC_GATE_ENGINE rc=${rc}: $(cat "${T}/env.err")"

harness_finish
