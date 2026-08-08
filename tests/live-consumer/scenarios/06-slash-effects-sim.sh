#!/usr/bin/env bash
# Simulate deterministic slash-command side-effects, then verify with
# verify-agent-command-effects.sh. This is the automatable half of Cursor
# slash coverage; pair with CURSOR-SLASH-LIVE.md for real chat invocation.
set -euo pipefail
# shellcheck source=../lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib.sh"

ROOT="${1:?target root required}"
echo "== 06 slash-command effect simulation =="

FEATURE="${ROOT}/agent-context/features/${WORK_ID}"
CANVAS="${ROOT}/spdd/canvas/${WORK_ID}.md"
VERIFY="${ROOT}/scripts/sdlc-spdd/verify-agent-command-effects.sh"

mkdir -p "${FEATURE}" "${ROOT}/spdd/analysis" "${ROOT}/spdd/reviews" "${ROOT}/spdd/sync" \
  "${ROOT}/agent-context/memory" "${ROOT}/session-notes"

# init
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step init >/dev/null; then
  ok "effects: init"
else
  bad "effects: init"
fi

# plan — ensure feature workspace + canvas sections exist (seed canvas already has O/S)
LEAN_PROGRESS="${ROOT}/spdd/memory/entries/progress.md"
mkdir -p "$(dirname "${LEAN_PROGRESS}")"
[[ -f "${FEATURE}/requirement.md" ]] || cp "${ROOT}/requirements/milestones/${WORK_ID}.md" "${FEATURE}/requirement.md"
[[ -f "${LEAN_PROGRESS}" ]] || printf '# Progress\n\n' >"${LEAN_PROGRESS}"
[[ -f "${FEATURE}/progress-log.md" ]] || printf '# Progress\n\n' >"${FEATURE}/progress-log.md"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step plan >/dev/null; then
  ok "effects: plan"
else
  bad "effects: plan"
fi

# architect — readiness marker
if ! grep -Eq 'Ready For Coding|Needs Analysis|Needs Clarification|Needs Redesign|Blocked' "${CANVAS}"; then
  printf '\n- Readiness: Ready For Coding\n' >>"${CANVAS}"
fi
# Promote readiness in metadata for code step soft gate
sed -i 's/^- Readiness: .*/- Readiness: Ready For Coding/' "${CANVAS}"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step architect >/dev/null; then
  ok "effects: architect"
else
  bad "effects: architect"
fi

# analysis artifact (no dedicated effects step; assert file)
printf '# Analysis\n\nScope lock for %s\n' "${WORK_ID}" >"${ROOT}/spdd/analysis/${WORK_ID}-analysis.md"
[[ -f "${ROOT}/spdd/analysis/${WORK_ID}-analysis.md" ]] && ok "effects: analysis artifact" || bad "effects: analysis artifact"

# code — write operation evidence to lean progress (#86); keep legacy mirror for archive compat
printf '\n### T01 - implement\n- Status: Complete\nImplemented greet helper.\nFiles changed: src/hello.py\n' >>"${LEAN_PROGRESS}"
printf '\n### T01 - implement\n- Status: Complete\nImplemented greet helper.\nFiles changed: src/hello.py\n' >>"${FEATURE}/progress-log.md"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step code --operation T01 >/dev/null; then
  ok "effects: code"
else
  bad "effects: code"
fi

# review
printf '# Review\n\nStatus: Approved\n' >"${FEATURE}/review.md"
printf '# Review\n\nStatus: Approved\n' >"${ROOT}/spdd/reviews/${WORK_ID}-review.md"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step review >/dev/null; then
  ok "effects: review"
else
  bad "effects: review"
fi

# sync
printf '# Sync log\n' >"${FEATURE}/sync-log.md"
printf '# Sync\n' >"${ROOT}/spdd/sync/${WORK_ID}-sync.md"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step sync >/dev/null; then
  ok "effects: sync"
else
  bad "effects: sync"
fi

# retro
printf '# Retro\n' >"${FEATURE}/retro.md"
touch "${ROOT}/agent-context/memory/known-pitfalls.md"
touch "${ROOT}/agent-context/memory/reusable-patterns.md"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step retro >/dev/null; then
  ok "effects: retro"
else
  bad "effects: retro"
fi

# prompt-update
LEDGER="${ROOT}/agent-context/memory/prompt-optimization-log.md"
if [[ ! -f "${LEDGER}" ]]; then
  printf '# Prompt optimization log\n\n' >"${LEDGER}"
fi
printf '\n- %s: clarified acceptance criteria during live matrix\n' "${WORK_ID}" >>"${LEDGER}"
if "${VERIFY}" --target "${ROOT}" --work-id "${WORK_ID}" --step prompt-update >/dev/null; then
  ok "effects: prompt-update"
else
  bad "effects: prompt-update"
fi

# capture (after real capture-session-memory already ran in 03; re-run to be sure)
"${ROOT}/scripts/sdlc-spdd/capture-session-memory.sh" \
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
