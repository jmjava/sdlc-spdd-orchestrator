#!/usr/bin/env bash
# Print Cursor / VS Code MCP config snippet for local Guide (spdd_* tools).
#
# Copy the JSON into your user or workspace MCP settings, or merge with embabel-dev.
#
# Usage:
#   ./scripts/guide/mcp-config-snippet.sh
#   GUIDE_PORT=21337 ./scripts/guide/mcp-config-snippet.sh --cursor
set -euo pipefail

PORT="${GUIDE_PORT:-21337}"
HOST="${GUIDE_HOST:-127.0.0.1}"
URL="http://${HOST}:${PORT}/sse"
NAME="${MCP_SERVER_NAME:-sdlc-spdd-guide}"

MODE="generic"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cursor) MODE="cursor" ;;
    --copilot) MODE="copilot" ;;
    -h|--help)
      sed -n '1,12p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

cat <<EOF
# Guide MCP at ${URL}
# Native spdd_* tools: spdd_workSubgraph, spdd_areaLessons, spdd_findByLabel,
# spdd_projectionStats, spdd_getLesson
#
# CLI fallback (same data, no MCP in IDE):
#   ./scripts/guide/query-guide.sh --work-id <WORK-ID>
#   SDLC_ENGINE=python ./scripts/sdlc.sh context guide-query --work-id <WORK-ID> --text
EOF

if [[ "${MODE}" == "cursor" ]]; then
  cat <<JSON
{
  "mcpServers": {
    "${NAME}": {
      "url": "${URL}"
    }
  }
}
JSON
else
  cat <<JSON
{
  "servers": {
    "${NAME}": {
      "type": "sse",
      "url": "${URL}"
    }
  }
}
JSON
fi
