#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/python.sh"

usage() {
  cat <<'EOF'
Usage: accept-lessons.sh [options]

Promote staged lesson records into spdd/memory/lessons.jsonl (dedupe by id, last wins).
Non-promoted staged records remain unless --discard-rest.

Options:
  --target <path>     Target project (default: .)
  --work-id <ID>      Promote only records for this Work ID
  --ids <a,b,c>       Promote only these record ids (comma-separated)
  --discard-rest      Drop non-promoted staged records in scope from stage
  --commit            git add ledger + git commit with memory message
  --list              Show staged records (id kind work_id title)
  --help              Print this help

Also available via: ./scripts/sdlc.sh accept [options]

Examples:
  ./scripts/accept-lessons.sh --work-id FEAT-001-order-status-api
  ./scripts/accept-lessons.sh --work-id FEAT-001 --commit
  ./scripts/accept-lessons.sh --list
EOF
}

TARGET="."
WORK_ID=""
IDS=""
DISCARD_REST=0
DO_COMMIT=0
LIST_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --work-id) WORK_ID="${2:-}"; shift 2 ;;
    --ids) IDS="${2:-}"; shift 2 ;;
    --discard-rest) DISCARD_REST=1; shift ;;
    --commit) DO_COMMIT=1; shift ;;
    --list) LIST_ONLY=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

TARGET="$(sdlc_resolve_target "${TARGET}")"
ledger="$(sdlc_ledger "${TARGET}")"
stage="$(sdlc_stage "${TARGET}")"
if [[ "$(basename "$(dirname "${_SCRIPT_DIR}")")" == "sdlc-spdd" ]]; then
  ENGINE_ROOT="$(cd "${_SCRIPT_DIR}/../.." && pwd)"
else
  ENGINE_ROOT="$(cd "${_SCRIPT_DIR}/.." && pwd)"
fi
SDLC_ROOT="${ENGINE_ROOT}" resolve_engine_python || exit 1
export SDLC_ROOT="${TARGET}"

_engine_cli() {
  if [[ -d "${ENGINE_ROOT}/engine/src/sdlc_engine" ]]; then
    PYTHONPATH="${ENGINE_ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
      "${SDLC_PY}" -m sdlc_engine --root "${TARGET}" "$@"
  else
    "${SDLC_PY}" -m sdlc_engine --root "${TARGET}" "$@"
  fi
}

_do_git_commit() {
  local count="${1:-0}"
  local commit_id="${WORK_ID:-all}"
  if [[ ! -f "${ledger}" ]] || [[ "${count}" -eq 0 ]]; then
    echo "Nothing to commit (no records promoted)."
    return 0
  fi
  local rel_ledger
  rel_ledger="${ledger#${TARGET}/}"
  git -C "${TARGET}" add "${rel_ledger}"
  git -C "${TARGET}" commit -m "memory: accept ${count} lessons for ${commit_id}"
  echo "Committed ${rel_ledger}"
}

if [[ "${LIST_ONLY}" -eq 1 ]]; then
  if [[ ! -f "${stage}" ]]; then
    echo "No staged records."
    exit 0
  fi
  "${SDLC_PY}" - <<PY
import json
from pathlib import Path
p = Path(${stage@Q})
for line in p.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    print(f"{r.get('id','')}\t{r.get('kind','')}\t{r.get('work_id','')}\t{r.get('title','')}")
PY
  exit 0
fi

args=(context accept)
[[ -n "${WORK_ID}" ]] && args+=(--work-id "${WORK_ID}")
[[ -n "${IDS}" ]] && args+=(--ids "${IDS}")
[[ "${DISCARD_REST}" -eq 1 ]] && args+=(--discard-rest)
result="$(_engine_cli "${args[@]}" 2>&1)" || { echo "${result}" >&2; exit 1; }
echo "${result}"
accepted_count="$(
  printf '%s' "${result}" |
    "${SDLC_PY}" -c 'import json,sys; print(json.load(sys.stdin).get("accepted_count", 0))'
)"
if [[ "${DO_COMMIT}" -eq 1 ]]; then
  _do_git_commit "${accepted_count}"
fi
