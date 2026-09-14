#!/usr/bin/env bash
set -euo pipefail

# Leftover #14 proving test: sdlc.sh gate must show advisory rows that did not run.
# GATE_LABELS append "(advisory)" on next; gate used to print only failures.
#
# Runs the Python engine through the installed sdlc-spdd/scripts/sdlc.sh on a
# fresh init-project target per case. The former SDLC_ENGINE=shell /
# SDLC_GATE_ENGINE=shell exports are gone: the bash gate twin was deleted and
# setting those variables now makes sdlc.sh exit 2.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/harness.sh
source "${SCRIPT_DIR}/lib/harness.sh"

TARGETS=()
cleanup() {
  local t
  for t in "${TARGETS[@]}"; do rm -rf "${t}"; done
  return 0
}
trap cleanup EXIT

# Sets T (installed target). Not a subshell, so the target is tracked for cleanup.
new_target() {
  T="$(harness_new_target)"
  TARGETS+=("${T}")
}

write_canvas() {
  local t="$1" work_id="$2"
  local home
  home="$(harness_home "${t}")"
  mkdir -p "${home}/spdd/canvas"
  cat > "${home}/spdd/canvas/${work_id}.md" <<EOF
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
  local t="$1" work_id="$2"
  local home
  home="$(harness_home "${t}")"
  mkdir -p "${home}/requirements/milestones"
  printf '# Requirement: %s\n' "${work_id}" > "${home}/requirements/milestones/${work_id}.md"
}

# Park a Work ID at a phase. The engine's `resume --phase` enforces the
# entrance gate of that phase, so fixtures use --force to set up the state
# the gate under test then inspects.
park() {
  local t="$1" work_id="$2" phase="$3"
  harness_sdlc "${t}" resume "${work_id}" --phase "${phase}" --force >/dev/null
}

echo "== test_gate_architect_ok_shows_advisory_did_not_run =="
new_target
work_id="FEAT-014-advisory-visible"
write_requirement "${T}" "${work_id}"
write_canvas "${T}" "${work_id}"
park "${T}" "${work_id}" plan
if out="$(harness_sdlc "${T}" gate --phase architect --work-id "${work_id}" 2>&1)"; then
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
if out="$(harness_sdlc "${T}" gate --phase architect --work-id "${work_id}" --json 2>&1)" \
  && grep -q '"gate": "architect_review"' <<< "${out}" \
  && grep -q '"ran": false' <<< "${out}"; then
  ok "gate --json lists advisory rows with ran=false"
else
  bad "gate --json missing advisory rows: ${out}"
fi

echo "== test_gate_architect_blocked_still_shows_advisory =="
new_target
work_id="FEAT-014-advisory-blocked"
park "${T}" "${work_id}" plan
if out="$(harness_sdlc "${T}" gate --phase architect --work-id "${work_id}" 2>&1)"; then
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
new_target
work_id="FEAT-014-no-advisory"
write_requirement "${T}" "${work_id}"
park "${T}" "${work_id}" init
if out="$(harness_sdlc "${T}" gate --phase analysis --work-id "${work_id}" 2>&1)"; then
  if grep -q '(advisory)' <<< "${out}" || grep -q 'did not run' <<< "${out}"; then
    bad "gate analysis should not invent advisory rows: ${out}"
  else
    ok "gate analysis has no advisory rows"
  fi
else
  bad "gate analysis should pass with a requirement: ${out}"
fi

harness_finish
