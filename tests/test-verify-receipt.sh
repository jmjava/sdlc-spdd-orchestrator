#!/usr/bin/env bash
set -euo pipefail

# Leftover #6 proving test: I1 capture/complete without a verify receipt refuse.
# LessonRecord title/body (or --validation prose) is not a receipt.
#
# Runs the Python engine through the installed sdlc-spdd/scripts/sdlc.sh on a
# fresh init-project target per case. The former SDLC_ENGINE=shell /
# SDLC_GATE_ENGINE=shell exports are gone: the bash twin was deleted and
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

staged_file() {
  printf '%s' "$(harness_home "$1")/.sdlc/staged/lessons.jsonl"
}

# Park a Work ID at the code phase. The engine's `resume --phase` enforces the
# entrance gate of that phase, so fixtures use --force to set up the state the
# capture/complete verbs then operate on.
park_code() {
  harness_sdlc "$1" resume "$2" --phase code --force >/dev/null
}

echo "== test_capture_without_verify_receipt_refuses =="
new_target
work_id="FEAT-020-i1-receipt"
park_code "${T}" "${work_id}"
if out="$(harness_sdlc "${T}" capture --phase code --summary "T01 complete" --validation "looked fine" 2>&1)"; then
  bad "capture without receipt should refuse: ${out}"
else
  if grep -q 'verify receipt required' <<< "${out}"; then
    ok "capture without receipt refuses"
  else
    bad "capture refuse message missing receipt: ${out}"
  fi
fi
if [[ -f "$(staged_file "${T}")" ]]; then
  bad "refused capture must not stage a lesson"
else
  ok "refused capture left no staged lesson"
fi

echo "== test_complete_without_verify_receipt_refuses =="
new_target
work_id="FEAT-021-i1-complete"
park_code "${T}" "${work_id}"
if out="$(harness_sdlc "${T}" complete --summary "T01 complete" 2>&1)"; then
  bad "complete without receipt should refuse: ${out}"
else
  if grep -q 'verify receipt required' <<< "${out}"; then
    ok "complete without receipt refuses"
  else
    bad "complete refuse message missing receipt: ${out}"
  fi
fi

echo "== test_complete_fail_receipt_refuses =="
new_target
work_id="FEAT-022-i1-fail"
park_code "${T}" "${work_id}"
if out="$(harness_sdlc "${T}" complete --summary "T01 complete" \
  --verify-command "pytest" --verify-exit 1 --verify-result fail 2>&1)"; then
  bad "complete with fail receipt should refuse: ${out}"
else
  if grep -q 'verify.result=pass' <<< "${out}"; then
    ok "complete refuses fail receipt"
  else
    bad "complete fail-receipt message: ${out}"
  fi
fi
if [[ -f "$(staged_file "${T}")" ]]; then
  bad "refused complete must not stage a lesson"
else
  ok "refused complete left no staged lesson"
fi

echo "== test_capture_with_receipt_stages_verify_object =="
new_target
work_id="FEAT-023-i1-ok"
park_code "${T}" "${work_id}"
if harness_sdlc "${T}" capture --phase code --summary "T01 complete" \
  --verify-command "pytest tests/test_foo.py" \
  --verify-exit 0 \
  --verify-result pass >/dev/null; then
  ok "capture with receipt succeeds"
else
  bad "capture with receipt should succeed"
fi
stage="$(staged_file "${T}")"
if [[ -f "${stage}" ]] \
  && grep -q '"command": "pytest tests/test_foo.py"' "${stage}" \
  && grep -q '"exit": 0' "${stage}" \
  && grep -q '"result": "pass"' "${stage}" \
  && grep -q '"verify"' "${stage}"; then
  ok "staged LessonRecord has command/exit/pass-fail"
else
  bad "staged record missing verify object: $(cat "${stage}" 2>/dev/null || true)"
fi

echo "== test_complete_with_pass_receipt_succeeds =="
new_target
work_id="FEAT-024-i1-done"
park_code "${T}" "${work_id}"
if harness_sdlc "${T}" complete --summary "T01 complete" \
  --verify-command "true" \
  --verify-exit 0 \
  --verify-result pass >/dev/null; then
  ok "complete with pass receipt succeeds"
else
  bad "complete with pass receipt should succeed"
fi
stage="$(staged_file "${T}")"
if [[ -f "${stage}" ]] \
  && grep -q "\"work_id\": \"${work_id}\"" "${stage}" \
  && grep -q '"result": "pass"' "${stage}"; then
  ok "complete staged a pass receipt for ${work_id}"
else
  bad "complete did not stage a pass receipt: $(cat "${stage}" 2>/dev/null || true)"
fi

harness_finish
