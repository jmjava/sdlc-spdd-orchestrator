#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"

usage() {
  cat <<'EOF'
Usage: summarize-session-notes.sh [--target <path>] [--work-id <WORK-ID>] [--limit <n>]

Summarize past session activity (storage v3). Session records live in the
committed lessons ledger (spdd/memory/lessons.jsonl, kind=session) plus any
staged captures (.sdlc/staged/lessons.jsonl). Human-authored notes under the
optional session-notes/ directory are listed as well.

This command is read-only: it never writes memory files.

Options:
  --target <path>    Target project path (default: .)
  --work-id <ID>     Only show session records for this Work ID
  --limit <n>        Max session records to show (default: 20)
  --help             Print this help message
EOF
}

TARGET="."
WORK_ID=""
LIMIT=20

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
    --limit)
      LIMIT="${2:-}"
      shift 2
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

if ! [[ "${LIMIT}" =~ ^[0-9]+$ ]]; then
  echo "Error: --limit must be a non-negative integer" >&2
  exit 1
fi

TARGET="$(sdlc_resolve_target "${TARGET}")"
export SDLC_ROOT="${TARGET}"
HOME_DIR="$(sdlc_home "${TARGET}")"
LEDGER="$(sdlc_ledger "${TARGET}")"
STAGE="$(sdlc_stage "${TARGET}")"
NOTES_DIR="${HOME_DIR}/session-notes"

echo "Session summary for: ${TARGET}"
echo "  ledger: ${LEDGER#${TARGET}/}"
echo

summarize_jsonl() {
  local file="$1"
  local label="$2"
  if [[ ! -s "${file}" ]]; then
    echo "${label}: no session records."
    return 0
  fi
  FILE="${file}" LABEL="${label}" WORK_ID_FILTER="${WORK_ID}" LIMIT="${LIMIT}" python3 - <<'PY'
import json, os

path = os.environ["FILE"]
label = os.environ["LABEL"]
work_id_filter = os.environ.get("WORK_ID_FILTER", "")
limit = int(os.environ.get("LIMIT", "20"))

records = []
with open(path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("kind") != "session":
            continue
        if work_id_filter and rec.get("work_id") != work_id_filter:
            continue
        records.append(rec)

records.sort(key=lambda r: r.get("ts", ""), reverse=True)
shown = records[:limit] if limit else records

print(f"{label}: {len(records)} session record(s)" + (f", showing {len(shown)}" if len(shown) < len(records) else ""))
for rec in shown:
    ts = rec.get("ts", "?")
    wid = rec.get("work_id", "?")
    phase = rec.get("phase", "?")
    title = (rec.get("title") or "").strip().splitlines()[0] if rec.get("title") else ""
    area = rec.get("area") or ""
    line = f"  {ts}  {wid}  [{phase}]"
    if area:
        line += f"  area={area}"
    if title:
        line += f"  {title[:100]}"
    print(line)
PY
}

summarize_jsonl "${LEDGER}" "Committed ledger"
echo
summarize_jsonl "${STAGE}" "Staged captures (not yet accepted)"
echo

shopt -s nullglob
notes=("${NOTES_DIR}"/*.md)
shopt -u nullglob
if ((${#notes[@]} > 0)); then
  echo "Human session notes (${#notes[@]} file(s) under ${NOTES_DIR#${TARGET}/}/):"
  for note in "${notes[@]}"; do
    echo "  ${note#${TARGET}/}"
  done
else
  echo "No session-notes/ files found (optional)."
fi

echo
echo "Planning review prompt:"
echo "  Read the session records above (full bodies via 'sdlc-engine context show <record-id>')."
echo "  Summarize recurring themes, open risks, and Work IDs mentioned."
