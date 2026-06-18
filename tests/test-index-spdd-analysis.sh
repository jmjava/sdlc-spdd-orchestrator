#!/usr/bin/env bash
# Regression harness for index-spdd-analysis.sh (Fowler Step 3 decision memory).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INDEX="${REPO_ROOT}/scripts/index-spdd-analysis.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0

ok() { echo "  OK: $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL: $1" >&2; fail=$((fail + 1)); }

assert_file() { [[ -f "$1" ]] && ok "file ${1#${WORK}/}" || bad "missing file $1"; }
assert_contains() {
  if grep -Fq "$2" "$1" 2>/dev/null; then ok "$3"; else bad "$3 (pattern: $2)"; fi
}
assert_count() {
  local n
  n="$(grep -cE "$2" "$1" 2>/dev/null || true)"
  if [[ "${n}" == "$3" ]]; then ok "$4"; else bad "$4 (got ${n}, want $3)"; fi
}

mkdir -p "${WORK}/spdd/analysis" "${WORK}/agent-context/memory"
cp "${REPO_ROOT}/agent-context/memory/domain-index.md" "${WORK}/agent-context/memory/domain-index.md"

cat > "${WORK}/spdd/analysis/FEAT-010-billing-analysis.md" <<'AN'
# Analysis Context: FEAT-010-billing

## Domain Keywords

- billing
- quota
- modelId

## Code Areas

- com.acme.billing
- src/billing

## Strategic Direction

Extend billing engine for model-aware pricing.

## Recommendation

Proceed to plan.
AN

echo "== Test 1: index analysis keywords and areas =="
"${INDEX}" --target "${WORK}" --work-id FEAT-010-billing >/dev/null
assert_file "${WORK}/agent-context/memory/domain-index.md"
assert_contains "${WORK}/agent-context/memory/domain-index.md" "| billing | com.acme.billing | analysis | FEAT-010-billing |" "domain row billing+billing area"
assert_file "${WORK}/agent-context/memory/context-index.md"
assert_count "${WORK}/agent-context/memory/context-index.md" '^\| com\.acme\.billing \| analysis \|' 1 "context analysis row for package"
assert_count "${WORK}/agent-context/memory/context-index.md" '^\| src/billing \| analysis \|' 1 "context analysis row for directory"
assert_file "${WORK}/agent-context/memory/code-areas.md"
assert_contains "${WORK}/agent-context/memory/code-areas.md" "com.acme.billing" "new area in registry"

echo "== Test 2: dry-run makes no writes =="
rm -f "${WORK}/agent-context/memory/context-index.md"
"${INDEX}" --target "${WORK}" --work-id FEAT-010-billing --dry-run >/dev/null
if [[ -f "${WORK}/agent-context/memory/context-index.md" ]]; then
  bad "dry-run should not create context-index"
else
  ok "dry-run leaves context-index absent"
fi

echo "== Test 3: missing analysis file fails =="
if "${INDEX}" --target "${WORK}" --work-id MISSING 2>/dev/null; then
  bad "expected failure for missing analysis"
else
  ok "missing analysis exits non-zero"
fi

echo
if (( fail > 0 )); then
  echo "${fail} failed, ${pass} passed" >&2
  exit 1
fi
echo "All ${pass} index-spdd-analysis tests passed."
