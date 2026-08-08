#!/usr/bin/env bash
# Runtime resolution of SPDD context backends (#79/#90).
#
# Emits CONTEXT_BACKENDS as a comma-separated *set* (not a single enum):
#   git-pointers  — lean stay-set + pointers (always on)
#   sqlite        — local .sdlc/index.sqlite when present / engine available
#   guide-dice    — Guide SPDD projection when opted-in and reachable
#
# Explicit sources (CONTEXT_BACKENDS env or .sdlc/persistence-config.json) are
# authoritative: a disabled guide-dice is never re-added from the harness marker.
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
      sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
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
explicit_source=0

_normalize_one() {
  case "$1" in
    git|files|pointers|git-pointer) echo "git-pointers" ;;
    db|local-sqlite) echo "sqlite" ;;
    guide|dice) echo "guide-dice" ;;
    *) echo "$1" ;;
  esac
}

_uniq_backends() {
  local -a raw=("$@")
  local -a out=()
  local seen="" b n
  for b in "${raw[@]}"; do
    n="$(_normalize_one "${b}")"
    case " ${seen} " in
      *" ${n} "*) ;;
      *) out+=("${n}"); seen="${seen} ${n}" ;;
    esac
  done
  printf '%s\n' "${out[@]}"
}

# Prefer explicit persistence-config / CONTEXT_BACKENDS when present.
# Match Python parse_backends_env: drop unknown tokens; if every token is
# garbage, treat as unset so defaults/file probe apply.
if [[ -n "${CONTEXT_BACKENDS:-}" ]]; then
  IFS=',' read -r -a _env_backends <<< "${CONTEXT_BACKENDS}"
  backends=()
  _any_known=0
  for b in "${_env_backends[@]}"; do
    b="$(printf '%s' "${b}" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s/_/-/g')"
    [[ -n "${b}" ]] || continue
    n="$(_normalize_one "${b}")"
    case "${n}" in
      git-pointers|sqlite|guide-dice)
        backends+=("${n}")
        _any_known=1
        ;;
    esac
  done
  if [[ "${_any_known}" -eq 1 ]]; then
    explicit_source=1
  else
    backends=("git-pointers")
  fi
fi

if [[ "${explicit_source}" -eq 1 ]]; then
  :
elif [[ -f "${PERSIST_CFG}" ]] && command -v python3 >/dev/null 2>&1; then
  explicit_source=1
  mapfile -t backends < <(
    PERSIST_CFG_PATH="${PERSIST_CFG}" python3 - <<'PY'
import json
import os
from pathlib import Path
p = Path(os.environ["PERSIST_CFG_PATH"])
try:
    data = json.loads(p.read_text(encoding="utf-8"))
    backends = data.get("backends") or ["git-pointers", "sqlite", "guide-dice"]
except Exception:
    backends = ["git-pointers", "sqlite", "guide-dice"]
aliases = {
    "git": "git-pointers",
    "files": "git-pointers",
    "guide": "guide-dice",
    "dice": "guide-dice",
    "db": "sqlite",
}
out = []
for b in backends:
    n = aliases.get(str(b).strip().lower().replace("_", "-"), str(b).strip().lower())
    if n in {"git-pointers", "sqlite", "guide-dice"} and n not in out:
        out.append(n)
if "git-pointers" not in out:
    out = ["git-pointers", *out]
print("\n".join(out))
PY
  )
else
  # Default probe: git always; sqlite when index/.sdlc exists; guide via marker+live
  if [[ -f "${SQLITE}" || -d "${TARGET}/.sdlc" ]]; then
    backends+=("sqlite")
  fi
fi

mapfile -t backends < <(_uniq_backends "${backends[@]}")
has_git=0
for b in "${backends[@]}"; do
  [[ "${b}" == "git-pointers" ]] && has_git=1
done
if [[ "${has_git}" -eq 0 ]]; then
  backends=("git-pointers" "${backends[@]}")
fi

guide_live=0
GUIDE_PORT="${GUIDE_PORT:-21337}"
marker_endpoint="$(grep -E '^endpoint:' "${MARKER}" 2>/dev/null | head -1 | sed 's/^endpoint:[[:space:]]*//' || true)"
GUIDE_BASE_URL="${GUIDE_BASE_URL:-${marker_endpoint:-http://localhost:${GUIDE_PORT}}}"
stats_url="${GUIDE_BASE_URL}/api/v1/data/spdd-projection/stats"

want_guide=0
for b in "${backends[@]}"; do
  [[ "${b}" == "guide-dice" ]] && want_guide=1
done

# Probe Guide only when the active backend set asks for it, or (defaults only)
# when the legacy harness marker opts in.
should_probe=0
if [[ "${want_guide}" -eq 1 ]]; then
  should_probe=1
elif [[ "${explicit_source}" -eq 0 && -f "${MARKER}" ]]; then
  should_probe=1
fi

if [[ "${should_probe}" -eq 1 ]] && curl -sf --max-time 2 "${stats_url}" >/dev/null 2>&1; then
  guide_live=1
  if [[ "${want_guide}" -eq 0 && "${explicit_source}" -eq 0 ]]; then
    backends+=("guide-dice")
    want_guide=1
  fi
fi

mapfile -t backends < <(_uniq_backends "${backends[@]}")

IFS=','; echo "CONTEXT_BACKENDS=${backends[*]}"
unset IFS

if [[ "${guide_live}" -eq 1 && "${want_guide}" -eq 1 ]]; then
  echo "CONTEXT_BACKEND=guide-dice"
  echo "GUIDE_BASE_URL=${GUIDE_BASE_URL}"
  echo "MCP_TOOLS=spdd_workSubgraph spdd_areaLessons spdd_findByLabel spdd_projectionStats"
else
  echo "CONTEXT_BACKEND=files"
  if [[ "${want_guide}" -eq 0 ]]; then
    if [[ "${explicit_source}" -eq 1 ]]; then
      echo "REASON=guide-dice disabled by CONTEXT_BACKENDS / persistence-config"
    else
      echo "REASON=guide-dice not enabled (no harness marker / not in CONTEXT_BACKENDS)"
    fi
  else
    echo "REASON=guide-dice configured but Guide is not reachable at ${stats_url}"
  fi
fi

if [[ "${MODE}" == "project" && "${guide_live}" -eq 1 && "${want_guide}" -eq 1 ]]; then
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
