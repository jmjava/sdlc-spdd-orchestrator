#!/usr/bin/env bash
set -euo pipefail

# Leftover #14 proving test: sdlc.sh gate must show advisory rows that did not run.
# GATE_LABELS append "(advisory)" on next; gate used to print only failures.

export SDLC_ENGINE=shell
export SDLC_GATE_ENGINE=shell

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKFLOW="${REPO_ROOT}/templates/agent-context/sdlc-workflow.sh"
POINTER="${REPO_ROOT}/templates/agent-context/sdlc-pointer.sh"
TEAM_REG="${REPO_ROOT}/templates/agent-context/sdlc-team-registry.sh"
CAPTURE="${REPO_ROOT}/scripts/capture-session-memory.sh"
SDLC_SH="${REPO_ROOT}/scripts/sdlc.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

write_canvas() {
  local t="$1"
  local work_id="$2"
  mkdir -p "${t}/spdd/canvas"
  cat > "${t}/spdd/canvas/${work_id}.md" <<EOF
# REASONS Canvas: ${work_id}

## Metadata
- Work ID: ${work_id}
- Readiness: Ready For Coding

## O - Operations
### T01 - Do the thing
- Files: src/app.py
EOF
}

write_requirement() {
  local t="$1"
  local work_id="$2"
  mkdir -p "${t}/requirements/milestones"
  printf '# Requirement: %s\n' "${work_id}" > "${t}/requirements/milestones/${work_id}.md"
}

setup_feature() {
  local t="$1"
  mkdir -p "${t}/.sdlc/sessions" \
    "${t}/agent-context" \
    "${t}/spdd/canvas" \
    "${t}/spdd/analysis" \
    "${t}/spdd/memory" \
    "${t}/scripts/sdlc-spdd/lib"
  cp "${POINTER}" "${t}/agent-context/sdlc-pointer.sh"
  cp "${WORKFLOW}" "${t}/agent-context/sdlc-workflow.sh"
  cp "${TEAM_REG}" "${t}/agent-context/sdlc-team-registry.sh"
  : > "${t}/spdd/memory/registry.jsonl"
  cp "${SDLC_SH}" "${t}/scripts/sdlc-spdd/sdlc.sh"
  cp "${CAPTURE}" "${t}/scripts/sdlc-spdd/capture-session-memory.sh"
  cp "${REPO_ROOT}/scripts/lib/"*.sh "${t}/scripts/sdlc-spdd/lib/"
  chmod +x "${t}/agent-context/"*.sh \
    "${t}/scripts/sdlc-spdd/sdlc.sh" \
    "${t}/scripts/sdlc-spdd/capture-session-memory.sh"
}

sdlc() {
  local t="$1"
  shift
  SDLC_ROOT="${t}" SDLC_ENGINE=shell SDLC_GATE_ENGINE=shell \
    "${t}/scripts/sdlc-spdd/sdlc.sh" "$@"
}

echo "== test_gate_architect_ok_shows_advisory_did_not_run =="
T="${WORK}/architect-ok"
work_id="FEAT-014-advisory-visible"
setup_feature "${T}"
write_requirement "${T}" "${work_id}"
write_canvas "${T}" "${work_id}"
sdlc "${T}" resume "${work_id}" --phase plan >/dev/null
if out="$(sdlc "${T}" gate architect --work-id "${work_id}" 2>&1)"; then
  if grep -q 'Architect review completed (advisory)' <<< "${out}" \
    && grep -q 'Operations are task-sized (advisory)' <<< "${out}" \
    && grep -q 'did not run' <<< "${out}"; then
    ok "gate architect OK shows advisory rows that did not run"
  else
    bad "gate architect OK hid advisory rows: ${out}"
  fi
else
  bad "gate architect should pass with requirement+canvas: ${out}"
fi

echo "== test_gate_architect_blocked_still_shows_advisory =="
T="${WORK}/architect-blocked"
work_id="FEAT-014-advisory-blocked"
setup_feature "${T}"
sdlc "${T}" resume "${work_id}" --phase plan >/dev/null
if out="$(sdlc "${T}" gate architect --work-id "${work_id}" 2>&1)"; then
  bad "gate architect must fail without canvas/requirement: ${out}"
else
  if grep -q 'BLOCKED' <<< "${out}" \
    && grep -q 'Architect review completed (advisory)' <<< "${out}" \
    && grep -q 'did not run' <<< "${out}"; then
    ok "blocked gate still shows advisory rows that did not run"
  else
    bad "blocked gate hid advisory rows: ${out}"
  fi
fi

echo "== test_gate_analysis_has_no_advisory_rows =="
T="${WORK}/analysis-ok"
work_id="FEAT-014-no-advisory"
setup_feature "${T}"
write_requirement "${T}" "${work_id}"
sdlc "${T}" resume "${work_id}" --phase init >/dev/null
if out="$(sdlc "${T}" gate analysis --work-id "${work_id}" 2>&1)"; then
  if grep -q '(advisory)' <<< "${out}" || grep -q 'did not run' <<< "${out}"; then
    bad "gate analysis should not invent advisory rows: ${out}"
  else
    ok "gate analysis has no advisory rows"
  fi
else
  bad "gate analysis should pass with a requirement: ${out}"
fi

echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
