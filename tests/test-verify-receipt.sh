#!/usr/bin/env bash
set -euo pipefail

# Leftover #6 proving test: I1 capture/complete without a verify receipt refuse.
# LessonRecord title/body (or --validation prose) is not a receipt.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=lib/engine-python.sh
source "${SCRIPT_DIR}/lib/engine-python.sh"
HARNESS_PYTHON="$(sdlc_harness_python "${REPO_ROOT}")"
CAPTURE="${REPO_ROOT}/scripts/capture-session-memory.sh"
SDLC_SH="${REPO_ROOT}/scripts/sdlc.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

setup_feature() {
  local t="$1"
  mkdir -p "${t}/sdlc-spdd/.sdlc/sessions" \
    "${t}/sdlc-spdd/scripts" \
    "${t}/sdlc-spdd/spdd/canvas" \
    "${t}/sdlc-spdd/spdd/analysis" \
    "${t}/sdlc-spdd/spdd/memory" \
    "${t}/sdlc-spdd/scripts/lib"
  : > "${t}/sdlc-spdd/spdd/memory/registry.jsonl"
  cp "${SDLC_SH}" "${t}/sdlc-spdd/scripts/sdlc.sh"
  cp "${CAPTURE}" "${t}/sdlc-spdd/scripts/capture-session-memory.sh"
  cp "${REPO_ROOT}/scripts/lib/"*.sh "${t}/sdlc-spdd/scripts/lib/"
  chmod +x "${t}/sdlc-spdd/scripts/"*.sh \
    "${t}/sdlc-spdd/scripts/sdlc.sh" \
    "${t}/sdlc-spdd/scripts/capture-session-memory.sh"
}

sdlc() {
  local t="$1"
  shift
  SDLC_ROOT="${t}" \
    PYTHON="${HARNESS_PYTHON}" \
    PYTHONPATH="${REPO_ROOT}/engine/src" \
    "${t}/sdlc-spdd/scripts/sdlc.sh" "$@"
}

echo "== test_capture_without_verify_receipt_refuses =="
T="${WORK}/capture-refuse"
work_id="FEAT-020-i1-receipt"
setup_feature "${T}"
sdlc "${T}" pointer set "${work_id}" >/dev/null
if out="$(sdlc "${T}" capture --phase code --summary "T01 complete" --validation "looked fine" 2>&1)"; then
  bad "capture without receipt should refuse: ${out}"
else
  if grep -q 'verify receipt required' <<< "${out}"; then
    ok "capture without receipt refuses"
  else
    bad "capture refuse message missing receipt: ${out}"
  fi
fi
if [[ -f "${T}/sdlc-spdd/.sdlc/staged/lessons.jsonl" ]]; then
  bad "refused capture must not stage a lesson"
else
  ok "refused capture left no staged lesson"
fi

echo "== test_complete_without_verify_receipt_refuses =="
T="${WORK}/complete-refuse"
work_id="FEAT-021-i1-complete"
setup_feature "${T}"
sdlc "${T}" pointer set "${work_id}" >/dev/null
if out="$(sdlc "${T}" complete --summary "T01 complete" 2>&1)"; then
  bad "complete without receipt should refuse: ${out}"
else
  if grep -q 'verify receipt required' <<< "${out}"; then
    ok "complete without receipt refuses"
  else
    bad "complete refuse message missing receipt: ${out}"
  fi
fi

echo "== test_complete_fail_receipt_refuses =="
T="${WORK}/complete-fail"
work_id="FEAT-022-i1-fail"
setup_feature "${T}"
sdlc "${T}" pointer set "${work_id}" >/dev/null
if out="$(sdlc "${T}" complete --summary "T01 complete" \
  --verify-command "pytest" --verify-exit 1 --verify-result fail 2>&1)"; then
  bad "complete with fail receipt should refuse: ${out}"
else
  if grep -q 'verify.result=pass' <<< "${out}"; then
    ok "complete refuses fail receipt"
  else
    bad "complete fail-receipt message: ${out}"
  fi
fi

echo "== test_capture_with_receipt_stages_verify_object =="
T="${WORK}/capture-ok"
work_id="FEAT-023-i1-ok"
setup_feature "${T}"
sdlc "${T}" pointer set "${work_id}" >/dev/null
if sdlc "${T}" capture --phase code --summary "T01 complete" \
  --verify-command "pytest tests/test_foo.py" \
  --verify-exit 0 \
  --verify-result pass >/dev/null; then
  ok "capture with receipt succeeds"
else
  bad "capture with receipt should succeed"
fi
stage="${T}/sdlc-spdd/.sdlc/staged/lessons.jsonl"
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
T="${WORK}/complete-ok"
work_id="FEAT-024-i1-done"
setup_feature "${T}"
sdlc "${T}" pointer set "${work_id}" >/dev/null
if sdlc "${T}" complete --summary "T01 complete" \
  --verify-command "true" \
  --verify-exit 0 \
  --verify-result pass >/dev/null; then
  ok "complete with pass receipt succeeds"
else
  bad "complete with pass receipt should succeed"
fi

echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
