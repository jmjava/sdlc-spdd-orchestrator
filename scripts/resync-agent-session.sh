#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage: resync-agent-session.sh --work-id <WORK-ID> [options]

Resync SDLC-SPDD artifacts before starting a new agent session.

Options:
  --target <path>     Target project path (default: .)
  --work-id <WORK-ID> Work ID to resync (required)
  --from-canvas       Copy canonical spdd/canvas/<WORK-ID>.md to feature workspace
  --from-feature      Copy feature workspace canvas to canonical spdd/canvas/<WORK-ID>.md
  --check-only        Check sync state without reconciling
  --phase <phase>     Phase for the generated session brief (default: resume)
  --force             Allow overwriting the destination canvas
  --dry-run           Show sync action without writing
  --help              Print this help message

Examples:
  ./scripts/resync-agent-session.sh --target /path/to/app --work-id FEAT-001-order-status-api --check-only
  ./scripts/resync-agent-session.sh --work-id FEAT-001-order-status-api --from-canvas --force --phase code
EOF
}

TARGET="."
WORK_ID=""
DIRECTION=""
CHECK_ONLY=0
PHASE="resume"
FORCE=0
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
    --from-canvas)
      DIRECTION="--from-canvas"
      shift
      ;;
    --from-feature)
      DIRECTION="--from-feature"
      shift
      ;;
    --check-only)
      CHECK_ONLY=1
      shift
      ;;
    --phase)
      PHASE="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
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

if [[ "${CHECK_ONLY}" -eq 1 && -n "${DIRECTION}" ]]; then
  echo "Error: --check-only cannot be combined with --from-canvas or --from-feature" >&2
  exit 1
fi

TARGET="$(cd "${TARGET}" && pwd)"

sync_args=(--target "${TARGET}" --work-id "${WORK_ID}")
if [[ -n "${DIRECTION}" ]]; then
  sync_args+=("${DIRECTION}")
fi
if [[ "${FORCE}" -eq 1 ]]; then
  sync_args+=(--force)
fi
if [[ "${DRY_RUN}" -eq 1 ]]; then
  sync_args+=(--dry-run)
fi

"${SCRIPT_DIR}/sync-agent-context.sh" "${sync_args[@]}"

canonical_canvas="${TARGET}/spdd/canvas/${WORK_ID}.md"
if [[ -f "${canonical_canvas}" ]]; then
  "${SCRIPT_DIR}/validate-reasons-canvas.sh" "${canonical_canvas}"
else
  echo "Canonical canvas not found after sync check: ${canonical_canvas}" >&2
  exit 1
fi

if [[ "${DRY_RUN}" -eq 0 ]]; then
  "${SCRIPT_DIR}/start-agent-session.sh" --target "${TARGET}" --work-id "${WORK_ID}" --phase "${PHASE}"
else
  echo "[dry-run] would create session brief for ${WORK_ID} phase ${PHASE}"
fi
