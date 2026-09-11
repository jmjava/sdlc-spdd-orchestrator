#!/usr/bin/env bash
# Leftover #18 proving test: I3 "never write .git/hooks" is a filesystem
# snapshot around init/upgrade, not a textual grep of the scripts.
# A write assembled from variables evades ".git/hooks on non-comment lines".
# Does not write .git/hooks in this repo — only throwaway temp dirs.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADAPTER_TEST="${REPO_ROOT}/tests/test-adapter-install.sh"
WORKFLOW="${REPO_ROOT}/.github/workflows/test-adapter-install.yml"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

# Same shape as test-adapter-install.sh: names + contents, not mtime.
hooks_fingerprint() {
  local dir="$1"
  if [[ ! -d "${dir}" ]]; then
    printf 'ABSENT\n'
    return 0
  fi
  {
    find "${dir}" -mindepth 1 \( -type f -o -type l \) -print0 \
      | sort -z \
      | while IFS= read -r -d '' path; do
          if [[ -L "${path}" ]]; then
            printf 'LINK %s -> %s\n' "${path#"${dir}"/}" "$(readlink "${path}")"
          else
            printf 'FILE %s %s\n' "${path#"${dir}"/}" "$(sha256sum "${path}" | awk '{print $1}')"
          fi
        done
    find "${dir}" -mindepth 1 -type d -printf 'DIR %P\n' | sort
  }
}

# The leftover hole: grep for a literal .git/hooks on non-comment lines.
comment_only_git_hooks_misses() {
  local file="$1"
  local live
  live="$(grep -nE '\.git/hooks' "${file}" | grep -vE '^[^:]+:[[:space:]]*#' || true)"
  [[ -z "${live}" ]]
}

echo "== leftover #18: I3 hook-write guard is behavioral =="

echo "== test_comment_only_grep_misses_variable_assembled_write =="
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT
mkdir -p "${scratch}/fixture"
# No literal ".git/hooks" on a non-comment line. The leftover hole.
cat > "${scratch}/fixture/write-via-var.sh" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
git_dir=".git"
hook_leaf="hooks/pre-commit"
printf 'injected-by-variable\n' > "${git_dir}/${hook_leaf}"
EOF
if comment_only_git_hooks_misses "${scratch}/fixture/write-via-var.sh"; then
  ok "old comment-only grep misses a variable-assembled write"
else
  bad "fixture accidentally contains a live .git/hooks literal"
fi

echo "== test_fingerprint_catches_variable_assembled_write =="
mkdir -p "${scratch}/repo/.git/hooks"
printf '%s\n' '#!/bin/sh' 'echo keep' > "${scratch}/repo/.git/hooks/keep-me"
before="$(hooks_fingerprint "${scratch}/repo/.git/hooks")"
(
  cd "${scratch}/repo"
  bash "${scratch}/fixture/write-via-var.sh"
)
after="$(hooks_fingerprint "${scratch}/repo/.git/hooks")"
if [[ "${before}" != "${after}" ]]; then
  ok "fingerprint catches variable-assembled hook write"
else
  bad "fingerprint missed variable-assembled hook write"
fi
if [[ -f "${scratch}/repo/.git/hooks/pre-commit" ]]; then
  ok "fixture wrote only the throwaway temp hook"
else
  bad "fixture did not write the temp hook"
fi

echo "== test_adapter_install_dropped_comment_only_grep_claim =="
if grep -q 'assert_comment_only_git_hooks' "${ADAPTER_TEST}"; then
  bad "Test 17 still claims never-write via assert_comment_only_git_hooks"
else
  ok "assert_comment_only_git_hooks is gone"
fi

echo "== test_adapter_install_snapshots_hooks_around_init_and_upgrade =="
if grep -q 'hooks_fingerprint' "${ADAPTER_TEST}" \
  && grep -q 'assert_hooks_unchanged' "${ADAPTER_TEST}"; then
  ok "adapter-install snapshots .git/hooks"
else
  bad "adapter-install must snapshot .git/hooks (not only grep scripts)"
fi
unchanged_count="$(grep -c 'assert_hooks_unchanged' "${ADAPTER_TEST}" || true)"
if [[ "${unchanged_count}" -ge 2 ]]; then
  ok "init and upgrade both assert hooks unchanged (${unchanged_count})"
else
  bad "need assert_hooks_unchanged for both init and upgrade, got ${unchanged_count}"
fi

echo "== test_adapter_install_keeps_behavioral_init_upgrade =="
if grep -Fq 'assert_absent "${T}/.git/hooks/pre-commit"' "${ADAPTER_TEST}"; then
  ok "Test 16 still asserts init does not create pre-commit"
else
  bad "Test 16 dropped assert_absent pre-commit"
fi
if grep -Fq 'echo custom-hook' "${ADAPTER_TEST}" \
  && grep -Fq '"${UPGRADE}" --target "${T}" --all' "${ADAPTER_TEST}"; then
  ok "Test 17 still runs upgrade against an existing custom hook"
else
  bad "Test 17 dropped the upgrade behavioral fixture"
fi
if grep -Fq '${HOME_DIR}/scripts/hooks/pre-commit.sample' "${ADAPTER_TEST}"; then
  ok "Test 17 still locks copy dest to scripts/hooks"
else
  bad "Test 17 dropped the scripts/hooks copy-dest lock"
fi

echo "== test_adapter_workflow_runs_leftover_18 =="
if grep -Fq 'test-i3-hook-write-is-behavioral.sh' "${WORKFLOW}"; then
  ok "workflow runs leftover #18 proving test"
else
  bad "workflow must run tests/test-i3-hook-write-is-behavioral.sh"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "Leftover #18 I3 hook-write behavioral gate FAILED." >&2
  exit 1
fi
echo "Leftover #18 I3 hook-write behavioral gate passed."
