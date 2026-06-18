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

assert_content() {
  local file="$1"
  local expected="$2"
  if [[ -f "${file}" && "$(cat "${file}")" == "${expected}" ]]; then ok "content preserved: $(rel "${file}")"; else bad "content changed: $(rel "${file}")"; fi
}

assert_contains() {
  local file="$1"
  local expected="$2"
  local label="$3"
  if [[ -f "${file}" ]] && grep -Fq "${expected}" "${file}"; then ok "contains ${label}: $(rel "${file}")"; else bad "missing ${label}: $(rel "${file}")"; fi
}

assert_count() {
  local file="$1"
  local expected_text="$2"
  local expected_count="$3"
  local label="$4"
  local actual_count
  actual_count="$(grep -F "${expected_text}" "${file}" | wc -l | tr -d ' ')"
  if [[ "${actual_count}" == "${expected_count}" ]]; then ok "count ${label}: ${actual_count}"; else bad "expected ${expected_count} ${label}, got ${actual_count}: $(rel "${file}")"; fi
}

assert_glob_exists() {
  local pattern="$1"
  local label="$2"
  shopt -s nullglob
  local matches=(${pattern})
  shopt -u nullglob
  if ((${#matches[@]} > 0)); then ok "glob exists ${label}: ${#matches[@]}"; else bad "missing glob ${label}: ${pattern}"; fi
}

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
  # Always-on operating-model rule (whole-ecosystem grounding).
  assert_file "${t}/.cursor/rules/sdlc-spdd.mdc"
  assert_same "${t}/.cursor/rules/sdlc-spdd.mdc" "${CURSOR_TPL}/rules/sdlc-spdd.mdc"
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

assert_claude_grounded() {
  local t="$1"
  assert_file "${t}/CLAUDE.md"
  assert_contains "${t}/CLAUDE.md" "BEGIN SDLC-SPDD MANAGED CLAUDE GROUNDING" "Claude managed grounding begin"
  assert_contains "${t}/CLAUDE.md" "END SDLC-SPDD MANAGED CLAUDE GROUNDING" "Claude managed grounding end"
  assert_contains "${t}/CLAUDE.md" "session-notes/" "Claude Planning grounding"
  assert_contains "${t}/CLAUDE.md" "spdd/canvas/" "Claude SPDD grounding"
  assert_contains "${t}/CLAUDE.md" "agent-context/sessions/" "Claude SDLC session grounding"
  assert_contains "${t}/CLAUDE.md" "agent-context/memory/" "Claude SDLC memory grounding"
  assert_count "${t}/CLAUDE.md" "BEGIN SDLC-SPDD MANAGED CLAUDE GROUNDING" 1 "Claude managed grounding begin markers"
  assert_count "${t}/CLAUDE.md" "END SDLC-SPDD MANAGED CLAUDE GROUNDING" 1 "Claude managed grounding end markers"
}

assert_memory_seed_files() {
  local t="$1"
  assert_file "${t}/agent-context/memory/phase-index.md"
  assert_same "${t}/agent-context/memory/phase-index.md" "${REPO_ROOT}/agent-context/memory/phase-index.md"
}

assert_no_cursor()  { local t="$1"; assert_absent "${t}/.cursor"; }
assert_no_copilot() { local t="$1"; assert_absent "${t}/.github/prompts"; assert_absent "${t}/.github/copilot-instructions.md"; }
assert_no_claude()  { local t="$1"; assert_absent "${t}/.claude"; assert_absent "${t}/CLAUDE.md"; }

assert_target_adapter_workflow() {
  local t="$1"
  local wf="${t}/.github/workflows/validate-sdlc-spdd-adapters.yml"
  assert_file "${wf}"
  assert_contains "${wf}" ".cursor/rules/sdlc-spdd.mdc" "Cursor grounding trigger"
  assert_contains "${wf}" ".github/copilot-instructions.md" "Copilot grounding trigger"
  assert_contains "${wf}" "CLAUDE.md" "Claude grounding trigger"
  assert_contains "${wf}" "bash -n ./scripts/sdlc-spdd/validate-command-adapters.sh" "validator syntax check"
}

# ---------------------------------------------------------------------------
echo "== Test 1: Cursor + Copilot only (no Claude side effects) =="
T="${WORK}/cc"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --cursor --copilot >/dev/null 2>&1
assert_cursor_pack "${T}"
assert_copilot_pack "${T}"
assert_no_claude "${T}"
assert_target_adapter_workflow "${T}"
expect_pass "verify --require-cursor --require-copilot" "${VERIFY}" --target "${T}" --require-cursor --require-copilot
expect_pass "validate (cursor+copilot)" "${VALIDATE}" --target "${T}"

# ---------------------------------------------------------------------------
echo "== Test 2: no assistant flags preserve legacy Cursor+Copilot default =="
T="${WORK}/default"; mkdir -p "${T}"
"${SETUP}" --target "${T}" >/dev/null 2>&1
assert_cursor_pack "${T}"
assert_copilot_pack "${T}"
assert_no_claude "${T}"
assert_target_adapter_workflow "${T}"
expect_pass "validate default cursor+copilot" "${VALIDATE}" --target "${T}"

# ---------------------------------------------------------------------------
echo "== Test 3: --all installs all three, Cursor/Copilot unchanged =="
T="${WORK}/all"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --all >/dev/null 2>&1
assert_cursor_pack "${T}"
assert_copilot_pack "${T}"
assert_claude_pack "${T}"
assert_memory_seed_files "${T}"
assert_target_adapter_workflow "${T}"
expect_pass "verify all three" "${VERIFY}" --target "${T}" --require-cursor --require-copilot --require-claude
expect_pass "validate (3 packs)" "${VALIDATE}" --target "${T}"

# ---------------------------------------------------------------------------
echo "== Test 4: Cursor only =="
T="${WORK}/cur"; mkdir -p "${T}"
"${INIT}" --target "${T}" --cursor >/dev/null 2>&1
assert_cursor_pack "${T}"
assert_no_copilot "${T}"
assert_no_claude "${T}"
expect_pass "verify --require-cursor" "${VERIFY}" --target "${T}" --require-cursor

# ---------------------------------------------------------------------------
echo "== Test 5: Copilot only =="
T="${WORK}/cop"; mkdir -p "${T}"
"${INIT}" --target "${T}" --copilot >/dev/null 2>&1
assert_copilot_pack "${T}"
assert_no_cursor "${T}"
assert_no_claude "${T}"
expect_pass "verify --require-copilot" "${VERIFY}" --target "${T}" --require-copilot

# ---------------------------------------------------------------------------
echo "== Test 6: Claude only (no Cursor/Copilot side effects) =="
T="${WORK}/cla"; mkdir -p "${T}"
"${INIT}" --target "${T}" --claude >/dev/null 2>&1
assert_claude_pack "${T}"
assert_no_cursor "${T}"
assert_no_copilot "${T}"
expect_pass "verify --require-claude" "${VERIFY}" --target "${T}" --require-claude

# ---------------------------------------------------------------------------
echo "== Test 7: no-flag upgrade preserves legacy Cursor+Copilot default =="
T="${WORK}/upg-default"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --cursor --copilot >/dev/null 2>&1
"${UPGRADE}" --target "${T}" >/dev/null 2>&1
assert_cursor_pack "${T}"
assert_copilot_pack "${T}"
assert_no_claude "${T}"
expect_pass "validate after default upgrade" "${VALIDATE}" --target "${T}"

# ---------------------------------------------------------------------------
echo "== Test 8: Claude install preserves existing CLAUDE.md and adds grounding =="
T="${WORK}/cla-existing"; mkdir -p "${T}"
custom_claude_install="custom install-time claude instructions"
printf '%s' "${custom_claude_install}" > "${T}/CLAUDE.md"
"${INIT}" --target "${T}" --claude >/dev/null 2>&1
assert_contains "${T}/CLAUDE.md" "${custom_claude_install}" "custom Claude content"
assert_claude_grounded "${T}"
assert_dir "${T}/.claude/commands"
expect_pass "validate Claude install with custom CLAUDE.md" "${VALIDATE}" --target "${T}"

# ---------------------------------------------------------------------------
echo "== Test 9: Upgrade --all adds Claude without disturbing Cursor/Copilot =="
T="${WORK}/upg"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --cursor --copilot >/dev/null 2>&1
"${UPGRADE}" --target "${T}" --all >/dev/null 2>&1
assert_cursor_pack "${T}"
assert_copilot_pack "${T}"
assert_claude_pack "${T}"
expect_pass "verify all three after upgrade" "${VERIFY}" --target "${T}" --require-cursor --require-copilot --require-claude

# ---------------------------------------------------------------------------
echo "== Test 10: Upgrade preserves project-owned Claude memory and target workflow =="
T="${WORK}/preserve"; mkdir -p "${T}/.github/workflows"
"${SETUP}" --target "${T}" --cursor --copilot >/dev/null 2>&1
custom_claude="custom existing claude instructions"
custom_workflow="custom existing adapter workflow"
printf '%s' "${custom_claude}" > "${T}/CLAUDE.md"
printf '%s' "${custom_workflow}" > "${T}/.github/workflows/validate-sdlc-spdd-adapters.yml"
"${UPGRADE}" --target "${T}" --all >/dev/null 2>&1
assert_contains "${T}/CLAUDE.md" "${custom_claude}" "custom Claude content"
assert_claude_grounded "${T}"
assert_content "${T}/.github/workflows/validate-sdlc-spdd-adapters.yml" "${custom_workflow}"
assert_glob_exists "${T}/.sdlc-spdd-upgrade-backups"/*/CLAUDE.md "CLAUDE.md backup"
assert_dir "${T}/.claude/commands"
for c in "${commands[@]}"; do
  assert_file "${T}/.claude/commands/sdlc-spdd-${c}.md"
  assert_same "${T}/.claude/commands/sdlc-spdd-${c}.md" "${CLAUDE_TPL}/commands/sdlc-spdd-${c}.md"
done
expect_pass "validate after preserving custom CLAUDE.md" "${VALIDATE}" --target "${T}"
"${UPGRADE}" --target "${T}" --all >/dev/null 2>&1
assert_contains "${T}/CLAUDE.md" "${custom_claude}" "custom Claude content after repeat upgrade"
assert_claude_grounded "${T}"
expect_pass "validate after repeated custom CLAUDE.md upgrade" "${VALIDATE}" --target "${T}"

# ---------------------------------------------------------------------------
echo "== Test 11: Upgrade dry-run does not mutate target files =="
T="${WORK}/dryrun"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --cursor --copilot >/dev/null 2>&1
dryrun_claude="dry-run custom claude instructions"
printf '%s' "${dryrun_claude}" > "${T}/CLAUDE.md"
"${UPGRADE}" --target "${T}" --all --dry-run >/dev/null 2>&1
assert_content "${T}/CLAUDE.md" "${dryrun_claude}"
assert_absent "${T}/.claude"

# ---------------------------------------------------------------------------
echo "== Test 12: Setup dry-run does not create scaffold files =="
T="${WORK}/setup-dryrun"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --all --dry-run >/dev/null 2>&1
assert_absent "${T}/requirements"
assert_absent "${T}/.cursor"
assert_absent "${T}/.github"
assert_absent "${T}/.claude"
assert_absent "${T}/CLAUDE.md"

# ---------------------------------------------------------------------------
echo "== Test 13: Partial upgrade creates missing grounding for present packs =="
T="${WORK}/partial"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --cursor --copilot >/dev/null 2>&1
rm -rf "${T}/.cursor/rules"
"${UPGRADE}" --target "${T}" --copilot >/dev/null 2>&1
assert_file "${T}/.cursor/rules/sdlc-spdd.mdc"
expect_pass "validate after partial copilot upgrade" "${VALIDATE}" --target "${T}"

# ---------------------------------------------------------------------------
echo "== Test 14: Validator still CATCHES Cursor/Copilot regressions =="
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
echo "== Test 15: Grounding files enforce the whole-ecosystem norm =="
T="${WORK}/grd"; mkdir -p "${T}"
"${SETUP}" --target "${T}" --all >/dev/null 2>&1
expect_pass "baseline validate (grounding present)" "${VALIDATE}" --target "${T}"

# 12a: strip the Planning (session-notes) artifact from the Claude grounding file
cp "${T}/CLAUDE.md" "${WORK}/claude-md.bak"
grep -Fv 'session-notes/' "${WORK}/claude-md.bak" > "${T}/CLAUDE.md"
expect_fail "validate after dropping session-notes from CLAUDE.md" "${VALIDATE}" --target "${T}"
cp "${WORK}/claude-md.bak" "${T}/CLAUDE.md"

# 12b: strip the SDLC session-brief artifact from the Claude grounding file
grep -Fv 'agent-context/sessions/' "${WORK}/claude-md.bak" > "${T}/CLAUDE.md"
expect_fail "validate after dropping agent-context/sessions from CLAUDE.md" "${VALIDATE}" --target "${T}"
cp "${WORK}/claude-md.bak" "${T}/CLAUDE.md"

# 12c: strip the SPDD (canvas) artifact from the Copilot grounding file
cp "${T}/.github/copilot-instructions.md" "${WORK}/copilot-inst.bak"
grep -Fv 'spdd/canvas/' "${WORK}/copilot-inst.bak" > "${T}/.github/copilot-instructions.md"
expect_fail "validate after dropping spdd/canvas from copilot-instructions.md" "${VALIDATE}" --target "${T}"
cp "${WORK}/copilot-inst.bak" "${T}/.github/copilot-instructions.md"

# 12d: remove the Cursor grounding rule entirely
mv "${T}/.cursor/rules/sdlc-spdd.mdc" "${WORK}/cursor-rule.bak"
expect_fail "validate after removing Cursor grounding rule" "${VALIDATE}" --target "${T}"
mv "${WORK}/cursor-rule.bak" "${T}/.cursor/rules/sdlc-spdd.mdc"

# 12e: confirm restored state validates again
expect_pass "validate after grounding restore" "${VALIDATE}" --target "${T}"

# ---------------------------------------------------------------------------
echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "Adapter install regression tests FAILED." >&2
  exit 1
fi
echo "All adapter install regression tests passed."
