#!/usr/bin/env bash
set -euo pipefail

# Leftover #20 proving test: verify-spike-guide-setup.sh must require the
# spdd-projection-v3 *tag*, not a local branch of that name and not the
# leftover that `rev-parse --abbrev-ref HEAD` is the string HEAD on any
# detached checkout (so a detached HEAD of anything used to pass).
#
# Usage: ./tests/test-verify-spike-guide-pin.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VERIFY="${REPO_ROOT}/scripts/guide/verify-spike-guide-setup.sh"

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

# Minimal git identity so fixture commits work in CI.
git_init() {
  local dir="$1"
  mkdir -p "${dir}"
  git -C "${dir}" init -q -b main
  git -C "${dir}" config user.email leftover20@example.test
  git -C "${dir}" config user.name leftover20
  printf 'seed\n' > "${dir}/README"
  git -C "${dir}" add README
  git -C "${dir}" commit -q -m seed
}

advance() {
  local dir="$1"
  printf 'advance %s\n' "$$" >> "${dir}/README"
  git -C "${dir}" add README
  git -C "${dir}" commit -q -m advance
}

run_verify() {
  local guide="$1"
  GUIDE_ROOT="${guide}" "${VERIFY}"
}

echo "== leftover #20: Guide pin is the tag, not a branch name or detached luck =="

echo "== test_script_no_longer_accepts_dead_branch_name =="
if grep -Eq 'branch.*"sdlc-spdd-projection-v3"|== "sdlc-spdd-projection-v3"' "${VERIFY}"; then
  bad "script still treats sdlc-spdd-projection-v3 as an accepted pin name"
else
  ok "dead ref sdlc-spdd-projection-v3 is not an accepted pin name"
fi
if grep -Fq 'refs/tags/spdd-projection-v3' "${VERIFY}"; then
  ok "script names the tag ref"
else
  bad "script does not require refs/tags/spdd-projection-v3"
fi

echo "== test_detached_head_not_at_tag_fails =="
# The leftover: abbrev-ref is HEAD, so the old allowlist passed any detached SHA.
git_init "${WORK}/detached-other"
git -C "${WORK}/detached-other" tag spdd-projection-v3
advance "${WORK}/detached-other"
git -C "${WORK}/detached-other" checkout -q --detach HEAD
expect_fail "detached HEAD that is not the tag" \
  run_verify "${WORK}/detached-other"

echo "== test_dead_branch_name_not_at_tag_fails =="
git_init "${WORK}/dead-name"
git -C "${WORK}/dead-name" tag spdd-projection-v3
advance "${WORK}/dead-name"
git -C "${WORK}/dead-name" checkout -q -b sdlc-spdd-projection-v3
expect_fail "local branch named sdlc-spdd-projection-v3 is not the pin" \
  run_verify "${WORK}/dead-name"

echo "== test_local_branch_named_like_the_tag_is_not_the_pin =="
git_init "${WORK}/name-only"
git -C "${WORK}/name-only" tag spdd-projection-v3
advance "${WORK}/name-only"
git -C "${WORK}/name-only" checkout -q -b spdd-projection-v3
expect_fail "local branch named spdd-projection-v3 is not the pin" \
  run_verify "${WORK}/name-only"

echo "== test_missing_tag_fails_even_on_main =="
git_init "${WORK}/no-tag"
expect_fail "main without the tag" \
  run_verify "${WORK}/no-tag"

echo "== test_detached_at_the_tag_passes =="
git_init "${WORK}/detached-tag"
git -C "${WORK}/detached-tag" tag spdd-projection-v3
git -C "${WORK}/detached-tag" checkout -q --detach spdd-projection-v3
expect_pass "detached HEAD that *is* the tag" \
  run_verify "${WORK}/detached-tag"

echo "== test_main_with_tag_present_passes =="
git_init "${WORK}/main-ok"
git -C "${WORK}/main-ok" tag spdd-projection-v3
advance "${WORK}/main-ok"
expect_pass "main when the tag exists (HEAD may have moved on)" \
  run_verify "${WORK}/main-ok"

echo "== test_head_at_tag_on_other_branch_passes =="
git_init "${WORK}/at-tag"
git -C "${WORK}/at-tag" tag spdd-projection-v3
git -C "${WORK}/at-tag" checkout -q -b work
expect_pass "any branch whose HEAD is the tag" \
  run_verify "${WORK}/at-tag"

echo "== test_old_allowlist_would_have_passed_the_leftover =="
# Reproduce the leftover logic against the detached-other fixture so a
# revert to name-matching cannot hide behind "we still fail for other reasons".
branch="$(git -C "${WORK}/detached-other" rev-parse --abbrev-ref HEAD)"
if [[ "${branch}" == "HEAD" ]]; then
  ok "detached leftover fixture reports abbrev-ref HEAD"
else
  bad "detached leftover fixture abbrev-ref is '${branch}', not HEAD"
fi
if [[ "${branch}" == "main" || "${branch}" == "HEAD" || "${branch}" == "sdlc-spdd-projection-v3" ]]; then
  ok "old name allowlist would have accepted that detached leftover"
else
  bad "old name allowlist no longer matches the leftover fixture"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "Leftover #20 Guide pin-is-the-tag gate FAILED." >&2
  exit 1
fi
echo "Leftover #20 Guide pin-is-the-tag gate passed."
