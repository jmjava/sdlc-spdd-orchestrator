#!/usr/bin/env bash
set -euo pipefail

# Leftover #16 proving test: the Kasana "constraint" line must not treat
# named Validation as a machine constraint. Either name the leftover #6
# verify receipt, or delete the instruction-vs-constraint distinction.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

echo "== test_constraint_line_does_not_treat_validation_as_constraint =="
for rel in \
  sdlc-spdd/harness/quality-gates.md \
  templates/agent-context/harness/quality-gates.md
do
  text="$(cat "${REPO_ROOT}/${rel}")"
  if grep -q 'constrained by named Validation' <<< "${text}"; then
    bad "${rel} still claims named Validation is a code-exit constraint"
  else
    ok "${rel} does not claim named Validation is a constraint"
  fi
done

echo "== test_constraint_line_names_leftover_6_receipt_or_is_deleted =="
for rel in \
  sdlc-spdd/harness/quality-gates.md \
  templates/agent-context/harness/quality-gates.md
do
  text="$(cat "${REPO_ROOT}/${rel}")"
  if grep -q 'Instruction vs constraint' <<< "${text}"; then
    if grep -q 'verify receipt' <<< "${text}" \
      && grep -q 'command' <<< "${text}" \
      && grep -q 'exit' <<< "${text}" \
      && grep -Eq 'pass/fail|pass-fail' <<< "${text}"; then
      ok "${rel} names leftover #6 verify receipt"
    else
      bad "${rel} keeps instruction vs constraint without leftover #6 receipt"
    fi
  else
    ok "${rel} deleted the instruction-vs-constraint distinction"
  fi
done

echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
