#!/usr/bin/env bash
# Leftover #13 proving test: U2 CI must not pin research/blog leftover prose
# (#268, "U3 leftover", "this orchestrator (done)"). Assert environment
# behavior instead. Inspects test-cloud-environment.sh only; leftover #12's
# schema-meaning doc lock stays in test-agent-can-update-snapshot-semantics.sh.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
U2="${REPO_ROOT}/tests/test-cloud-environment.sh"
WORKFLOW="${REPO_ROOT}/.github/workflows/test-cloud-environment.yml"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

u2_pins_markdown() {
  local hay="$1"
  grep -Eq 'assert_contains[[:space:]]+"\$\{REPO_ROOT\}/[^"]+\.md"' "${hay}" \
    || grep -Eq 'assert_contains[[:space:]]+\$\{REPO_ROOT\}/[^[:space:]]+\.md' "${hay}" \
    || grep -Eq '(docs/research/|docs/blog/|docs/maintaining-your-project|sdlc-spdd/docs/maintaining-your-project).*\.md' "${hay}"
}

echo "== leftover #13: U2 does not pin doc prose =="

if [[ -f "${U2}" ]]; then
  ok "exists tests/test-cloud-environment.sh"
else
  bad "missing ${U2}"
fi

echo "== test_u2_does_not_assert_contains_markdown =="
if u2_pins_markdown "${U2}"; then
  bad "U2 still assert_contains / greps markdown docs"
  grep -nE '\.md|docs/research/|docs/blog/|maintaining-your-project' "${U2}" >&2 || true
else
  ok "U2 does not grep research/blog/maintaining markdown"
fi

echo "== test_u2_does_not_pin_stale_u3_changelog =="
stale_pins=(
  "this orchestrator (done)"
  "#268"
  "U2 marked done in research"
  "blog still names U2"
  "kasana leftover notes I3 copy-lock merged"
  "maintaining-your-project documents install.sh"
  "sdlc-spdd copy documents install.sh"
  "maintaining-your-project documents schema meaning"
  "maintaining-your-project documents Builds"
)
pin_hit=0
for pin in "${stale_pins[@]}"; do
  if grep -Fq -- "${pin}" "${U2}"; then
    bad "U2 still pins '${pin}'"
    pin_hit=1
  fi
done
if [[ "${pin_hit}" -eq 0 ]]; then
  ok "U2 does not pin leftover changelog / U3 / #268 phrases"
fi

echo "== test_pin_detector_catches_markdown_assert =="
scratch="$(mktemp)"
trap 'rm -f "${scratch}"' EXIT
cat > "${scratch}" << 'EOF'
assert_contains "${REPO_ROOT}/docs/research/kasana-agent-harness-2-0.md" \
  "#268" "kasana leftover notes I3 copy-lock merged"
EOF
if u2_pins_markdown "${scratch}"; then
  ok "detector fails a reintroduced markdown pin"
else
  bad "detector missed a kasana #268 assert_contains fixture"
fi

echo "== test_u2_asserts_environment_json_behavior =="
behavior_needles=(
  "environment.json is valid JSON"
  "environment.json is tracked"
  "environment.json is not gitignored"
  "no committed snapshot id"
  "no secret-looking material in environment files"
)
missing=0
for needle in "${behavior_needles[@]}"; do
  if grep -Fq -- "${needle}" "${U2}"; then
    ok "U2 asserts ${needle}"
  else
    bad "U2 dropped behavior assert: ${needle}"
    missing=1
  fi
done
if [[ "${missing}" -eq 0 ]]; then
  :
fi

echo "== test_u2_asserts_install_sh_behavior =="
if grep -Fq 'test-install-noninteractive-path.sh' "${U2}" \
  && grep -Fq 'test-install-sh-runs.sh' "${U2}"; then
  ok "U2 still runs leftover #10/#11 install behavior"
else
  bad "U2 must keep leftover #10/#11 proving tests"
fi
if grep -Fq 'agent_can_update_snapshot.py' "${U2}" \
  && grep -Fq 'test-agent-can-update-snapshot-semantics.sh' "${U2}"; then
  ok "U2 still classifies snapshot flag and runs leftover #12"
else
  bad "U2 must keep leftover #12 snapshot-flag behavior"
fi
if grep -Fq 'assert_absent "${INSTALL_SH}" ".git/hooks/"' "${U2}"; then
  ok "U2 still asserts install.sh does not write .git/hooks"
else
  bad "U2 dropped install.sh no-.git/hooks behavior"
fi

echo "== test_u2_workflow_does_not_path_filter_changelog_docs =="
changelog_docs=(
  "docs/blog/cloud-agents-as-the-sdlc-platform.md"
  "docs/research/kasana-agent-harness-2-0.md"
)
wf_hit=0
for doc in "${changelog_docs[@]}"; do
  if grep -Fq -- "${doc}" "${WORKFLOW}"; then
    bad "workflow still path-filters ${doc}"
    wf_hit=1
  fi
done
if [[ "${wf_hit}" -eq 0 ]]; then
  ok "workflow no longer fires on blog/kasana leftover prose"
fi
if grep -Fq 'test-u2-does-not-pin-doc-prose.sh' "${WORKFLOW}"; then
  ok "workflow runs leftover #13 proving test"
else
  bad "workflow must run tests/test-u2-does-not-pin-doc-prose.sh"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "Leftover #13 U2 doc-prose pins FAILED." >&2
  exit 1
fi
echo "Leftover #13 U2 doc-prose pins passed."
