#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: sync-agent-context.sh --work-id <WORK-ID> [--from-canvas|--from-feature] [--dry-run] [--force]

Synchronize feature workspace canvas with canonical spdd/canvas copy.
EOF
}

WORK_ID=""
DIRECTION=""
DRY_RUN=0
FORCE=0
TARGET="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --work-id)
      WORK_ID="${2:-}"
      shift 2
      ;;
    --from-canvas)
      DIRECTION="from-canvas"
      shift
      ;;
    --from-feature)
      DIRECTION="from-feature"
      shift
      ;;
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --force)
      FORCE=1
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
  exit 1
fi

TARGET="$(cd "${TARGET}" && pwd)"
feature_canvas="${TARGET}/agent-context/features/${WORK_ID}/reasons-canvas.md"
canonical_canvas="${TARGET}/spdd/canvas/${WORK_ID}.md"

if [[ ! -f "${feature_canvas}" && ! -f "${canonical_canvas}" ]]; then
  echo "Neither feature nor canonical canvas exists for ${WORK_ID}" >&2
  exit 1
fi

if [[ -z "${DIRECTION}" ]]; then
  if [[ -f "${feature_canvas}" && -f "${canonical_canvas}" ]]; then
    if cmp -s "${feature_canvas}" "${canonical_canvas}"; then
      echo "Canvases are in sync: ${WORK_ID}"
      exit 0
    fi
    echo "Drift detected between feature and canonical canvases for ${WORK_ID}" >&2
    echo "Use --from-canvas or --from-feature to reconcile." >&2
    exit 2
  fi
  echo "One canvas missing; use --from-canvas or --from-feature to create the missing copy." >&2
  exit 2
fi

src=""
dest=""
case "${DIRECTION}" in
  from-canvas)
    src="${canonical_canvas}"
    dest="${feature_canvas}"
    ;;
  from-feature)
    src="${feature_canvas}"
    dest="${canonical_canvas}"
    ;;
esac

if [[ ! -f "${src}" ]]; then
  echo "Source canvas not found: ${src}" >&2
  exit 1
fi

if [[ -f "${dest}" && "${FORCE}" -eq 0 && ! "${DRY_RUN}" -eq 1 ]]; then
  if cmp -s "${src}" "${dest}"; then
    echo "Already in sync: ${dest}"
    exit 0
  fi
  echo "Destination exists and differs. Re-run with --force to overwrite: ${dest}" >&2
  exit 2
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "[dry-run] would copy ${src} -> ${dest}"
else
  mkdir -p "$(dirname "${dest}")"
  cp "${src}" "${dest}"
  echo "Synced ${src} -> ${dest}"
fi
