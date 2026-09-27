#!/usr/bin/env bash
set -euo pipefail

# When Guide is unreachable, project-spdd-entities.sh must tell operators to
# run the live pin spdd-projection-v3. Recommending sdlc-spdd-projection-v2
# fails this check.
#
# Usage: ./tests/test-project-spdd-entities-pin.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
HELPER="${REPO_ROOT}/scripts/guide/project-spdd-entities.sh"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

echo "== project-spdd-entities unreachable hint is spdd-projection-v3 =="

if grep -Fq 'sdlc-spdd-projection-v2' "${HELPER}"; then
  bad "helper still recommends sdlc-spdd-projection-v2"
else
  ok "helper source does not name sdlc-spdd-projection-v2"
fi

if grep -Fq 'spdd-projection-v3' "${HELPER}"; then
  ok "helper source names spdd-projection-v3"
else
  bad "helper source does not name spdd-projection-v3"
fi

set +e
output="$(GUIDE_PORT=41723 "${HELPER}" 2>&1)"
status=$?
set -e

if [[ "${status}" -ne 0 ]]; then
  ok "unreachable Guide exits non-zero"
else
  bad "unreachable Guide exited 0"
fi

if grep -Fq 'sdlc-spdd-projection-v2' <<<"${output}"; then
  bad "operator error still recommends sdlc-spdd-projection-v2"
else
  ok "operator error does not recommend sdlc-spdd-projection-v2"
fi

if grep -Fq 'spdd-projection-v3' <<<"${output}"; then
  ok "operator error names spdd-projection-v3"
else
  bad "operator error does not name spdd-projection-v3"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "project-spdd-entities pin gate FAILED." >&2
  exit 1
fi
echo "project-spdd-entities pin gate passed."
