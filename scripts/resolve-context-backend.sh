#!/usr/bin/env bash
# Runtime resolution of SPDD context backends (#79/#90).
#
# Emits CONTEXT_BACKENDS as a comma-separated *set* (not a single enum):
#   git-pointers  — lean stay-set + pointers (always on)
#   sqlite        — local .sdlc/index.sqlite when present / engine available
#   guide-dice    — Guide SPDD projection when opted-in and reachable
#
# Legacy CONTEXT_BACKEND=files|guide-dice is still emitted for older parsers.
#
# Usage:
#   resolve-context-backend.sh [--target <path>]
#   resolve-context-backend.sh --project [--target <path>] [--work-id <id>]
set -euo pipefail

TARGET="."
MODE="probe"
WORK_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --project)
      MODE="project"
      shift
      ;;
    --work-id)
      WORK_ID="${2:-}"
      shift 2
      ;;
    --help|-h)
      sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

TARGET="$(cd "${TARGET}" && pwd)"
MARKER="${TARGET}/agent-context/harness/guide-dice.md"
SQLITE="${TARGET}/.sdlc/index.sqlite"
PERSIST_CFG="${TARGET}/.sdlc/persistence-config.json"

backends=("git-pointers")

# Prefer explicit persistence-config / CONTEXT_BACKENDS when present.
if [[ -n "${CONTEXT_BACKENDS:-}" ]]; then
  IFS=',' read -r -a _env_backends <<< "${CONTEXT_BACKENDS}"
  backends=()
  for b in "${_env_backends[@]}"; do
    b="$(echo "${b}" | tr '[:upper:]' '[:lower:]' | xargs)"
    [[ -n "${b}" ]] || continue
    backends+=("${b}")
  done
  # Ensure git baseline
  has_git=0
  for b in "${backends[@]}"; do
    [[ "${b}" == "git-pointers" || "${b}" == "git" || "${b}" == "files" ]] && has_git=1
  done
  if [[ "${has_git}" -eq 0 ]]; then
    backends=("git-pointers" "${backends[@]}")
  fi
elif [[ -f "${PERSIST_CFG}" ]] && command -v python3 >/dev/null 2>&1; then
  mapfile -t backends < <(
    python3 - <<PY
import json
from pathlib import Path
p = Path(${PERSIST_CFG@Q})
try:
    data = json.loads(p.read_text(encoding="utf-8"))
    backends = data.get("backends") or ["git-pointers", "sqlite", "guide-dice"]
except Exception:
    backends = ["git-pointers", "sqlite", "guide-dice"]
if "git-pointers" not in backends and "git" not in backends:
    backends = ["git-pointers", *backends]
print("\n".join(str(b) for b in backends))
PY
  )
else
  # Default probe: git always; sqlite when index exists; guide when marker+live
  if [[ -f "${SQLITE}" ]]; then
    backends+=("sqlite")
  elif [[ -d "${TARGET}/.sdlc" ]]; then
    backends+=("sqlite")
  fi
fi

guide_live=0
GUIDE_PORT="${GUIDE_PORT:-21337}"
marker_endpoint="$(grep -E '^endpoint:' "${MARKER}" 2>/dev/null | head -1 | sed 's/^endpoint:[[:space:]]*//' || true)"
GUIDE_BASE_URL="${GUIDE_BASE_URL:-${marker_endpoint:-http://localhost:${GUIDE_PORT}}}"
stats_url="${GUIDE_BASE_URL}/api/v1/data/spdd-projection/stats"

want_guide=0
for b in "${backends[@]}"; do
  case "${b}" in
    guide-dice|guide|dice) want_guide=1 ;;
  esac
done

if [[ "${want_guide}" -eq 1 || -f "${MARKER}" ]]; then
  if [[ -f "${MARKER}" || "${want_guide}" -eq 1 ]]; then
    if curl -sf --max-time 2 "${stats_url}" >/dev/null 2>&1; then
      guide_live=1
      has_guide=0
      for b in "${backends[@]}"; do
        [[ "${b}" == "guide-dice" || "${b}" == "guide" ]] && has_guide=1
      done
      if [[ "${has_guide}" -eq 0 ]]; then
        backends+=("guide-dice")
      fi
    fi
  fi
fi

# Normalize names for output
normalized=()
for b in "${backends[@]}"; do
  case "${b}" in
    git|files|pointers|git-pointer) normalized+=("git-pointers") ;;
    db|local-sqlite) normalized+=("sqlite") ;;
    guide|dice) normalized+=("guide-dice") ;;
    *) normalized+=("${b}") ;;
  esac
done
# uniq preserve order
backends=()
seen=""
for b in "${normalized[@]}"; do
  case " ${seen} " in
    *" ${b} "*) ;;
    *) backends+=("${b}"); seen="${seen} ${b}" ;;
  esac
done

IFS=','; echo "CONTEXT_BACKENDS=${backends[*]}"
unset IFS

if [[ "${guide_live}" -eq 1 ]]; then
  echo "CONTEXT_BACKEND=guide-dice"
  echo "GUIDE_BASE_URL=${GUIDE_BASE_URL}"
  echo "MCP_TOOLS=spdd_workSubgraph spdd_areaLessons spdd_findByLabel spdd_projectionStats"
else
  echo "CONTEXT_BACKEND=files"
  if [[ ! -f "${MARKER}" && "${want_guide}" -eq 0 ]]; then
    echo "REASON=guide-dice not enabled (no harness marker / not in CONTEXT_BACKENDS)"
  else
    echo "REASON=guide-dice configured but Guide is not reachable at ${stats_url}"
  fi
fi

if [[ "${MODE}" == "project" && "${guide_live}" -eq 1 ]]; then
  echo ""
  echo "Projecting SPDD entities from: ${TARGET}"
  curl -sf --max-time 30 -X POST "${GUIDE_BASE_URL}/api/v1/data/spdd-projection/load" \
    -H 'Content-Type: application/json' \
    -d "{\"rootPath\":\"${TARGET}\"}" >/dev/null
  echo "PROJECTED=1"
  if [[ -n "${WORK_ID}" ]]; then
    echo "WORK_ID=${WORK_ID}"
  fi
fi
