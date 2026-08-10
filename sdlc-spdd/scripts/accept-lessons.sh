#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"

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
export SDLC_ROOT="${TARGET}"

ledger="$(sdlc_ledger "${TARGET}")"
stage="$(sdlc_stage "${TARGET}")"

_python_engine_available() {
  if [[ -d "${TARGET}/engine/src/sdlc_engine" ]]; then
    PYTHONPATH="${TARGET}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
      python3 -c 'import sdlc_engine' 2>/dev/null
    return $?
  fi
  python3 -c 'import sdlc_engine' 2>/dev/null
}

_run_python_accept() {
  local -a args=(context accept)
  [[ -n "${WORK_ID}" ]] && args+=(--work-id "${WORK_ID}")
  [[ -n "${IDS}" ]] && args+=(--ids "${IDS}")
  [[ "${DISCARD_REST}" -eq 1 ]] && args+=(--discard-rest)
  if [[ -d "${TARGET}/engine/src/sdlc_engine" ]]; then
    PYTHONPATH="${TARGET}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
      python3 -m sdlc_engine --root "${TARGET}" "${args[@]}"
  else
    python3 -m sdlc_engine --root "${TARGET}" "${args[@]}"
  fi
}

if [[ "${LIST_ONLY}" -eq 1 ]]; then
  if [[ ! -f "${stage}" ]]; then
    echo "No staged records."
    exit 0
  fi
  python3 - <<PY
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

engine_mode="${SDLC_ENGINE:-shell}"
if [[ "${engine_mode}" == "python" ]] || { [[ "${engine_mode}" == "auto" ]] && _python_engine_available; }; then
  result="$(_run_python_accept 2>&1)" || { echo "${result}" >&2; exit 1; }
  echo "${result}"
  accepted_count="$(printf '%s' "${result}" | python3 -c 'import json,sys; d=json.load(sys.stdin) if sys.stdin.readable() else {}; print(d.get("accepted_count",0))' 2>/dev/null || echo 0)"
  if [[ "${DO_COMMIT}" -eq 1 ]]; then
    _do_git_commit "${accepted_count}"
  fi
  exit 0
fi

# Pure-shell accept fallback
_accept_shell() {
  python3 - <<PY
import json, os, tempfile
from pathlib import Path

root = Path(${TARGET@Q})
ledger = Path(${ledger@Q})
stage = Path(${stage@Q})
work_id = ${WORK_ID@Q}
ids_csv = ${IDS@Q}
discard_rest = ${DISCARD_REST}

want_ids = set(x.strip() for x in ids_csv.split(",") if x.strip()) if ids_csv else None

def read_jsonl(path):
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out

def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def in_scope(rec):
    if work_id and rec.get("work_id") != work_id:
        return False
    if want_ids is not None and rec.get("id") not in want_ids:
        return False
    return True

staged = read_jsonl(stage)
promote = [r for r in staged if in_scope(r)]
by_id = {}
for rec in promote:
    by_id[rec["id"]] = rec
promote = list(by_id.values())

accepted = {r["id"]: r for r in read_jsonl(ledger)}
for rec in promote:
    accepted[rec["id"]] = rec
if promote:
    write_jsonl(ledger, accepted.values())

if discard_rest:
    remaining = [r for r in staged if work_id and r.get("work_id") != work_id]
else:
    promoted_ids = {r["id"] for r in promote}
    remaining = [r for r in staged if r.get("id") not in promoted_ids]
write_jsonl(stage, remaining)

print(json.dumps({
    "accepted": [r["id"] for r in promote],
    "accepted_count": len(promote),
    "staged_remaining": len(remaining),
    "ledger": str(ledger),
}))
PY
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

result="$(_accept_shell)"
echo "${result}"
accepted_count="$(printf '%s' "${result}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("accepted_count",0))')"
if [[ "${DO_COMMIT}" -eq 1 ]]; then
  _do_git_commit "${accepted_count}"
fi
