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

echo "== Test 4: re-run is idempotent (no duplicate rows) =="
IDEM="$(mktemp -d)"
mkdir -p "${IDEM}/spdd/analysis" "${IDEM}/agent-context/memory"
cp "${REPO_ROOT}/agent-context/memory/domain-index.md" "${IDEM}/agent-context/memory/domain-index.md"
cat > "${IDEM}/spdd/analysis/FEAT-020-quota-analysis.md" <<'AN'
# Analysis Context: FEAT-020-quota

## Domain Keywords

- quota
- plan

## Code Areas

- com.acme.quota
- src/quota
AN
"${INDEX}" --target "${IDEM}" --work-id FEAT-020-quota >/dev/null
"${INDEX}" --target "${IDEM}" --work-id FEAT-020-quota >/dev/null
"${INDEX}" --target "${IDEM}" --work-id FEAT-020-quota >/dev/null
assert_count "${IDEM}/agent-context/memory/domain-index.md" '^\| quota \| com\.acme\.quota \| analysis \| FEAT-020-quota \|' 1 "domain row not duplicated after re-runs"
assert_count "${IDEM}/agent-context/memory/context-index.md" '^\| src/quota \| analysis \| FEAT-020-quota \|' 1 "context row not duplicated after re-runs"
assert_count "${IDEM}/agent-context/memory/code-areas.md" '^- com\.acme\.quota$' 1 "code area not duplicated after re-runs"
rm -rf "${IDEM}"

echo "== Test 5: re-run refreshes a second Work ID without dropping the first =="
MULTI="$(mktemp -d)"
mkdir -p "${MULTI}/spdd/analysis" "${MULTI}/agent-context/memory"
cp "${REPO_ROOT}/agent-context/memory/domain-index.md" "${MULTI}/agent-context/memory/domain-index.md"
cat > "${MULTI}/spdd/analysis/FEAT-030-a-analysis.md" <<'AN'
# Analysis Context: FEAT-030-a

## Domain Keywords

- alpha

## Code Areas

- src/alpha
AN
cat > "${MULTI}/spdd/analysis/FEAT-031-b-analysis.md" <<'AN'
# Analysis Context: FEAT-031-b

## Domain Keywords

- beta

## Code Areas

- src/beta
AN
"${INDEX}" --target "${MULTI}" --work-id FEAT-030-a >/dev/null
"${INDEX}" --target "${MULTI}" --work-id FEAT-031-b >/dev/null
"${INDEX}" --target "${MULTI}" --work-id FEAT-030-a >/dev/null
assert_count "${MULTI}/agent-context/memory/domain-index.md" '\| FEAT-030-a \|' 1 "first work id refreshed to single row"
assert_count "${MULTI}/agent-context/memory/domain-index.md" '\| FEAT-031-b \|' 1 "second work id preserved on re-run"
rm -rf "${MULTI}"

echo "== Test 6: keyword-only analysis (no Code Areas) writes placeholder area, no blank rows =="
KW="$(mktemp -d)"
mkdir -p "${KW}/spdd/analysis" "${KW}/agent-context/memory"
cp "${REPO_ROOT}/agent-context/memory/domain-index.md" "${KW}/agent-context/memory/domain-index.md"
cat > "${KW}/spdd/analysis/FEAT-040-kw-analysis.md" <<'AN'
# Analysis Context: FEAT-040-kw

## Domain Keywords

- gamma

## Strategic Direction

No code areas identified yet.
AN
"${INDEX}" --target "${KW}" --work-id FEAT-040-kw >/dev/null
assert_contains "${KW}/agent-context/memory/domain-index.md" "| gamma | - | analysis | FEAT-040-kw |" "keyword-only domain row uses placeholder area"
assert_count "${KW}/agent-context/memory/domain-index.md" '^\| \| ' 0 "no empty leading-pipe rows in domain index"
assert_count "${KW}/agent-context/memory/context-index.md" '^\| - \| analysis \| FEAT-040-kw \|' 1 "keyword-only context row uses placeholder area"
rm -rf "${KW}"

echo "== Test 7: area-only analysis (no Domain Keywords) leaves domain index header-only =="
AR="$(mktemp -d)"
mkdir -p "${AR}/spdd/analysis" "${AR}/agent-context/memory"
cp "${REPO_ROOT}/agent-context/memory/domain-index.md" "${AR}/agent-context/memory/domain-index.md"
cat > "${AR}/spdd/analysis/FEAT-050-ar-analysis.md" <<'AN'
# Analysis Context: FEAT-050-ar

## Code Areas

- src/onlyarea
AN
"${INDEX}" --target "${AR}" --work-id FEAT-050-ar >/dev/null
assert_count "${AR}/agent-context/memory/domain-index.md" '^\| \| ' 0 "no empty leading-pipe rows when keywords absent"
assert_count "${AR}/agent-context/memory/domain-index.md" '^\| FEAT' 0 "no malformed domain rows when keywords absent"
assert_count "${AR}/agent-context/memory/context-index.md" '^\| src/onlyarea \| analysis \| FEAT-050-ar \|' 1 "area-only context row present"
rm -rf "${AR}"

echo
if (( fail > 0 )); then
  echo "${fail} failed, ${pass} passed" >&2
  exit 1
fi
echo "All ${pass} index-spdd-analysis tests passed."
