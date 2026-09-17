#!/usr/bin/env bash
set -euo pipefail

# ORCH-03 / ORCH-04 proving test.
# ORCH-03: missing CURSOR_API_KEY must fail the workflow, not skip-PASS the SDK job.
# ORCH-04: overlapping live-consumer runs on the same ref must cancel the older one.
# Does not call the Cursor API.
#
# Usage: ./tests/test-orch-03-live-consumer-fail-closed.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW="$(cd "${SCRIPT_DIR}/.." && pwd)/.github/workflows/test-live-consumer.yml"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

echo "== ORCH-03/04: live-consumer fail-closed + concurrency =="

echo "== test_missing_key_is_a_workflow_failure =="
if grep -Fq 'cursor-sdk-not-skip-pass' "${WORKFLOW}" \
  && grep -Fq 'Live-consumer SDK is not a skip-PASS' "${WORKFLOW}" \
  && grep -Fq 'CURSOR_API_KEY is unset' "${WORKFLOW}"; then
  ok "workflow has a required job that fails when the key is missing"
else
  bad "workflow dropped the missing-key fail-closed job"
fi

echo "== test_sdk_job_skip_is_not_the_only_path =="
# The leftover: SDK job `if: available == true` + no other job → skip-PASS.
# A skip on the SDK job is allowed only if the required job still fails.
if grep -Fq 'if: needs.cursor-api-key-available.outputs.available == '\''true'\''' "${WORKFLOW}" \
  && ! grep -Fq 'cursor-sdk-not-skip-pass' "${WORKFLOW}"; then
  bad "SDK job skip is still a skip-PASS (no required missing-key job)"
else
  ok "SDK skip cannot hide a missing key"
fi

echo "== test_concurrency_cancels_the_older_run =="
if grep -Fq 'group: live-consumer-${{ github.ref }}' "${WORKFLOW}" \
  && grep -Fq 'cancel-in-progress: true' "${WORKFLOW}"; then
  ok "workflow concurrency cancels the older live-consumer run"
else
  bad "workflow has no live-consumer concurrency group"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "ORCH-03/04 live-consumer fail-closed gate FAILED." >&2
  exit 1
fi
echo "ORCH-03/04 live-consumer fail-closed gate passed."
