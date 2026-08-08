#!/usr/bin/env bash
# Regression harness for index-spdd-analysis.sh (storage v3 staged analysis records).
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

stage_file() {
  printf '%s' "${1}/.sdlc/staged/lessons.jsonl"
}

mkdir -p "${WORK}/spdd/analysis"

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
STAGE="$(stage_file "${WORK}")"
assert_file "${STAGE}"
assert_contains "${STAGE}" '"kind": "analysis"' "staged analysis kind"
assert_contains "${STAGE}" '"work_id": "FEAT-010-billing"' "staged work id"
assert_contains "${STAGE}" '"area": "com.acme.billing"' "primary code area"
assert_contains "${STAGE}" 'billing' "keywords include billing"
assert_contains "${STAGE}" 'src/billing' "extra code area in keywords"

echo "== Test 2: dry-run makes no writes =="
DRY="$(mktemp -d)"
mkdir -p "${DRY}/spdd/analysis"
cp "${WORK}/spdd/analysis/FEAT-010-billing-analysis.md" "${DRY}/spdd/analysis/FEAT-010-billing-analysis.md"
"${INDEX}" --target "${DRY}" --work-id FEAT-010-billing --dry-run >/dev/null
if [[ -f "$(stage_file "${DRY}")" ]]; then
  bad "dry-run should not create staged lessons"
else
  ok "dry-run leaves staged lessons absent"
fi
rm -rf "${DRY}"

echo "== Test 3: missing analysis file fails =="
if "${INDEX}" --target "${WORK}" --work-id MISSING 2>/dev/null; then
  bad "expected failure for missing analysis"
else
  ok "missing analysis exits non-zero"
fi

echo "== Test 4: re-run appends staged records with stable id =="
IDEM="$(mktemp -d)"
mkdir -p "${IDEM}/spdd/analysis"
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
IDEM_STAGE="$(stage_file "${IDEM}")"
assert_count "${IDEM_STAGE}" '"id": "analysis:FEAT-020-quota:com\.acme\.quota:analysis"' 3 "re-runs append staged analysis records"
assert_contains "${IDEM_STAGE}" 'quota' "keywords preserved on re-run"
assert_contains "${IDEM_STAGE}" 'src/quota' "extra area preserved on re-run"
rm -rf "${IDEM}"

echo "== Test 5: re-run refreshes a second Work ID without dropping the first =="
MULTI="$(mktemp -d)"
mkdir -p "${MULTI}/spdd/analysis"
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
MULTI_STAGE="$(stage_file "${MULTI}")"
assert_count "${MULTI_STAGE}" '"work_id": "FEAT-030-a"' 2 "first work id preserved across re-run"
assert_count "${MULTI_STAGE}" '"work_id": "FEAT-031-b"' 1 "second work id preserved on re-run"
rm -rf "${MULTI}"

echo "== Test 6: keyword-only analysis uses placeholder area =="
KW="$(mktemp -d)"
mkdir -p "${KW}/spdd/analysis"
cat > "${KW}/spdd/analysis/FEAT-040-kw-analysis.md" <<'AN'
# Analysis Context: FEAT-040-kw

## Domain Keywords

- gamma

## Strategic Direction

No code areas identified yet.
AN
"${INDEX}" --target "${KW}" --work-id FEAT-040-kw >/dev/null
KW_STAGE="$(stage_file "${KW}")"
assert_contains "${KW_STAGE}" '"area": ""' "keyword-only analysis uses empty primary area"
assert_contains "${KW_STAGE}" 'gamma' "keyword-only analysis keeps keyword"
rm -rf "${KW}"

echo "== Test 7: area-only analysis (no Domain Keywords) still stages =="
AR="$(mktemp -d)"
mkdir -p "${AR}/spdd/analysis"
cat > "${AR}/spdd/analysis/FEAT-050-ar-analysis.md" <<'AN'
# Analysis Context: FEAT-050-ar

## Code Areas

- src/onlyarea
AN
"${INDEX}" --target "${AR}" --work-id FEAT-050-ar >/dev/null
AR_STAGE="$(stage_file "${AR}")"
assert_contains "${AR_STAGE}" '"area": "src/onlyarea"' "area-only analysis uses code area"
assert_count "${AR_STAGE}" '"work_id": "FEAT-050-ar"' 1 "area-only analysis staged once"
rm -rf "${AR}"

echo
if (( fail > 0 )); then
  echo "${fail} failed, ${pass} passed" >&2
  exit 1
fi
echo "All ${pass} index-spdd-analysis tests passed."
