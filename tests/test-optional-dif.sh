#!/usr/bin/env bash
# Fail-closed / detect-and-skip without a JVM. Orch CI must not need Maven.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STUB="${ROOT}/tests/fixtures/dif-fold-stub.sh"
pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

resolve() {
  if [[ "${DIF_DISABLED:-}" == "1" ]]; then
    return 1
  fi
  if [[ -n "${DIF_HOME:-}" && -x "${DIF_HOME}/scripts/dif-fold.sh" ]]; then
    echo "${DIF_HOME}/scripts/dif-fold.sh"
    return 0
  fi
  return 1
}

run_architect() {
  if cli="$(resolve)"; then
    "${cli}" architect --quiet --canvas unused.md
    return $?
  fi
  echo "dif=skipped"
  return 0
}

echo "== missing CLI is skip =="
unset DIF_HOME
DIF_DISABLED=1
set +e
out="$(run_architect)"
code=$?
set -e
if [[ "${code}" -eq 0 && "${out}" == "dif=skipped" ]]; then
  ok "missing CLI → dif=skipped exit 0"
else
  bad "missing CLI (got code=${code} out=${out})"
fi
unset DIF_DISABLED

echo "== stub exit 0 is ready =="
tmp="$(mktemp -d)"
mkdir -p "${tmp}/scripts"
ln -s "${STUB}" "${tmp}/scripts/dif-fold.sh"
export DIF_HOME="${tmp}"
export DIF_STUB_EXIT=0 DIF_STUB_STATUS=ready
set +e
out="$(run_architect)"
code=$?
set -e
if [[ "${code}" -eq 0 && "${out}" == "dif=ready workId=STUB" ]]; then
  ok "present CLI exit 0 → ready"
else
  bad "ready stub (got code=${code} out=${out})"
fi

echo "== stub exit 1 is blocked (not Ready For Coding) =="
export DIF_STUB_EXIT=1 DIF_STUB_STATUS=blocked
set +e
out="$(run_architect)"
code=$?
set -e
if [[ "${code}" -eq 1 && "${out}" == "dif=blocked workId=STUB" ]]; then
  ok "present CLI exit 1 → blocked"
else
  bad "blocked stub (got code=${code} out=${out})"
fi
rm -rf "${tmp}"

if grep -Fq "Do not use login fixtures" "${ROOT}/spec/commands/lifecycle-review.spec.md"; then
  ok "review spec forbids login fixtures"
else
  bad "review spec missing login-fixture ban"
fi

echo
if [[ "${fail}" -eq 0 ]]; then
  echo "Summary: ${pass} passed, 0 failed"
  exit 0
fi
echo "Summary: ${pass} passed, ${fail} failed" >&2
exit 1
