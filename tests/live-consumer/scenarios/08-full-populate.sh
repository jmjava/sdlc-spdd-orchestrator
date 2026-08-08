#!/usr/bin/env bash
# Fully populate every capture / memory / planning artifact and assert
# no "Not recorded" / empty placeholder fields remain on staged records.
set -euo pipefail
# shellcheck source=../lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib.sh"

ROOT="${1:?target root required}"
echo "== 08 full populate (no empty capture fields) =="

HOME="${ROOT}/sdlc-spdd"
SCRIPTS="${HOME}/scripts"
CANVAS="${HOME}/spdd/canvas/${WORK_ID}.md"
STAGE="${HOME}/.sdlc/staged/lessons.jsonl"
LEDGER="${HOME}/spdd/memory/lessons.jsonl"
MILESTONE_REL="requirements/milestones/milestone-1/MILESTONE-1.md"
MILESTONE="${HOME}/${MILESTONE_REL}"
SESSION="${HOME}/.sdlc/sessions/current-session.md"

mkdir -p "${HOME}/spdd/analysis" "${HOME}/spdd/reviews" "${HOME}/spdd/sync" \
  "${HOME}/session-notes" "${HOME}/requirements/milestones"

[[ -f "${HOME}/requirements/milestones/${WORK_ID}.md" ]] \
  || cp "${ROOT}/requirements/milestones/${WORK_ID}.md" "${HOME}/requirements/milestones/${WORK_ID}.md" 2>/dev/null \
  || printf '# Requirement: %s\n' "${WORK_ID}" >"${HOME}/requirements/milestones/${WORK_ID}.md"

# --- Populate lifecycle artifacts as a real session would ---
LEAN_PROGRESS="${HOME}/spdd/memory/entries/progress.md"
mkdir -p "$(dirname "${LEAN_PROGRESS}")"
[[ -f "${LEAN_PROGRESS}" ]] || printf '# Progress Log: %s\n\n' "${WORK_ID}" >"${LEAN_PROGRESS}"

sed -i 's/^- Readiness: .*/- Readiness: Ready For Coding/' "${CANVAS}"
sed -i 's/^- Status: .*/- Status: In Progress/' "${CANVAS}"
# Mark T01 complete in canvas operations
if grep -q '### T01' "${CANVAS}"; then
  sed -i '/### T01/,/### T02/{s/- Status: Not Started/- Status: Complete/}' "${CANVAS}"
fi

printf '# Analysis\n\nScope lock and constraints for %s.\n' "${WORK_ID}" \
  >"${HOME}/spdd/analysis/${WORK_ID}-analysis.md"
printf '# Review\n\nStatus: Approved\n\nAll acceptance criteria met for T01.\n' \
  >"${HOME}/spdd/reviews/${WORK_ID}-review.md"
printf '# Sync\n\nNo drift detected after live matrix populate.\n' \
  >"${HOME}/spdd/sync/${WORK_ID}-sync.md"

printf '\n### T01 - implement greet\n- Status: Complete\nImplemented greet helper.\nFiles changed: src/hello.py\n' \
  >>"${LEAN_PROGRESS}"

# Ensure milestone + roadmap exist (install creates them; seed keeps FEAT req).
[[ -f "${MILESTONE}" ]] && ok "milestone present (${MILESTONE_REL})" || bad "milestone missing"
[[ -f "${HOME}/ROADMAP.md" ]] && ok "ROADMAP.md present" || bad "ROADMAP.md missing"

# Claim + session brief so capture has rich area parsing sources.
live_sdlc "${ROOT}" claim "${WORK_ID}" --force >/dev/null 2>&1 || true
"${SCRIPTS}/start-agent-session.sh" \
  --target "${ROOT}" \
  --work-id "${WORK_ID}" \
  --phase code \
  --milestone "${MILESTONE_REL}" >/dev/null

SUMMARY="FEAT-001 T01: implemented greet() in src/hello.py; live consumer matrix full-populate pass"
VALIDATION="./tests/test-live-consumer-matrix.sh (72+ checks) + python3 -c greet assert"
DECISIONS="Use ephemeral seeded git consumer (/tmp wipe) instead of a durable sibling repo"
PITFALLS="Sparse capture leaves Validation/Next as Not recorded; always pass full capture flags"
PATTERNS="seed→install→populate→assert→flush; keep /tmp/sdlc-spdd-live only for Cursor slash live"
ROADMAP_NOTE="Live consumer matrix fully populates memory, milestone, and roadmap on every run"
NEXT_STEP="/sdlc-spdd-review @spdd/canvas/${WORK_ID}.md"

if "${SCRIPTS}/capture-session-memory.sh" \
  --target "${ROOT}" \
  --work-id "${WORK_ID}" \
  --phase code \
  --summary "${SUMMARY}" \
  --validation "${VALIDATION}" \
  --decisions "${DECISIONS}" \
  --pitfalls "${PITFALLS}" \
  --patterns "${PATTERNS}" \
  --areas "src/hello.py, tests/live-consumer, scripts/sdlc-spdd" \
  --milestone "${MILESTONE_REL}" \
  --roadmap-note "${ROADMAP_NOTE}" \
  --next "${NEXT_STEP}" \
  --readiness "Ready For Coding" \
  --review-result pass \
  --rework 0 \
  --context-files 18 \
  --validate-cycles 1 \
  --review-cycles 1 >/dev/null; then
  ok "full capture-session-memory"
else
  bad "full capture-session-memory"
fi

[[ -f "${STAGE}" ]] && ok "staged lessons present" || bad "staged lessons missing"

session_line="$(grep '"kind": "session"' "${STAGE}" | tail -n 1 || true)"
decision_line="$(grep '"kind": "decision"' "${STAGE}" | tail -n 1 || true)"
pitfall_line="$(grep '"kind": "pitfall"' "${STAGE}" | tail -n 1 || true)"
pattern_line="$(grep '"kind": "pattern"' "${STAGE}" | tail -n 1 || true)"

assert_staged_field() {
  local label="$1"
  local line="$2"
  local text="$3"
  if [[ -z "${line}" ]]; then
    bad "staged ${label} record missing"
    return
  fi
  if grep -Fq "${text}" <<<"${line}"; then
    ok "staged ${label} populated"
  else
    bad "staged ${label} missing ${text}"
  fi
}

assert_staged_field "session" "${session_line}" "${VALIDATION}"
assert_staged_field "session" "${session_line}" "${NEXT_STEP}"
assert_staged_field "session" "${session_line}" "${SUMMARY}"
grep -Fq 'readiness=Ready For Coding' <<<"${session_line}" \
  && ok "staged session readiness metric" || bad "staged session readiness metric"
grep -Fq 'review-result=pass' <<<"${session_line}" \
  && ok "staged session review-result metric" || bad "staged session review-result metric"
assert_staged_field "decision" "${decision_line}" "${DECISIONS}"
assert_staged_field "pitfall" "${pitfall_line}" "${PITFALLS}"
assert_staged_field "pattern" "${pattern_line}" "${PATTERNS}"

for kind in session decision pitfall pattern; do
  if grep -Fq "\"kind\": \"${kind}\"" "${STAGE}"; then
    ok "staged record kind ${kind}"
  else
    bad "staged record kind ${kind} missing"
  fi
done

if [[ -f "${SESSION}" ]] \
  && grep -Fq "## Captured Memory" "${SESSION}" \
  && grep -Fq "${SUMMARY}" "${SESSION}" \
  && grep -Fq "${VALIDATION}" "${SESSION}"; then
  ok "current-session capture summary populated"
else
  bad "current-session capture summary incomplete"
fi

# Planning docs updated
grep -Fq "${WORK_ID}" "${MILESTONE}" && ok "milestone mentions work" || bad "milestone missing work"
grep -Fq "${ROADMAP_NOTE}" "${HOME}/ROADMAP.md" && ok "ROADMAP note written" || bad "ROADMAP note missing"
grep -Fq "${NEXT_STEP}" "${HOME}/ROADMAP.md" && ok "ROADMAP next written" || bad "ROADMAP next missing"

# Lean progress log still carries operation evidence for code step checks
grep -Fq "${WORK_ID}" "${LEAN_PROGRESS}" \
  && grep -Fq "src/hello.py" "${LEAN_PROGRESS}" \
  && ok "lean progress operation evidence" || bad "lean progress incomplete"

# Official effects verifier with roadmap gate
if "${SCRIPTS}/verify-agent-command-effects.sh" \
  --target "${ROOT}" \
  --work-id "${WORK_ID}" \
  --step capture \
  --milestone "${MILESTONE_REL}" \
  --require-roadmap >/dev/null; then
  ok "verify effects: capture + milestone + roadmap"
else
  bad "verify effects: capture + milestone + roadmap"
fi

# Phase effect steps still green after full populate
for step in init plan architect code review sync retro prompt-update; do
  if [[ "${step}" == "prompt-update" ]]; then
    if [[ ! -f "${STAGE}" ]] || ! grep -Fq "${WORK_ID}" "${STAGE}"; then
      printf '%s\n' \
        "{\"id\":\"session:${WORK_ID}:(none):capture\",\"kind\":\"session\",\"work_id\":\"${WORK_ID}\",\"area\":\"\",\"phase\":\"prompt-update\",\"ts\":\"2026-08-08T00:00:00Z\",\"title\":\"prompt update\",\"body\":\"full-populate prompt refinement\",\"source\":\"capture\",\"keywords\":[],\"schema\":1}" \
        >>"${STAGE}"
    fi
  fi
  if [[ "${step}" == "retro" ]]; then
    if [[ ! -f "${LEDGER}" ]] || ! grep -Fq "\"work_id\": \"${WORK_ID}\"" "${LEDGER}"; then
      printf '%s\n' \
        "{\"id\":\"session:${WORK_ID}:(none):capture\",\"kind\":\"session\",\"work_id\":\"${WORK_ID}\",\"area\":\"\",\"phase\":\"retro\",\"ts\":\"2026-08-08T00:00:00Z\",\"title\":\"retro\",\"body\":\"accepted retro evidence\",\"source\":\"capture\",\"keywords\":[],\"schema\":1}" \
        >>"${LEDGER}"
    fi
  fi
  if "${SCRIPTS}/verify-agent-command-effects.sh" \
    --target "${ROOT}" --work-id "${WORK_ID}" --step "${step}" --operation T01 >/dev/null; then
    ok "verify effects: ${step}"
  else
    bad "verify effects: ${step}"
  fi
done

echo "  golden staged lessons: ${STAGE}"
echo "  golden milestone: ${MILESTONE}"
echo "  golden roadmap: ${HOME}/ROADMAP.md"
