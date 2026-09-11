#!/usr/bin/env bash
set -euo pipefail

# Leftover #7 proving test: gate review requires Validation ran, not any ledger row.
# Capture a dummy lesson, skip tests, `gate review` must fail.

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

echo "== test_gate_review_fails_dummy_lesson_skip_tests =="
T="${WORK}/dummy-skip"
work_id="FEAT-025-dummy-review"
setup_feature "${T}"
write_canvas "${T}" "${work_id}"
sdlc "${T}" resume "${work_id}" --phase plan >/dev/null
if ! sdlc "${T}" capture --phase plan --summary "dummy lesson" \
  --validation "skipped tests" >/dev/null; then
  bad "plan-phase dummy capture should succeed"
else
  ok "captured dummy lesson without a verify receipt"
fi
if ! sdlc "${T}" skip api-test --reason "skip tests" >/dev/null; then
  bad "skip api-test should succeed"
else
  ok "skipped tests (api-test)"
fi
if out="$(sdlc "${T}" gate review --work-id "${work_id}" 2>&1)"; then
  bad "gate review must fail after dummy lesson + skip tests: ${out}"
else
  if grep -q 'Validation receipt' <<< "${out}"; then
    ok "gate review fails without Validation"
  else
    bad "gate review failed but message missed Validation receipt: ${out}"
  fi
fi

echo "== test_gate_review_passes_with_validation_receipt =="
T="${WORK}/receipt-ok"
work_id="FEAT-026-review-receipt"
setup_feature "${T}"
write_canvas "${T}" "${work_id}"
sdlc "${T}" resume "${work_id}" --phase code >/dev/null
if sdlc "${T}" capture --phase code --summary "T01 complete" \
  --verify-command "pytest tests/test_foo.py" \
  --verify-exit 0 \
  --verify-result pass >/dev/null; then
  ok "code capture with receipt succeeds"
else
  bad "code capture with receipt should succeed"
fi
if out="$(sdlc "${T}" gate review --work-id "${work_id}" 2>&1)"; then
  ok "gate review passes with Validation receipt"
else
  bad "gate review should pass with receipt: ${out}"
fi

echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
