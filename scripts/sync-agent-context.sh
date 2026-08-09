#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"

usage() {
  cat <<'EOF'
Usage: sync-agent-context.sh --work-id <WORK-ID> [--from-home|--from-root] [--dry-run] [--force]

Reconcile duplicate canvas copies after a partial consolidation (storage v3).

The canonical canvas lives under the framework home:
  <target>/sdlc-spdd/spdd/canvas/<WORK-ID>.md

A leftover copy at the legacy root location (<target>/spdd/canvas/<WORK-ID>.md)
indicates an incomplete upgrade. With no direction flag this command reports
drift; pass a direction to reconcile:

  --from-home   Overwrite the root copy from the home canvas
  --from-root   Overwrite the home canvas from the root copy

Options:
  --target <path>  Target project path (default: .)
  --dry-run        Show actions without writing files
  --force          Overwrite an existing, differing destination
  --help           Print this help message
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
    --from-home)
      DIRECTION="from-home"
      shift
      ;;
    --from-root)
      DIRECTION="from-root"
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

TARGET="$(sdlc_resolve_target "${TARGET}")"
export SDLC_ROOT="${TARGET}"
HOME_DIR="$(sdlc_home "${TARGET}")"
home_canvas="${HOME_DIR}/spdd/canvas/${WORK_ID}.md"
root_canvas="${TARGET}/spdd/canvas/${WORK_ID}.md"

if [[ "${HOME_DIR}" == "${TARGET}" ]]; then
  # Legacy sprawled layout: home == root, there is only one location.
  if [[ -f "${home_canvas}" ]]; then
    echo "Single canvas location (no sdlc-spdd/ home yet): ${home_canvas}"
    echo "Run upgrade-project.sh to consolidate into the single-folder layout."
    exit 0
  fi
  echo "No canvas found for ${WORK_ID}: ${home_canvas}" >&2
  exit 1
fi

if [[ ! -f "${home_canvas}" && ! -f "${root_canvas}" ]]; then
  echo "No canvas found for ${WORK_ID} (checked ${home_canvas} and ${root_canvas})" >&2
  exit 1
fi

if [[ -z "${DIRECTION}" ]]; then
  if [[ -f "${home_canvas}" && -f "${root_canvas}" ]]; then
    if cmp -s "${home_canvas}" "${root_canvas}"; then
      echo "Canvases are in sync: ${WORK_ID}"
      echo "The root copy is redundant; remove ${root_canvas} (home copy is canonical)."
      exit 0
    fi
    echo "Drift detected between home and root canvases for ${WORK_ID}" >&2
    echo "Use --from-home or --from-root to reconcile." >&2
    exit 2
  fi
  if [[ -f "${home_canvas}" ]]; then
    echo "Canvas is in the canonical home location: ${home_canvas}"
    exit 0
  fi
  echo "Canvas exists only at the legacy root location: ${root_canvas}" >&2
  echo "Use --from-root to move it into the home, or re-run upgrade-project.sh." >&2
  exit 2
fi

src=""
dest=""
case "${DIRECTION}" in
  from-home)
    src="${home_canvas}"
    dest="${root_canvas}"
    ;;
  from-root)
    src="${root_canvas}"
    dest="${home_canvas}"
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
