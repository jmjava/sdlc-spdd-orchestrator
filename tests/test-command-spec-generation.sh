#!/usr/bin/env bash
# FEAT-002 — command spec generation / adapter staleness regression.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GEN="${REPO_ROOT}/scripts/generate-command-adapters.sh"
EXTRACT="${REPO_ROOT}/scripts/extract-command-specs.sh"
VALIDATE="${REPO_ROOT}/scripts/validate-command-adapters.sh"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

echo "== Test 1: shell syntax =="
if bash -n "${GEN}" && bash -n "${EXTRACT}"; then
  ok "generator and extract scripts parse"
else
  bad "shell syntax"
fi

echo "== Test 2: checked-in adapters match specs =="
if "${GEN}" --check >/dev/null; then
  ok "generate-command-adapters --check clean"
else
  bad "adapters stale vs specs"
fi

echo "== Test 3: workflow + lifecycle specs exist =="
missing=0
for slug in claim shelf advance next team; do
  [[ -f "${REPO_ROOT}/spec/commands/workflow-${slug}.spec.md" ]] || missing=1
done
for slug in init analysis plan architect code api-test review commit-message prompt-update retro sync sunset whereami; do
  [[ -f "${REPO_ROOT}/spec/commands/lifecycle-${slug}.spec.md" ]] || missing=1
done
if [[ "${missing}" -eq 0 ]]; then
  ok "all expected command specs present"
else
  bad "missing command specs"
fi

echo "== Test 4: --check detects intentional drift =="
tmp="$(mktemp)"
trap 'rm -f "${tmp}"' EXIT
target="${REPO_ROOT}/templates/cursor/sdlc-claim.md"
cp "${target}" "${tmp}"
printf '\n<!-- drift-probe -->\n' >> "${target}"
if "${GEN}" --check >/dev/null 2>&1; then
  bad "--check should fail after template drift"
else
  ok "--check fails on drifted adapter"
fi
mv "${tmp}" "${target}"
if "${GEN}" --check >/dev/null; then
  ok "restored adapter passes --check"
else
  bad "restore left adapters stale"
fi

echo "== Test 5: parity validator still green =="
if "${VALIDATE}" >/dev/null; then
  ok "validate-command-adapters passes"
else
  bad "validate-command-adapters failed"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if (( fail > 0 )); then exit 1; fi
echo "All command-spec generation tests passed."
