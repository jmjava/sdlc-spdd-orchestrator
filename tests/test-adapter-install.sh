#!/usr/bin/env bash
set -euo pipefail

# Regression harness for the assistant adapter install/upgrade/validation flow.
#
# Goal: prove that adding a new assistant (Claude Code) does not change the
# behavior of the existing Cursor and GitHub Copilot adapters, and that the
# parity validator still catches real regressions. Runs entirely against
# throwaway target directories; touches nothing outside a temp dir.
#
# Usage: ./tests/test-adapter-install.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SETUP="${REPO_ROOT}/scripts/setup-agent-prompts.sh"
INIT="${REPO_ROOT}/scripts/init-project.sh"
UPGRADE="${REPO_ROOT}/scripts/upgrade-project.sh"
VERIFY="${REPO_ROOT}/scripts/verify-project-install.sh"
VALIDATE="${REPO_ROOT}/scripts/validate-command-adapters.sh"

CURSOR_TPL="${REPO_ROOT}/templates/cursor"
COPILOT_TPL="${REPO_ROOT}/templates/copilot"
CLAUDE_TPL="${REPO_ROOT}/templates/claude"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0

ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

rel() { echo "${1#"${WORK}"/}"; }

assert_file()   { if [[ -f "$1" ]]; then ok "exists: $(rel "$1")"; else bad "missing: $(rel "$1")"; fi; }
assert_dir()    { if [[ -d "$1" ]]; then ok "dir exists: $(rel "$1")"; else bad "missing dir: $(rel "$1")"; fi; }
assert_absent() { if [[ ! -e "$1" ]]; then ok "absent: $(rel "$1")"; else bad "should be absent: $(rel "$1")"; fi; }

assert_same() {
  # Installed file must be byte-identical to its framework template.
  if cmp -s "$1" "$2"; then ok "byte-identical to template: $(rel "$1")"; else bad "differs from template: $(rel "$1")"; fi
}

expect_pass() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then ok "passes: ${label}"; else bad "expected pass: ${label}"; fi
}

expect_fail() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then bad "expected FAIL but passed: ${label}"; else ok "correctly fails: ${label}"; fi
}

commands=(init plan architect code review prompt-update retro sync)

assert_cursor_pack() {
  local t="$1"
  assert_dir "${t}/.cursor/commands"
  for c in "${commands[@]}"; do
    assert_file "${t}/.cursor/commands/sdlc-spdd-${c}.md"
    assert_same "${t}/.cursor/commands/sdlc-spdd-${c}.md" "${CURSOR_TPL}/sdlc-spdd-${c}.md"
  done
}

assert_copilot_pack() {
  local t="$1"
  assert_file "${t}/.github/copilot-instructions.md"
  assert_same "${t}/.github/copilot-instructions.md" "${COPILOT_TPL}/copilot-instructions.md"
  for c in "${commands[@]}"; do
    assert_file "${t}/.github/prompts/sdlc-spdd-${c}.prompt.md"
    assert_same "${t}/.github/prompts/sdlc-spdd-${c}.prompt.md" "${COPILOT_TPL}/prompts/sdlc-spdd-${c}.prompt.md"
  done
}

assert_claude_pack() {
  local t="$1"
  assert_dir "${t}/.claude/commands"
  assert_file "${t}/CLAUDE.md"
  assert_same "${t}/CLAUDE.md" "${CLAUDE_TPL}/CLAUDE.md"
  for c in "${commands[@]}"; do
    assert_file "${t}/.claude/commands/sdlc-spdd-${c}.md"
    assert_same "${t}/.claude/commands/sdlc-spdd-${c}.md" "${CLAUDE_TPL}/commands/sdlc-spdd-${c}.md"
  done
}

assert_no_cursor()  { local t="$1"; assert_absent "${t}/.cursor"; }
assert_no_copilot() { local t="$1"; assert_absent "${t}/.github/prompts"; assert_absent "${t}/.github/copilot-instructions.md"; }
assert_no_claude()  { local t="$1"; assert_absent "${t}/.claude"; assert_absent "${t}/CLAUDE.md"; }

# ---------------------------------------------------------------------------
echo "== Test 1: Cursor + Copilot only (no Claude side effects) =="
T="${WORK}/cc"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --cursor --copilot >/dev/null 2>&1
assert_cursor_pack "${T}"
assert_copilot_pack "${T}"
assert_no_claude "${T}"
expect_pass "verify --require-cursor --require-copilot" "${VERIFY}" --target "${T}" --require-cursor --require-copilot
expect_pass "validate (cursor+copilot)" "${VALIDATE}" --target "${T}"

# ---------------------------------------------------------------------------
echo "== Test 2: --all installs all three, Cursor/Copilot unchanged =="
T="${WORK}/all"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --all >/dev/null 2>&1
assert_cursor_pack "${T}"
assert_copilot_pack "${T}"
assert_claude_pack "${T}"
expect_pass "verify all three" "${VERIFY}" --target "${T}" --require-cursor --require-copilot --require-claude
expect_pass "validate (3 packs)" "${VALIDATE}" --target "${T}"

# ---------------------------------------------------------------------------
echo "== Test 3: Cursor only =="
T="${WORK}/cur"; mkdir -p "${T}"
"${INIT}" --target "${T}" --cursor >/dev/null 2>&1
assert_cursor_pack "${T}"
assert_no_copilot "${T}"
assert_no_claude "${T}"
expect_pass "verify --require-cursor" "${VERIFY}" --target "${T}" --require-cursor

# ---------------------------------------------------------------------------
echo "== Test 4: Copilot only =="
T="${WORK}/cop"; mkdir -p "${T}"
"${INIT}" --target "${T}" --copilot >/dev/null 2>&1
assert_copilot_pack "${T}"
assert_no_cursor "${T}"
assert_no_claude "${T}"
expect_pass "verify --require-copilot" "${VERIFY}" --target "${T}" --require-copilot

# ---------------------------------------------------------------------------
echo "== Test 5: Claude only (no Cursor/Copilot side effects) =="
T="${WORK}/cla"; mkdir -p "${T}"
"${INIT}" --target "${T}" --claude >/dev/null 2>&1
assert_claude_pack "${T}"
assert_no_cursor "${T}"
assert_no_copilot "${T}"
expect_pass "verify --require-claude" "${VERIFY}" --target "${T}" --require-claude

# ---------------------------------------------------------------------------
echo "== Test 6: Upgrade adds Claude without disturbing Cursor/Copilot =="
T="${WORK}/upg"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --cursor --copilot >/dev/null 2>&1
"${UPGRADE}" --target "${T}" --all >/dev/null 2>&1
assert_cursor_pack "${T}"
assert_copilot_pack "${T}"
assert_claude_pack "${T}"
expect_pass "verify all three after upgrade" "${VERIFY}" --target "${T}" --require-cursor --require-copilot --require-claude

# ---------------------------------------------------------------------------
echo "== Test 7: Validator still CATCHES Cursor/Copilot regressions =="
T="${WORK}/neg"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --all >/dev/null 2>&1
expect_pass "baseline validate" "${VALIDATE}" --target "${T}"

# 7a: remove a Cursor guardrail
cp "${T}/.cursor/commands/sdlc-spdd-code.md" "${WORK}/code.bak"
grep -Fv 'Implement only that task.' "${WORK}/code.bak" > "${T}/.cursor/commands/sdlc-spdd-code.md"
expect_fail "validate after removing Cursor guardrail" "${VALIDATE}" --target "${T}"
cp "${WORK}/code.bak" "${T}/.cursor/commands/sdlc-spdd-code.md"

# 7b: break Copilot Required-Behavior step-count parity
cp "${T}/.github/prompts/sdlc-spdd-plan.prompt.md" "${WORK}/plan.bak"
awk '1; /^## Required Behavior$/{print "15. extra"; print "16. extra"; print "17. extra"}' \
  "${WORK}/plan.bak" > "${T}/.github/prompts/sdlc-spdd-plan.prompt.md"
expect_fail "validate after Copilot step-count divergence" "${VALIDATE}" --target "${T}"
cp "${WORK}/plan.bak" "${T}/.github/prompts/sdlc-spdd-plan.prompt.md"

# 7c: delete a Cursor command file (dir still present)
mv "${T}/.cursor/commands/sdlc-spdd-review.md" "${WORK}/review.bak"
expect_fail "validate after deleting Cursor command file" "${VALIDATE}" --target "${T}"
mv "${WORK}/review.bak" "${T}/.cursor/commands/sdlc-spdd-review.md"

# 7d: remove a Claude guardrail
cp "${T}/.claude/commands/sdlc-spdd-review.md" "${WORK}/clreview.bak"
grep -Fv 'Do not make code changes unless explicitly asked.' "${WORK}/clreview.bak" > "${T}/.claude/commands/sdlc-spdd-review.md"
expect_fail "validate after removing Claude guardrail" "${VALIDATE}" --target "${T}"
cp "${WORK}/clreview.bak" "${T}/.claude/commands/sdlc-spdd-review.md"

# 7e: delete a Claude command file (dir still present)
mv "${T}/.claude/commands/sdlc-spdd-sync.md" "${WORK}/clsync.bak"
expect_fail "validate after deleting Claude command file" "${VALIDATE}" --target "${T}"
mv "${WORK}/clsync.bak" "${T}/.claude/commands/sdlc-spdd-sync.md"

# 7f: confirm restored state validates again
expect_pass "validate after restore" "${VALIDATE}" --target "${T}"

# ---------------------------------------------------------------------------
echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "Adapter install regression tests FAILED." >&2
  exit 1
fi
echo "All adapter install regression tests passed."
