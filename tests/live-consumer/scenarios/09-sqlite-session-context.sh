#!/usr/bin/env bash
# CI-safe: db rebuild → start-agent-session → brief contains SQLite lookup.
set -euo pipefail
# shellcheck source=../lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib.sh"

ROOT="${1:?target root required}"
HOME="$(live_home "${ROOT}")"
echo "== 09 sqlite session context =="

if ! PYTHONPATH="${REPO_ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
  python3 -c 'import sdlc_engine' 2>/dev/null; then
  skipped "sdlc_engine not importable"
  exit 0
fi

export PYTHONPATH="${REPO_ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}"

# Ensure claim + canvas so rebuild indexes a real work item.
live_sdlc "${ROOT}" claim "${WORK_ID}" --force >/dev/null 2>&1 || true
if [[ ! -f "${HOME}/spdd/canvas/${WORK_ID}.md" ]]; then
  mkdir -p "${HOME}/spdd/canvas" "${HOME}/requirements/milestones"
  printf '# REASONS Canvas: %s\n\n## Metadata\n\n- Work ID: %s\n- Status: In Progress\n- Readiness: Ready For Coding\n\n## Final Status\n\n- Status: In Progress\n' \
    "${WORK_ID}" "${WORK_ID}" >"${HOME}/spdd/canvas/${WORK_ID}.md"
  printf '# requirement\n' >"${HOME}/requirements/milestones/${WORK_ID}.md"
fi

if PYTHONPATH="${PYTHONPATH}" python3 -m sdlc_engine --root "${ROOT}" db rebuild >/dev/null; then
  ok "db rebuild"
else
  bad "db rebuild"
fi

lookup_json="$(
  PYTHONPATH="${PYTHONPATH}" python3 -m sdlc_engine --root "${ROOT}" db lookup \
    --work-id "${WORK_ID}" --json 2>/dev/null || true
)"
if grep -Fq "\"work_id\": \"${WORK_ID}\"" <<<"${lookup_json}" \
  || grep -Fq "\"${WORK_ID}\"" <<<"${lookup_json}"; then
  ok "db lookup json returns work_id"
else
  bad "db lookup json missing work_id"
fi

# Fresh start-agent-session must embed the markdown lookup section.
# Prefer target script (install copies start-agent-session); fall back to orchestrator.
START="${HOME}/scripts/start-agent-session.sh"
if [[ ! -x "${START}" ]]; then
  START="${REPO_ROOT}/scripts/start-agent-session.sh"
fi

if [[ -f "${REPO_ROOT}/scripts/start-agent-session.sh" ]]; then
  cp "${REPO_ROOT}/scripts/start-agent-session.sh" "${HOME}/scripts/start-agent-session.sh"
  chmod +x "${HOME}/scripts/start-agent-session.sh"
  START="${HOME}/scripts/start-agent-session.sh"
fi

if PYTHONPATH="${PYTHONPATH}" "${START}" \
  --target "${ROOT}" \
  --work-id "${WORK_ID}" \
  --phase code >/dev/null; then
  ok "start-agent-session"
else
  bad "start-agent-session"
fi

BRIEF="${HOME}/.sdlc/sessions/current-session.md"
[[ -f "${BRIEF}" ]] && ok "current-session.md exists" || bad "current-session.md missing"

if grep -Fq 'Local SQLite Index (query cache)' "${BRIEF}"; then
  ok "brief contains Local SQLite Index section"
else
  bad "brief missing Local SQLite Index section"
fi

if grep -Fq "${WORK_ID}" "${BRIEF}" \
  && grep -Eq 'has_canvas|registry_status' "${BRIEF}"; then
  ok "brief lookup includes work_id + indexed fields"
else
  bad "brief lookup incomplete"
fi

if grep -Fq 'Local SQLite Index (query cache)' "${BRIEF}" \
  && grep -Fq 'Resume Prompt' "${BRIEF}" \
  && awk '/## Resume Prompt/,0' "${BRIEF}" | grep -Fq 'Local SQLite Index'; then
  ok "resume prompt references SQLite lookup"
else
  bad "resume prompt missing SQLite lookup hint"
fi
