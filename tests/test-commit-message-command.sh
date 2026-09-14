#!/usr/bin/env bash
# Regression harness for FEAT-008 /sdlc-spdd-commit-message adapters + engine routing.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pass=0
fail=0

ok() { echo "  OK: $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL: $1" >&2; fail=$((fail + 1)); }

assert_file() {
  if [[ -f "$1" ]]; then ok "file ${1#${REPO_ROOT}/}"; else bad "missing file $1"; fi
}

assert_contains() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  if grep -Fq "${pattern}" "${path}" 2>/dev/null; then
    ok "${label}"
  else
    bad "${label} (missing in ${path#${REPO_ROOT}/}: ${pattern})"
  fi
}

assert_absent() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  if grep -Fq "${pattern}" "${path}" 2>/dev/null; then
    bad "${label} (unexpected in ${path#${REPO_ROOT}/}: ${pattern})"
  else
    ok "${label}"
  fi
}

CURSOR="${REPO_ROOT}/templates/cursor/sdlc-spdd-commit-message.md"
COPILOT="${REPO_ROOT}/templates/copilot/prompts/sdlc-spdd-commit-message.prompt.md"
CLAUDE="${REPO_ROOT}/templates/claude/commands/sdlc-spdd-commit-message.md"
SPEC="${REPO_ROOT}/spec/commands/lifecycle-commit-message.spec.md"
ENGINE="${REPO_ROOT}/engine/src/sdlc_engine/commit_message.py"
SDLC_SH="${REPO_ROOT}/scripts/sdlc.sh"

echo "== Test 1: spec, adapters, and engine module exist =="
assert_file "${SPEC}"
assert_file "${CURSOR}"
assert_file "${COPILOT}"
assert_file "${CLAUDE}"
assert_file "${ENGINE}"

echo "== Test 2: generate-only commit message + engine delegation contract =="
for path in "${CURSOR}" "${COPILOT}" "${CLAUDE}"; do
  assert_contains "${path}" 'Do not run `git commit`' "no-commit guardrail (${path##*/})"
  assert_contains "${path}" "Do not implement code" "no-code guardrail (${path##*/})"
  assert_contains "${path}" "sdlc.sh commit-message" "engine delegation (${path##*/})"
  assert_contains "${path}" "Work ID" "Work ID metadata (${path##*/})"
  assert_contains "${path}" "On success:" "success feedback (${path##*/})"
  assert_contains "${path}" "On failure:" "failure feedback (${path##*/})"
  assert_contains "${path}" "Paste-ready commit message" "paste-ready output (${path##*/})"
  assert_absent "${path}" "PR review comment" "not a PR review command (${path##*/})"
done
assert_contains "${SDLC_SH}" '_engine_args=("${cmd}" "$@")' "sdlc.sh routes commands to Python engine"

echo "== Test 3: generator --check and adapter validation =="
if "${REPO_ROOT}/scripts/generate-command-adapters.sh" --check >/dev/null; then
  ok "generate-command-adapters --check"
else
  bad "generate-command-adapters --check"
fi
if "${REPO_ROOT}/scripts/validate-command-adapters.sh" >/dev/null; then
  ok "validate-command-adapters"
else
  bad "validate-command-adapters"
fi

echo "== Test 4: engine commit-message CLI smoke (isolated repo) =="
# Use a throwaway git repo so CI checkouts without origin/main still exercise
# the staged-diff path (unit coverage for ahead-of-base lives in pytest).
smoke_root="$(mktemp -d)"
trap 'rm -rf "${smoke_root}"' EXIT
git -C "${smoke_root}" init -q
git -C "${smoke_root}" config user.email "ci@example.com"
git -C "${smoke_root}" config user.name "CI"
printf '# smoke\n' > "${smoke_root}/README.md"
git -C "${smoke_root}" add README.md
git -C "${smoke_root}" commit -q -m "init"
printf 'staged\n' > "${smoke_root}/staged.txt"
git -C "${smoke_root}" add staged.txt
if PYTHONPATH="${REPO_ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
  python3 -m sdlc_engine --root "${smoke_root}" commit-message --hint "smoke" --work-id FEAT-008 \
  >/tmp/sdlc-cm-smoke.out 2>/tmp/sdlc-cm-smoke.err
then
  if grep -Fq 'source: staged' /tmp/sdlc-cm-smoke.out && grep -Fq 'staged.txt' /tmp/sdlc-cm-smoke.out; then
    ok "python -m sdlc_engine commit-message emits staged report"
  else
    bad "engine output missing staged report"
  fi
else
  bad "engine commit-message unexpected failure: $(cat /tmp/sdlc-cm-smoke.err)"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "commit-message command regression tests FAILED." >&2
  exit 1
fi
echo "All commit-message command regression tests passed."
