#!/usr/bin/env bash
# Fully populate every capture / memory / planning artifact and assert
# no "Not recorded" / empty placeholder fields remain on the golden entry.
set -euo pipefail
# shellcheck source=../lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib.sh"

ROOT="${1:?target root required}"
echo "== 08 full populate (no empty capture fields) =="

SCRIPTS="${ROOT}/scripts/sdlc-spdd"
FEATURE="${ROOT}/agent-context/features/${WORK_ID}"
CANVAS="${ROOT}/spdd/canvas/${WORK_ID}.md"
MEM="${ROOT}/agent-context/memory"
MILESTONE_REL="requirements/milestones/milestone-1/MILESTONE-1.md"
MILESTONE="${ROOT}/${MILESTONE_REL}"
HISTORY="${MEM}/session-history.md"

mkdir -p "${FEATURE}" "${ROOT}/spdd/analysis" "${ROOT}/spdd/reviews" "${ROOT}/spdd/sync" \
  "${MEM}" "${ROOT}/session-notes"

# --- Populate lifecycle artifacts as a real session would ---
LEAN_PROGRESS="${ROOT}/spdd/memory/entries/progress.md"
mkdir -p "$(dirname "${LEAN_PROGRESS}")"
[[ -f "${FEATURE}/requirement.md" ]] || cp "${ROOT}/requirements/milestones/${WORK_ID}.md" "${FEATURE}/requirement.md"
[[ -f "${LEAN_PROGRESS}" ]] || printf '# Progress Log: %s\n\n' "${WORK_ID}" >"${LEAN_PROGRESS}"
[[ -f "${FEATURE}/progress-log.md" ]] || printf '# Progress Log: %s\n\n' "${WORK_ID}" >"${FEATURE}/progress-log.md"

sed -i 's/^- Readiness: .*/- Readiness: Ready For Coding/' "${CANVAS}"
sed -i 's/^- Status: .*/- Status: In Progress/' "${CANVAS}"
# Mark T01 complete in canvas operations
if grep -q '### T01' "${CANVAS}"; then
  sed -i '/### T01/,/### T02/{s/- Status: Not Started/- Status: Complete/}' "${CANVAS}"
fi

printf '# Analysis\n\nScope lock and constraints for %s.\n' "${WORK_ID}" \
  >"${ROOT}/spdd/analysis/${WORK_ID}-analysis.md"
printf '# Review\n\nStatus: Approved\n\nAll acceptance criteria met for T01.\n' \
  >"${FEATURE}/review.md"
cp "${FEATURE}/review.md" "${ROOT}/spdd/reviews/${WORK_ID}-review.md"
printf '# Sync log\n\nCanvas, requirement, and milestone aligned.\n' \
  >"${FEATURE}/sync-log.md"
printf '# Sync\n\nNo drift detected after live matrix populate.\n' \
  >"${ROOT}/spdd/sync/${WORK_ID}-sync.md"
printf '# Retro\n\nWhat went well: seed/flush matrix.\nWhat to improve: always pass full capture flags.\n' \
  >"${FEATURE}/retro.md"

printf '\n### T01 - implement greet\n- Status: Complete\nImplemented greet helper.\nFiles changed: src/hello.py\n' \
  >>"${LEAN_PROGRESS}"
printf '\n### T01 - implement greet\n- Status: Complete\nImplemented greet helper.\nFiles changed: src/hello.py\n' \
  >>"${FEATURE}/progress-log.md"

# Ensure milestone + roadmap exist (install creates them; seed keeps FEAT req).
[[ -f "${MILESTONE}" ]] && ok "milestone present (${MILESTONE_REL})" || bad "milestone missing"
[[ -f "${ROOT}/ROADMAP.md" ]] && ok "ROADMAP.md present" || bad "ROADMAP.md missing"

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

# Extract the latest session entry block from session-history.md
latest="$(awk '
  /^### / { buf=""; in_entry=1 }
  in_entry { buf = buf $0 ORS }
  END { printf "%s", buf }
' "${HISTORY}")"

assert_field_filled() {
  local label="$1"
  local pattern="$2"
  local empty_re="$3"
  if ! grep -Eq "${pattern}" <<<"${latest}"; then
    bad "latest entry missing ${label}"
    return
  fi
  if grep -Eq "${empty_re}" <<<"${latest}"; then
    bad "latest entry ${label} still empty/placeholder"
    return
  fi
  ok "latest entry ${label} populated"
}

assert_field_filled "Validation" '^- Validation: ' '^- Validation: (Not recorded)?$'
assert_field_filled "Decisions" '^- Decisions: ' '^- Decisions: (None)?$'
assert_field_filled "Pitfalls" '^- Pitfalls: ' '^- Pitfalls: (None)?$'
assert_field_filled "Reusable patterns" '^- Reusable patterns: ' '^- Reusable patterns: (None)?$'
assert_field_filled "Milestone" '^- Milestone: ' '^- Milestone: (None)?$'
assert_field_filled "Roadmap note" '^- Roadmap note: ' '^- Roadmap note: (None)?$'
assert_field_filled "Next" '^- Next: ' '^- Next: (Not recorded)?$'
assert_field_filled "Metrics" '^- Metrics: ' '^- Metrics: $'
assert_field_filled "Code areas" '^- Code areas: ' '^- Code areas: (none)?$'

# Exact content anchors
grep -Fq "${VALIDATION}" <<<"${latest}" && ok "validation text present" || bad "validation text missing"
grep -Fq "${DECISIONS}" <<<"${latest}" && ok "decisions text present" || bad "decisions text missing"
grep -Fq "${PITFALLS}" <<<"${latest}" && ok "pitfalls text present" || bad "pitfalls text missing"
grep -Fq "${PATTERNS}" <<<"${latest}" && ok "patterns text present" || bad "patterns text missing"
grep -Fq "${MILESTONE_REL}" <<<"${latest}" && ok "milestone path recorded" || bad "milestone path missing"
grep -Fq "${ROADMAP_NOTE}" <<<"${latest}" && ok "roadmap note recorded" || bad "roadmap note missing"
grep -Fq "${NEXT_STEP}" <<<"${latest}" && ok "next step recorded" || bad "next step missing"
grep -Eq 'readiness=Ready For Coding|readiness=ready-for-coding' <<<"${latest}" \
  && ok "readiness metric recorded" || bad "readiness metric missing"
grep -Fq 'review-result=pass' <<<"${latest}" && ok "review-result metric" || bad "review-result metric"

# Durable memory files received appends
grep -Fq "${DECISIONS}" "${MEM}/architecture-decisions.md" \
  && ok "architecture-decisions.md appended" || bad "architecture-decisions.md"
grep -Fq "${PITFALLS}" "${MEM}/known-pitfalls.md" \
  && ok "known-pitfalls.md appended" || bad "known-pitfalls.md"
grep -Fq "${PATTERNS}" "${MEM}/reusable-patterns.md" \
  && ok "reusable-patterns.md appended" || bad "reusable-patterns.md"
grep -Fq "${WORK_ID}" "${MEM}/project-memory.md" \
  && ok "project-memory.md updated" || bad "project-memory.md"
grep -Fq "${WORK_ID}" "${MEM}/session-index.md" \
  && ok "session-index.md updated" || bad "session-index.md"

# Context index kinds
for kind in session decision pitfall pattern metric; do
  if grep -Eq "\\| ${kind} \\|" "${MEM}/context-index.md"; then
    ok "context-index has ${kind} rows"
  else
    bad "context-index missing ${kind} rows"
  fi
done

# Per-session entry file exists
entry_count="$(find "${MEM}/sessions" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
[[ "${entry_count}" -ge 1 ]] && ok "per-session memory files (${entry_count})" || bad "no per-session files"

# Planning docs updated
grep -Fq "${WORK_ID}" "${MILESTONE}" && ok "milestone mentions work" || bad "milestone missing work"
grep -Fq "${ROADMAP_NOTE}" "${ROOT}/ROADMAP.md" && ok "ROADMAP note written" || bad "ROADMAP note missing"
grep -Fq "${NEXT_STEP}" "${ROOT}/ROADMAP.md" && ok "ROADMAP next written" || bad "ROADMAP next missing"

# Daily session note
note="$(ls -1t "${ROOT}/session-notes"/*.md 2>/dev/null | head -n 1 || true)"
if [[ -n "${note}" ]] && grep -Fq "${WORK_ID}" "${note}" && grep -Fq "${VALIDATION}" "${note}"; then
  ok "session-notes fully populated"
else
  bad "session-notes incomplete"
fi

# Lean progress log includes full capture header (#86)
PROGRESS="${ROOT}/spdd/memory/entries/progress.md"
grep -Fq "${WORK_ID}" "${PROGRESS}" \
  && grep -Fq "${VALIDATION}" "${PROGRESS}" \
  && ok "lean progress full capture" || bad "lean progress incomplete"

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
    # ensure ledger mentions work
    if [[ ! -f "${MEM}/prompt-optimization-log.md" ]] \
      || ! grep -Fq "${WORK_ID}" "${MEM}/prompt-optimization-log.md"; then
      printf '\n- %s: full-populate prompt refinement\n' "${WORK_ID}" >>"${MEM}/prompt-optimization-log.md"
    fi
  fi
  if "${SCRIPTS}/verify-agent-command-effects.sh" \
    --target "${ROOT}" --work-id "${WORK_ID}" --step "${step}" --operation T01 >/dev/null; then
    ok "verify effects: ${step}"
  else
    bad "verify effects: ${step}"
  fi
done

# Dump golden entry path for humans inspecting /tmp/sdlc-spdd-live
echo "  golden session-history: ${HISTORY}"
echo "  golden milestone: ${MILESTONE}"
echo "  golden roadmap: ${ROOT}/ROADMAP.md"
