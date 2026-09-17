#!/usr/bin/env bash
set -euo pipefail

# ORCH-02 proving test: Suite 3 Playwright on main must run when
# engine/src changes, not only engine/tests_e2e. A push that breaks
# installer/app.py without touching e2e tests used to skip this job.
#
# Usage: ./tests/test-orch-02-playwright-src-paths.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW="$(cd "${SCRIPT_DIR}/.." && pwd)/.github/workflows/test-e2e-playwright.yml"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

section_paths() {
  local key="$1"
  awk -v key="${key}" '
    $0 ~ "^  " key ":" { in_sec=1; next }
    in_sec && /^  [a-z]/ { exit }
    in_sec { print }
  ' "${WORKFLOW}"
}

has_engine_tree() {
  printf '%s\n' "$1" | grep -Eq -- "- 'engine/\\*\\*'|- 'engine/src/\\*\\*'"
}

echo "== ORCH-02: Suite 3 Playwright watches engine/src on main =="

push_paths="$(section_paths push)"
pr_paths="$(section_paths pull_request)"

if has_engine_tree "${push_paths}"; then
  ok "push paths include engine/** or engine/src/**"
else
  bad "push paths do not include engine/src (would skip installer/app.py)"
fi

if printf '%s\n' "${push_paths}" | grep -Fq -- "- 'engine/tests_e2e/**'" \
  && ! has_engine_tree "${push_paths}"; then
  bad "push paths are still tests_e2e-only"
else
  ok "push paths are not tests_e2e-only"
fi

if has_engine_tree "${pr_paths}"; then
  ok "pull_request still watches the engine tree"
else
  bad "pull_request dropped the engine tree"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "ORCH-02 Playwright src-path gate FAILED." >&2
  exit 1
fi
echo "ORCH-02 Playwright src-path gate passed."
