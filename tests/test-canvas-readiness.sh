#!/usr/bin/env bash
# FEAT-005 readiness + leading-indicator smoke tests
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VALIDATE="${ROOT}/scripts/validate-reasons-canvas.sh"
CAPTURE="${ROOT}/scripts/capture-session-memory.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT
pass=0; fail=0
ok() { echo "  ok   $*"; pass=$((pass+1)); }
bad() { echo "  FAIL $*"; fail=$((fail+1)); }

echo "== Test 1: sections-only canvas still validates (no readiness) =="
mkdir -p "${WORK}/bare"
cat > "${WORK}/bare/FEAT-BARE.md" <<'EOF'
# REASONS Canvas: FEAT-BARE

## Metadata
- Work ID: FEAT-BARE

## R - Requirements
## E - Entities
## A - Approach
## S - Structure
## O - Operations
## N - Norms
## S - Safeguards
## Review Checklist
## Sync Notes
## Final Status
EOF
if "${VALIDATE}" "${WORK}/bare/FEAT-BARE.md" >/dev/null; then ok "bare canvas valid"; else bad "bare canvas should validate"; fi

echo "== Test 2: Metadata Ready For Coding normalizes =="
cp "${WORK}/bare/FEAT-BARE.md" "${WORK}/bare/FEAT-READY.md"
sed -i 's/## Metadata/## Metadata\n- Readiness: Ready For Coding/' "${WORK}/bare/FEAT-READY.md"
out="$("${VALIDATE}" "${WORK}/bare/FEAT-READY.md" 2>&1)"
if grep -q 'readiness: ready-for-coding' <<<"${out}"; then ok "normalizes Ready For Coding"; else bad "expected ready-for-coding in: ${out}"; fi

echo "== Test 3: YAML frontmatter readiness =="
cat > "${WORK}/bare/FEAT-YAML.md" <<'EOF'
---
readiness: needs-analysis
---
# REASONS Canvas: FEAT-YAML

## Metadata
## R - Requirements
## E - Entities
## A - Approach
## S - Structure
## O - Operations
## N - Norms
## S - Safeguards
## Review Checklist
## Sync Notes
## Final Status
EOF
out="$("${VALIDATE}" "${WORK}/bare/FEAT-YAML.md" 2>&1)"
if grep -q 'readiness: needs-analysis' <<<"${out}"; then ok "yaml readiness"; else bad "yaml: ${out}"; fi

echo "== Test 4: unrecognized readiness warns but exits 0 =="
cp "${WORK}/bare/FEAT-BARE.md" "${WORK}/bare/FEAT-WEIRD.md"
sed -i 's/## Metadata/## Metadata\n- Readiness: Totally Made Up/' "${WORK}/bare/FEAT-WEIRD.md"
set +e
out="$("${VALIDATE}" "${WORK}/bare/FEAT-WEIRD.md" 2>&1)"
rc=$?
set -e
if [[ "${rc}" -eq 0 ]] && grep -qi 'Warning:.*unrecognized readiness' <<<"${out}"; then
  ok "unknown readiness warns, exit 0"
else
  bad "expected warn+0 got rc=${rc} out=${out}"
fi

echo "== Test 5: Reviewed — Approved With Notes → reviewed =="
cp "${WORK}/bare/FEAT-BARE.md" "${WORK}/bare/FEAT-REV.md"
sed -i 's/## Metadata/## Metadata\n- Readiness: Reviewed — Approved With Notes/' "${WORK}/bare/FEAT-REV.md"
out="$("${VALIDATE}" "${WORK}/bare/FEAT-REV.md" 2>&1)"
if grep -q 'readiness: reviewed' <<<"${out}"; then ok "reviewed prefix"; else bad "reviewed: ${out}"; fi

echo "== Test 5b: parenthetical annotation stripped =="
cp "${WORK}/bare/FEAT-BARE.md" "${WORK}/bare/FEAT-PAREN.md"
sed -i 's/## Metadata/## Metadata\n- Readiness: Ready For Coding (implemented on integration)/' "${WORK}/bare/FEAT-PAREN.md"
out="$("${VALIDATE}" "${WORK}/bare/FEAT-PAREN.md" 2>&1)"
if grep -q 'readiness: ready-for-coding' <<<"${out}" && ! grep -qi 'Warning:.*unrecognized readiness' <<<"${out}"; then
  ok "parenthetical Ready For Coding normalizes"
else
  bad "paren annotate: ${out}"
fi

echo "== Test 5c: architect values Needs Redesign + Blocked =="
cp "${WORK}/bare/FEAT-BARE.md" "${WORK}/bare/FEAT-REDESIGN.md"
sed -i 's/## Metadata/## Metadata\n- Readiness: Needs Redesign/' "${WORK}/bare/FEAT-REDESIGN.md"
out="$("${VALIDATE}" "${WORK}/bare/FEAT-REDESIGN.md" 2>&1)"
if grep -q 'readiness: needs-redesign' <<<"${out}"; then ok "needs-redesign"; else bad "redesign: ${out}"; fi
cp "${WORK}/bare/FEAT-BARE.md" "${WORK}/bare/FEAT-BLOCKED.md"
sed -i 's/## Metadata/## Metadata\n- Readiness: Blocked/' "${WORK}/bare/FEAT-BLOCKED.md"
out="$("${VALIDATE}" "${WORK}/bare/FEAT-BLOCKED.md" 2>&1)"
if grep -q 'readiness: blocked' <<<"${out}"; then ok "blocked"; else bad "blocked: ${out}"; fi

echo "== Test 6: capture validate/review cycle metrics =="
T="${WORK}/cap"; mkdir -p "${T}"
"${CAPTURE}" --target "${T}" --work-id FEAT-005-cycles --phase review \
  --summary "cycle metrics" --areas "scripts/validate-reasons-canvas.sh" \
  --validate-cycles 2 --review-cycles 1 >/dev/null
stage="${T}/.sdlc/staged/lessons.jsonl"
if [[ -f "${stage}" ]] \
  && grep -q '"work_id": "FEAT-005-cycles"' "${stage}" \
  && grep -q '"kind": "session"' "${stage}" \
  && grep -q 'cycle metrics' "${stage}"; then
  ok "capture stages session record"
else
  bad "missing staged session in ${stage}"
fi

echo "== Test 7: directory validate reports readiness per file =="
T="${WORK}/dir"; mkdir -p "${T}"
cat > "${T}/FEAT-A.md" <<'EOF'
# A
## Metadata
- Readiness: Ready For Coding
## R - Requirements
## E - Entities
## A - Approach
## S - Structure
## O - Operations
## N - Norms
## S - Safeguards
## Review Checklist
## Sync Notes
## Final Status
EOF
cat > "${T}/FEAT-B.md" <<'EOF'
# B
## Metadata
- Readiness: Blocked
## R - Requirements
## E - Entities
## A - Approach
## S - Structure
## O - Operations
## N - Norms
## S - Safeguards
## Review Checklist
## Sync Notes
## Final Status
EOF
out="$("${VALIDATE}" "${T}" 2>&1)"
if grep -q 'ready-for-coding' <<<"${out}" && grep -q 'blocked' <<<"${out}"; then
  ok "directory validate reports both readiness values"
else
  bad "dir validate: ${out}"
fi

echo "== Test 8: complete / done aliases normalize =="
cat > "${WORK}/done.md" <<'EOF'
# D
## Metadata
- Readiness: Done
## R - Requirements
## E - Entities
## A - Approach
## S - Structure
## O - Operations
## N - Norms
## S - Safeguards
## Review Checklist
## Sync Notes
## Final Status
EOF
out="$("${VALIDATE}" "${WORK}/done.md" 2>&1)"
if grep -q 'readiness: complete' <<<"${out}"; then ok "Done → complete"; else bad "done alias: ${out}"; fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
[[ "${fail}" -eq 0 ]]
