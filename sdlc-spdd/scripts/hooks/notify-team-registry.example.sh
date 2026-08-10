#!/usr/bin/env bash
# Example SDLC_TEAM_REGISTRY_HOOK — copy to agent-context/hooks/notify-team-registry.sh
# and set: export SDLC_TEAM_REGISTRY_HOOK=./agent-context/hooks/notify-team-registry.sh
#
# Args: work_id status phase operation owner updated note
#
# Slack (set SDLC_TEAM_SLACK_WEBHOOK):
#   https://api.slack.com/messaging/webhooks

set -euo pipefail

work_id="${1:-}"
status="${2:-}"
phase="${3:-}"
operation="${4:-}"
owner="${5:-}"
updated="${6:-}"
note="${7:-}"

message="SDLC registry: *${work_id}* → ${status} (phase: ${phase}, op: ${operation:-none}, by: ${owner})"
[[ -n "${note}" ]] && message+=" — ${note}"

if [[ -n "${SDLC_TEAM_SLACK_WEBHOOK:-}" ]]; then
  payload="$(printf '{"text":"%s"}' "${message//\"/\\\"}")"
  curl -fsS -X POST -H 'Content-type: application/json' \
    --data "${payload}" \
    "${SDLC_TEAM_SLACK_WEBHOOK}" >/dev/null 2>&1 || true
fi

# Jira (optional — set SDLC_TEAM_JIRA_WEBHOOK to a script or URL your team approves):
if [[ -n "${SDLC_TEAM_JIRA_WEBHOOK:-}" ]]; then
  curl -fsS -X POST -H 'Content-type: application/json' \
    --data "{\"work_id\":\"${work_id}\",\"status\":\"${status}\",\"owner\":\"${owner}\",\"note\":\"${note}\"}" \
    "${SDLC_TEAM_JIRA_WEBHOOK}" >/dev/null 2>&1 || true
fi

echo "${message}"
