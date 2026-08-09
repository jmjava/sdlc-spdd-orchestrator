#!/usr/bin/env bash
# Simulate deterministic slash-command side-effects, then verify with
# verify-agent-command-effects.sh (storage v3 contract paths only).
set -euo pipefail
# shellcheck source=../lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib.sh"

ROOT="${1:?target root required}"
HOME="$(live_home "${ROOT}")"
echo "== 06 slash-command effect simulation =="

CANVAS="${HOME}/spdd/canvas/${WORK_ID}.md"
MILESTONE="${HOME}/requirements/milestones/${WORK_ID}.md"
STAGE="${HOME}/.sdlc/staged/lessons.jsonl"
LEDGER="${HOME}/spdd/memory/lessons.jsonl"
VERIFY="${HOME}/scripts/verify-agent-command-effects.sh"

mkdir -p "${HOME}/spdd/analysis" "${HOME}/spdd/reviews" "${HOME}/spdd/sync" \
  "${HOME}/session-notes" "$(dirname "${STAGE}")"

# init
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step init >/dev/null; then
  ok "effects: init"
else
  bad "effects: init"
fi

# plan — canvas + milestone requirement
[[ -f "${MILESTONE}" ]] || printf '# Requirement: %s\n' "${WORK_ID}" >"${MILESTONE}"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step plan >/dev/null; then
  ok "effects: plan"
else
  bad "effects: plan"
fi

# architect — readiness marker
if ! grep -Eq 'Ready For Coding|Needs Analysis|Needs Clarification|Needs Redesign|Blocked' "${CANVAS}"; then
  printf '\n- Readiness: Ready For Coding\n' >>"${CANVAS}"
fi
sed -i 's/^- Readiness: .*/- Readiness: Ready For Coding/' "${CANVAS}"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step architect >/dev/null; then
  ok "effects: architect"
else
  bad "effects: architect"
fi

# analysis artifact
printf '# Analysis\n\nScope lock for %s\n' "${WORK_ID}" >"${HOME}/spdd/analysis/${WORK_ID}-analysis.md"
[[ -f "${HOME}/spdd/analysis/${WORK_ID}-analysis.md" ]] && ok "effects: analysis artifact" || bad "effects: analysis artifact"

# code — staged session evidence for operation T01
printf '%s\n' \
  "{\"id\":\"session:${WORK_ID}:(none):capture\",\"kind\":\"session\",\"work_id\":\"${WORK_ID}\",\"area\":\"\",\"phase\":\"code\",\"ts\":\"2026-08-08T00:00:00Z\",\"title\":\"T01 implement\",\"body\":\"### T01 - implement\\n- Status: Complete\\nImplemented greet helper.\\nFiles changed: src/hello.py\",\"source\":\"capture\",\"keywords\":[],\"schema\":1}" \
  >>"${STAGE}"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step code --operation T01 >/dev/null; then
  ok "effects: code"
else
  bad "effects: code"
fi

# review
printf '# Review\n\nStatus: Approved\n' >"${HOME}/spdd/reviews/${WORK_ID}-review.md"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step review >/dev/null; then
  ok "effects: review"
else
  bad "effects: review"
fi

# sync
printf '# Sync\n' >"${HOME}/spdd/sync/${WORK_ID}-sync.md"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step sync >/dev/null; then
  ok "effects: sync"
else
  bad "effects: sync"
fi

# retro — promote staged session into committed ledger
mkdir -p "$(dirname "${LEDGER}")"
grep -F "\"work_id\": \"${WORK_ID}\"" "${STAGE}" >>"${LEDGER}" || true
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step retro >/dev/null; then
  ok "effects: retro"
else
  bad "effects: retro"
fi

# prompt-update — additional staged record
if ! grep -Fq 'prompt update' "${STAGE}" 2>/dev/null; then
  printf '%s\n' \
    "{\"id\":\"session:${WORK_ID}:(none):prompt\",\"kind\":\"session\",\"work_id\":\"${WORK_ID}\",\"area\":\"\",\"phase\":\"prompt-update\",\"ts\":\"2026-08-08T00:00:00Z\",\"title\":\"prompt update\",\"body\":\"clarified acceptance criteria during live matrix\",\"source\":\"capture\",\"keywords\":[],\"schema\":1}" \
    >>"${STAGE}"
fi
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step prompt-update >/dev/null; then
  ok "effects: prompt-update"
else
  bad "effects: prompt-update"
fi

# capture (after real capture-session-memory already ran in 03; re-run to be sure)
"${HOME}/scripts/capture-session-memory.sh" \
  --target "${ROOT}" \
  --work-id "${WORK_ID}" \
  --phase code \
  --summary "live matrix code capture" >/dev/null || true
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step capture >/dev/null; then
  ok "effects: capture"
else
  bad "effects: capture"
fi

# whereami / workflow slash commands are wrappers — assert CLI parity
live_sdlc "${ROOT}" claim "${WORK_ID}" --force >/dev/null 2>&1 || true
live_sdlc "${ROOT}" next >/dev/null && ok "slash-parity: next via shell" || bad "slash-parity: next"
live_sdlc "${ROOT}" team >/dev/null && ok "slash-parity: team via shell" || bad "slash-parity: team"
