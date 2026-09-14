#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib/common.sh"

usage() {
  cat <<'EOF'
Usage: resync-agent-session.sh --work-id <WORK-ID> [options]

Validate storage-v3 artifacts before starting a new agent session.

Options:
  --target <path>     Target project path (default: .)
  --work-id <WORK-ID> Work ID to resync (required)
  --check-only        Validate the canvas without creating a session brief
  --phase <phase>     Phase for the generated session brief (default: resume)
  --dry-run           Validate without creating a session brief
  --help              Print this help message

Examples:
  ./scripts/resync-agent-session.sh --target /path/to/app --work-id FEAT-001-order-status-api --check-only
  ./sdlc-spdd/scripts/resync-agent-session.sh --work-id FEAT-001-order-status-api --phase code
EOF
}

TARGET="."
WORK_ID=""
CHECK_ONLY=0
PHASE="resume"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --work-id)
      WORK_ID="${2:-}"
      shift 2
      ;;
    --check-only)
      CHECK_ONLY=1
      shift
      ;;
    --phase)
      PHASE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${WORK_ID}" ]]; then
  echo "Error: --work-id is required" >&2
  usage >&2
  exit 1
fi

canonical_canvas="${SDLC_HOME:-${TARGET}/sdlc-spdd}/spdd/canvas/${WORK_ID}.md"
if [[ -f "${canonical_canvas}" ]]; then
  "${SCRIPT_DIR}/validate-reasons-canvas.sh" "${canonical_canvas}"
else
  echo "Canvas not found: ${canonical_canvas}" >&2
  exit 1
fi

if [[ "${CHECK_ONLY}" -eq 1 ]]; then
  echo "Check complete. Run start-agent-session.sh to create a session brief."
elif [[ "${DRY_RUN}" -eq 0 ]]; then
  "${SCRIPT_DIR}/start-agent-session.sh" --target "${TARGET}" --work-id "${WORK_ID}" --phase "${PHASE}"
else
  echo "[dry-run] would create session brief for ${WORK_ID} phase ${PHASE}"
fi
