#!/usr/bin/env bash
set -euo pipefail

# Leftover #7 proving test: gate review requires Validation ran, not any ledger row.
# Capture a dummy lesson, skip tests, `gate review` must fail.
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

# Park a Work ID at a phase. The engine's `resume --phase` enforces the
# entrance gate of that phase, so fixtures use --force to set up the state
# the gate under test then inspects.
park() {
  local t="$1" work_id="$2" phase="$3"
  harness_sdlc "${t}" resume "${work_id}" --phase "${phase}" --force >/dev/null
}

echo "== test_gate_review_fails_dummy_lesson_skip_tests =="
new_target
work_id="FEAT-025-dummy-review"
write_canvas "${T}" "${work_id}"
park "${T}" "${work_id}" plan
if ! harness_sdlc "${T}" capture --phase plan --summary "dummy lesson" \
  --validation "skipped tests" >/dev/null; then
  bad "plan-phase dummy capture should succeed"
else
  ok "captured dummy lesson without a verify receipt"
fi
if [[ -f "$(harness_home "${T}")/.sdlc/staged/lessons.jsonl" ]] \
  && grep -q "\"work_id\": \"${work_id}\"" "$(harness_home "${T}")/.sdlc/staged/lessons.jsonl"; then
  ok "dummy lesson staged under the home's .sdlc/staged"
else
  bad "dummy lesson not staged under $(harness_home "${T}")/.sdlc/staged"
fi
if ! harness_sdlc "${T}" skip api-test --reason "skip tests" >/dev/null; then
  bad "skip api-test should succeed"
else
  ok "skipped tests (api-test)"
fi
if out="$(harness_sdlc "${T}" gate --phase review --work-id "${work_id}" 2>&1)"; then
  bad "gate review must fail after dummy lesson + skip tests: ${out}"
else
  if grep -q 'Validation receipt' <<< "${out}"; then
    ok "gate review fails without Validation"
  else
    bad "gate review failed but message missed Validation receipt: ${out}"
  fi
fi

echo "== test_gate_review_passes_with_validation_receipt =="
new_target
work_id="FEAT-026-review-receipt"
write_canvas "${T}" "${work_id}"
park "${T}" "${work_id}" code
if harness_sdlc "${T}" capture --phase code --summary "T01 complete" \
  --verify-command "pytest tests/test_foo.py" \
  --verify-exit 0 \
  --verify-result pass >/dev/null; then
  ok "code capture with receipt succeeds"
else
  bad "code capture with receipt should succeed"
fi
if out="$(harness_sdlc "${T}" gate --phase review --work-id "${work_id}" 2>&1)"; then
  ok "gate review passes with Validation receipt"
else
  bad "gate review should pass with receipt: ${out}"
fi

harness_finish
