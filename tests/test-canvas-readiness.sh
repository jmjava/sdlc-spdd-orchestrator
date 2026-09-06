#!/usr/bin/env bash
# FEAT-005 readiness + FEAT-014 semantic minima smoke tests
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VALIDATE="${ROOT}/scripts/validate-reasons-canvas.sh"
CAPTURE="${ROOT}/scripts/capture-session-memory.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT
pass=0; fail=0
ok() { echo "  ok   $*"; pass=$((pass+1)); }
bad() { echo "  FAIL $*"; fail=$((fail+1)); }

write_canvas() {
  local path="$1"
  local extra_meta="${2:-}"
  local extra_sync="${3:-}"
  cat > "${path}" <<EOF
# REASONS Canvas: $(basename "${path}" .md)

## Metadata
- Work ID: $(basename "${path}" .md)
${extra_meta}
## R - Requirements
Implement the fixture operation with a real requirement sentence.
## E - Entities
- Widget
## A - Approach
Do the smallest change.
## S - Structure
- src/app.py
## O - Operations
### T01 - Implement fixture
- Status: Not Started
## N - Norms
- One operation
## S - Safeguards
- Do not expand scope
## Review Checklist
- [ ] reviewed
## Sync Notes
${extra_sync}
## Final Status
- Status: In Progress
EOF
}

echo "== Test 1: headings-only canvas is invalid (FEAT-014) =="
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
set +e
out="$("${VALIDATE}" "${WORK}/bare/FEAT-BARE.md" 2>&1)"
rc=$?
set -e
if [[ "${rc}" -ne 0 ]] && grep -qi 'empty Requirements\|no T##' <<<"${out}"; then
  ok "headings-only canvas fails"
else
  bad "expected headings-only fail, rc=${rc} out=${out}"
fi

echo "== Test 2: Metadata Ready For Coding normalizes =="
write_canvas "${WORK}/bare/FEAT-READY.md" "- Readiness: Ready For Coding"
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
Implement YAML-readiness fixture.
## E - Entities
- Widget
## A - Approach
Do the smallest change.
## S - Structure
- src/app.py
## O - Operations
### T01 - Implement fixture
- Status: Not Started
## N - Norms
- One operation
## S - Safeguards
- Do not expand scope
## Review Checklist
- [ ] reviewed
## Sync Notes
fixture
## Final Status
- Status: In Progress
EOF
out="$("${VALIDATE}" "${WORK}/bare/FEAT-YAML.md" 2>&1)"
if grep -q 'readiness: needs-analysis' <<<"${out}"; then ok "yaml readiness"; else bad "yaml: ${out}"; fi

echo "== Test 4: unrecognized readiness warns but exits 0 =="
write_canvas "${WORK}/bare/FEAT-WEIRD.md" "- Readiness: Totally Made Up"
set +e
out="$("${VALIDATE}" "${WORK}/bare/FEAT-WEIRD.md" 2>&1)"
rc=$?
set -e
if [[ "${rc}" -eq 0 ]] && grep -qi 'Warning:.*unrecognized readiness' <<<"${out}"; then
  ok "unknown readiness warns, exit 0"
else
  bad "expected warn+0 got rc=${rc} out=${out}"
fi

echo "== Test 4b: --strict-readiness fails unrecognized =="
set +e
out="$("${VALIDATE}" --strict-readiness "${WORK}/bare/FEAT-WEIRD.md" 2>&1)"
rc=$?
set -e
if [[ "${rc}" -ne 0 ]] && grep -qi 'unrecognized' <<<"${out}"; then
  ok "strict unrecognized fails"
else
  bad "expected strict fail rc=${rc} out=${out}"
fi

echo "== Test 5: Reviewed — Approved With Notes → reviewed =="
write_canvas "${WORK}/bare/FEAT-REV.md" "- Readiness: Reviewed — Approved With Notes"
out="$("${VALIDATE}" "${WORK}/bare/FEAT-REV.md" 2>&1)"
if grep -q 'readiness: reviewed' <<<"${out}"; then ok "reviewed prefix"; else bad "reviewed: ${out}"; fi

echo "== Test 5b: parenthetical annotation stripped =="
write_canvas "${WORK}/bare/FEAT-PAREN.md" "- Readiness: Ready For Coding (implemented on integration)"
out="$("${VALIDATE}" "${WORK}/bare/FEAT-PAREN.md" 2>&1)"
if grep -q 'readiness: ready-for-coding' <<<"${out}" && ! grep -qi 'Warning:.*unrecognized readiness' <<<"${out}"; then
  ok "parenthetical Ready For Coding normalizes"
else
  bad "paren annotate: ${out}"
fi

echo "== Test 5c: architect values Needs Redesign + Blocked =="
write_canvas "${WORK}/bare/FEAT-REDESIGN.md" "- Readiness: Needs Redesign"
out="$("${VALIDATE}" "${WORK}/bare/FEAT-REDESIGN.md" 2>&1)"
if grep -q 'readiness: needs-redesign' <<<"${out}"; then ok "needs-redesign"; else bad "redesign: ${out}"; fi
write_canvas "${WORK}/bare/FEAT-BLOCKED.md" "- Readiness: Blocked"
out="$("${VALIDATE}" "${WORK}/bare/FEAT-BLOCKED.md" 2>&1)"
if grep -q 'readiness: blocked' <<<"${out}"; then ok "blocked"; else bad "blocked: ${out}"; fi

echo "== Test 5d: Ready For Coding in Sync Notes is not structured readiness =="
write_canvas "${WORK}/bare/FEAT-FALSE.md" "" "Remember: Ready For Coding lives only here."
out="$("${VALIDATE}" "${WORK}/bare/FEAT-FALSE.md" 2>&1)"
if grep -q 'readiness: (absent' <<<"${out}"; then
  ok "sync-notes phrase is not Metadata readiness"
else
  bad "false-ready should be absent: ${out}"
fi

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
if grep -q '"validate_cycles": 2' "${stage}" \
  && grep -q '"review_cycles": 1' "${stage}" \
  && grep -q '"metrics"' "${stage}"; then
  ok "capture writes structured metrics object"
else
  bad "missing structured metrics in ${stage}: $(cat "${stage}" 2>/dev/null || true)"
fi

echo "== Test 7: directory validate reports readiness per file =="
T="${WORK}/dir"; mkdir -p "${T}"
write_canvas "${T}/FEAT-A.md" "- Readiness: Ready For Coding"
write_canvas "${T}/FEAT-B.md" "- Readiness: Blocked"
out="$("${VALIDATE}" "${T}" 2>&1)"
if grep -q 'ready-for-coding' <<<"${out}" && grep -q 'blocked' <<<"${out}"; then
  ok "directory validate reports both readiness values"
else
  bad "dir validate: ${out}"
fi

echo "== Test 8: complete / done aliases normalize =="
write_canvas "${WORK}/done.md" "- Readiness: Done"
out="$("${VALIDATE}" "${WORK}/done.md" 2>&1)"
if grep -q 'readiness: complete' <<<"${out}"; then ok "Done → complete"; else bad "done alias: ${out}"; fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
[[ "${fail}" -eq 0 ]]
