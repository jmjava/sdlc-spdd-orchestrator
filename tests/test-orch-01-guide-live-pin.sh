#!/usr/bin/env bash
set -euo pipefail

# ORCH-01 proving test: the experimental Guide + Neo4j live stack must pin
# orch-guide tag spdd-projection-v3, not leftover sdlc-spdd-projection-v2.
# Restoring the v2 checkout ref or GUIDE_GIT_REF default turns this red.
# Does not boot Guide or Neo4j.
#
# Usage: ./tests/test-orch-01-guide-live-pin.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKFLOW="${REPO_ROOT}/.github/workflows/test-guide-stack-experimental.yml"
LIVE="${REPO_ROOT}/tests/test-guide-stack-live.sh"
SUITES="${REPO_ROOT}/scripts/run-test-suites.sh"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

echo "== ORCH-01: experimental Guide live stack pin is spdd-projection-v3 =="

echo "== test_workflow_checkouts_the_v3_tag =="
if grep -Eq 'ref:[[:space:]]*spdd-projection-v3' "${WORKFLOW}"; then
  ok "workflow checkout ref is spdd-projection-v3"
else
  bad "workflow checkout ref is not spdd-projection-v3"
fi
if grep -Eq 'ref:[[:space:]]*sdlc-spdd-projection-v2' "${WORKFLOW}"; then
  bad "workflow still checks out leftover sdlc-spdd-projection-v2"
else
  ok "workflow does not check out sdlc-spdd-projection-v2"
fi

echo "== test_workflow_env_is_the_v3_tag =="
v3_env="$(grep -c 'GUIDE_GIT_REF: spdd-projection-v3' "${WORKFLOW}" || true)"
v2_env="$(grep -c 'GUIDE_GIT_REF: sdlc-spdd-projection-v2' "${WORKFLOW}" || true)"
if [[ "${v3_env}" -ge 2 ]]; then
  ok "workflow sets GUIDE_GIT_REF to spdd-projection-v3 (${v3_env} times)"
else
  bad "workflow GUIDE_GIT_REF v3 count is ${v3_env}, expected >= 2"
fi
if [[ "${v2_env}" -eq 0 ]]; then
  ok "workflow has no GUIDE_GIT_REF leftover v2"
else
  bad "workflow still sets GUIDE_GIT_REF to sdlc-spdd-projection-v2 (${v2_env})"
fi

echo "== test_workflow_asserts_head_is_the_tag =="
if grep -Fq "refs/tags/spdd-projection-v3" "${WORKFLOW}" \
  && grep -Fq 'Checked-out Guide is the spdd-projection-v3 tag' "${WORKFLOW}"; then
  ok "live job fails unless HEAD is the v3 tag"
else
  bad "live job dropped the HEAD-equals-tag assertion"
fi

echo "== test_live_script_default_is_the_v3_tag =="
if grep -Fq 'GUIDE_GIT_REF="${GUIDE_GIT_REF:-spdd-projection-v3}"' "${LIVE}"; then
  ok "test-guide-stack-live.sh defaults to spdd-projection-v3"
else
  bad "test-guide-stack-live.sh default is not spdd-projection-v3"
fi
if grep -Fq 'sdlc-spdd-projection-v2' "${LIVE}"; then
  bad "test-guide-stack-live.sh still names leftover v2"
else
  ok "test-guide-stack-live.sh no longer names leftover v2"
fi

echo "== test_run_test_suites_default_is_the_v3_tag =="
if grep -Fq 'GUIDE_GIT_REF:-spdd-projection-v3' "${SUITES}"; then
  ok "run-test-suites.sh defaults GUIDE_GIT_REF to spdd-projection-v3"
else
  bad "run-test-suites.sh default is not spdd-projection-v3"
fi
if grep -Fq 'GUIDE_GIT_REF:-sdlc-spdd-projection-v2' "${SUITES}"; then
  bad "run-test-suites.sh still defaults to leftover v2"
else
  ok "run-test-suites.sh no longer defaults to leftover v2"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "ORCH-01 Guide live-stack pin gate FAILED." >&2
  exit 1
fi
echo "ORCH-01 Guide live-stack pin gate passed."
