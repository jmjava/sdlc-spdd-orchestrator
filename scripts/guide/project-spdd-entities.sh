#!/usr/bin/env bash
# SPIKE-001 leg 3 — POST Guide spdd-projection/load for orchestrator or fixture root.
# Optional 2nd arg: Work ID to fetch GET …/work/{workId} subgraph after load.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GUIDE_PORT="${GUIDE_PORT:-21337}"
ROOT_PATH="${1:-${REPO_ROOT}}"
WORK_ID="${2:-}"

url="http://localhost:${GUIDE_PORT}/api/v1/data/spdd-projection/load"
stats_url="http://localhost:${GUIDE_PORT}/api/v1/data/spdd-projection/stats"

if ! curl -sf --max-time 3 "${stats_url}" >/dev/null 2>&1; then
  echo "Guide not reachable at ${stats_url}" >&2
  echo "Ensure guide runs sdlc-spdd-projection-v2 (or main) with guide.spdd-projection.enabled=true" >&2
  exit 1
fi

echo "Projecting SPDD entities from: ${ROOT_PATH}"
curl -s -X POST "${url}" \
  -H 'Content-Type: application/json' \
  -d "{\"rootPath\":\"${ROOT_PATH}\"}" | jq .

echo ""
echo "Entity stats:"
curl -s "${stats_url}" | jq .

if [[ -n "${WORK_ID}" ]]; then
  echo ""
  echo "WorkId subgraph: ${WORK_ID}"
  curl -s "http://localhost:${GUIDE_PORT}/api/v1/data/spdd-projection/work/${WORK_ID}" | jq .
fi
