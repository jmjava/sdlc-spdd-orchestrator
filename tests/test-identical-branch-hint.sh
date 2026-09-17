#!/usr/bin/env bash
set -euo pipefail

# Leftover #19 proving test: the install-time path rewrite must not collapse a
# dual-branch sentence into one path, and the adapter validator must fail the
# packs when it does.
#
# The packs tell the reader which entry point belongs to which context:
#
#   (in the orchestrator repo: `./scripts/sdlc.sh gate ...`; installed projects:
#    `./sdlc-spdd/scripts/sdlc.sh gate ...`)
#   ... (or `./scripts/sdlc.sh team` in the orchestrator repo)
#
# A blind `./scripts/sdlc.sh` rewrite spells both branches the same way, so the
# sentence survives every existing grep-style check while telling an agent the
# two contexts share one path.
#
# Usage: ./tests/test-identical-branch-hint.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# shellcheck source=../scripts/lib/framework-install.sh
source "${REPO_ROOT}/scripts/lib/framework-install.sh"

VALIDATE="${REPO_ROOT}/scripts/validate-command-adapters.sh"
DOGFOOD_VALIDATE="${REPO_ROOT}/sdlc-spdd/scripts/validate-command-adapters.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

expect_pass() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then ok "passes: ${label}"; else bad "expected pass: ${label}"; fi
}

expect_fail() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then bad "expected FAIL but passed: ${label}"; else ok "correctly fails: ${label}"; fi
}

# A scratch installed target shaped like the dogfood CI job: Cursor is the
# proving host, and --mode installed so a templates/ tree cannot mask drift.
make_installed_target() {
  local dir="$1"
  mkdir -p "${dir}/.cursor/commands" "${dir}/.cursor/rules"
  cp "${REPO_ROOT}/.cursor/commands/"sdlc-*.md "${dir}/.cursor/commands/"
  cp "${REPO_ROOT}/.cursor/rules/sdlc-spdd.mdc" "${dir}/.cursor/rules/"
}

echo "== test_blind_rewrite_collapses_both_branches =="
cat > "${WORK}/blind.md" <<'EOF'
1. Gate first: run `./scripts/sdlc.sh gate code --work-id <WORK-ID>` (in the
   orchestrator repo: `./scripts/sdlc.sh gate ...`; installed projects:
   `./scripts/sdlc-spdd/sdlc.sh gate ...`).
2. Run `./scripts/sdlc-spdd/sdlc.sh team` (or `./scripts/sdlc.sh team` in the orchestrator repo).
EOF
sed -E \
  -e 's#(\./)?scripts/sdlc-spdd/#\1sdlc-spdd/scripts/#g' \
  -e 's#\./scripts/sdlc\.sh#./sdlc-spdd/scripts/sdlc.sh#g' \
  "${WORK}/blind.md" > "${WORK}/blind.out"
if grep -Fq 'orchestrator repo: `./sdlc-spdd/scripts/sdlc.sh gate' "${WORK}/blind.out" \
  && grep -Fq '(or `./sdlc-spdd/scripts/sdlc.sh team` in the orchestrator repo)' "${WORK}/blind.out"; then
  ok "blind rewrite collapses both branches (the leftover)"
else
  bad "fixture did not reproduce the leftover"
fi

echo "== test_rewrite_keeps_orchestrator_branch_distinct =="
cp "${WORK}/blind.md" "${WORK}/fixed.md"
framework_rewrite_adapter_paths "${WORK}/fixed.md"
if grep -Fq 'orchestrator repo: `./scripts/sdlc.sh gate ...`' "${WORK}/fixed.md" \
  && grep -Fq 'installed projects:' "${WORK}/fixed.md" \
  && grep -Fq '`./sdlc-spdd/scripts/sdlc.sh gate ...`' "${WORK}/fixed.md"; then
  ok "labelled branches stay distinct after rewrite"
else
  bad "labelled branches collapsed after rewrite"
fi
if grep -Fq 'Run `./sdlc-spdd/scripts/sdlc.sh team` (or `./scripts/sdlc.sh team` in the orchestrator repo)' "${WORK}/fixed.md"; then
  ok "parenthetical branches stay distinct after rewrite"
else
  bad "parenthetical branches collapsed after rewrite"
fi
if grep -Fq "${FRAMEWORK_ORCH_SDLC_SENTINEL}" "${WORK}/fixed.md"; then
  bad "rewrite leaked the sentinel into the output"
else
  ok "rewrite leaves no sentinel behind"
fi

echo "== test_rewrite_refuses_a_file_carrying_the_sentinel =="
# The rewrite must not silently mangle prose that already contains the
# placeholder it relies on.
printf 'run `%s gate`\n' "${FRAMEWORK_ORCH_SDLC_SENTINEL}" > "${WORK}/sentinel.md"
expect_fail "rewrite refuses a file that already contains the sentinel" \
  framework_rewrite_adapter_paths "${WORK}/sentinel.md"

echo "== test_validator_fails_labelled_identical_branch =="
make_installed_target "${WORK}/labelled"
target="${WORK}/labelled/.cursor/commands/sdlc-spdd-code.md"
sed -i -E 's#(orchestrator repo: `)\./scripts/sdlc\.sh#\1./sdlc-spdd/scripts/sdlc.sh#' "${target}"
if grep -Fq 'orchestrator repo: `./sdlc-spdd/scripts/sdlc.sh gate' "${target}"; then
  ok "injected the labelled leftover"
else
  bad "could not inject the labelled leftover"
fi
expect_fail "validator rejects labelled identical-branch prose" \
  "${VALIDATE}" --target "${WORK}/labelled" --mode installed

echo "== test_validator_fails_parenthetical_identical_branch =="
make_installed_target "${WORK}/parenthetical"
target="${WORK}/parenthetical/.cursor/commands/sdlc-team.md"
sed -i -E 's#(\(or `)\./scripts/sdlc\.sh#\1./sdlc-spdd/scripts/sdlc.sh#' "${target}"
if grep -Fq '(or `./sdlc-spdd/scripts/sdlc.sh team` in the orchestrator repo)' "${target}"; then
  ok "injected the parenthetical leftover"
else
  bad "could not inject the parenthetical leftover"
fi
expect_fail "validator rejects parenthetical identical-branch prose" \
  "${VALIDATE}" --target "${WORK}/parenthetical" --mode installed

echo "== test_validator_accepts_committed_packs =="
make_installed_target "${WORK}/clean"
expect_pass "validator accepts the committed dogfood packs" \
  "${VALIDATE}" --target "${WORK}/clean" --mode installed
expect_pass "validator accepts the shipped templates" \
  "${VALIDATE}" --target "${REPO_ROOT}" --mode templates

echo "== test_committed_packs_carry_no_identical_branch =="
collapsed=0
while IFS= read -r file; do
  echo "  collapsed: ${file#"${REPO_ROOT}"/}" >&2
  collapsed=1
done < <(grep -rlE 'orchestrator repo: `\./sdlc-spdd/scripts/sdlc\.sh|\(or `\./sdlc-spdd/scripts/sdlc\.sh' \
  "${REPO_ROOT}/.cursor/commands" "${REPO_ROOT}/.claude/commands" "${REPO_ROOT}/.github/prompts" \
  "${REPO_ROOT}/templates" 2>/dev/null || true)
if [[ "${collapsed}" -eq 0 ]]; then
  ok "no committed pack has identical path branches"
else
  bad "a committed pack still has identical path branches"
fi

echo "== test_dogfood_validator_copy_in_sync =="
if diff -q "${VALIDATE}" "${DOGFOOD_VALIDATE}" >/dev/null 2>&1; then
  ok "sdlc-spdd/ validator copy matches scripts/"
else
  bad "sdlc-spdd/scripts/validate-command-adapters.sh drifted from scripts/"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "Leftover #19 identical-branch gate FAILED." >&2
  exit 1
fi
echo "Leftover #19 identical-branch gate passed."
