#!/usr/bin/env bash
# Team-visible Work ID registry — committed coordination layer on top of local .sdlc/ state.
#
# Local pointer (.sdlc/pointer) stays machine-private.
# spdd/memory/registry.jsonl is committed so teammates see claims, phase, and shelf notes.
#
# Usage (via sdlc-workflow.sh / scripts/sdlc.sh):
#   team | list-work | claim WORK-ID | release [--reason TEXT]

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  set -euo pipefail
fi

_TEAM_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_TEAM_SCRIPT_DIR}/sdlc-pointer.sh"
_paths_lib="${SDLC_ROOT}/scripts/lib/paths.sh"
if [[ ! -f "${_paths_lib}" ]]; then
  _paths_lib="${SDLC_ROOT}/sdlc-spdd/scripts/lib/paths.sh"
fi
if [[ ! -f "${_paths_lib}" ]]; then
  _paths_lib="${SDLC_ROOT}/scripts/sdlc-spdd/lib/paths.sh"
fi
if [[ -f "${_paths_lib}" ]]; then
  # shellcheck source=/dev/null
  source "${_paths_lib}"
fi

SDLC_TEAM_REGISTRY_JSONL="$(sdlc_registry "${SDLC_ROOT}" 2>/dev/null || printf '%s/spdd/memory/registry.jsonl' "${SDLC_ROOT}")"
SDLC_TEAM_REGISTRY_LEGACY="${SDLC_ROOT}/agent-context/work-registry.tsv"
SDLC_TEAM_REGISTRY_LOCK="${SDLC_DIR:-${SDLC_ROOT}/.sdlc}/registry.lock"

_team_stale_days() {
  printf '%s' "${SDLC_TEAM_STALE_DAYS:-7}"
}

_team_is_stale_claim() {
  local updated="${1:-}"
  local status="${2:-}"
  [[ "${status}" == "active" ]] || return 1
  [[ -n "${updated}" ]] || return 1
  local now updated_secs age limit
  now="$(date -u +%s)"
  updated_secs="$(date -u -d "${updated}" +%s 2>/dev/null || echo 0)"
  (( updated_secs > 0 )) || return 1
  age=$((now - updated_secs))
  limit=$(( $(_team_stale_days) * 86400 ))
  (( age > limit ))
}

_team_stale_label() {
  local updated="$1"
  local status="$2"
  if _team_is_stale_claim "${updated}" "${status}"; then
    printf ' [STALE>%sd]' "$(_team_stale_days)"
  fi
}

_team_canvas_path() {
  local work_id="$1"
  local root="${SDLC_ROOT}"
  local home canvas
  if declare -F sdlc_home >/dev/null 2>&1; then
    home="$(sdlc_home "${root}")"
  else
    home="${root}"
  fi
  canvas="${home}/spdd/canvas/${work_id}.md"
  [[ -f "${canvas}" ]] && printf '%s' "${canvas}"
}

# Prints Final Status line text (empty when missing).
_team_canvas_final_status_text() {
  local work_id="$1"
  local canvas
  canvas="$(_team_canvas_path "${work_id}")"
  [[ -n "${canvas}" ]] || return 0
  awk '
    /^## Final Status/ { in_final=1; next }
    /^## / { if (in_final) in_final=0 }
    in_final && /^- Status:/ {
      sub(/^- Status:[[:space:]]*/, "")
      print
      exit
    }
  ' "${canvas}"
}

# Prints complete | cancelled | other based on ## Final Status.
_team_canvas_final_kind() {
  local work_id="$1"
  local line
  line="$(_team_canvas_final_status_text "${work_id}")"
  [[ -z "${line}" ]] && { printf '%s' "other"; return 0; }
  line="$(printf '%s' "${line}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${line}" == *cancel* ]]; then
    printf '%s' "cancelled"
    return 0
  fi
  if [[ "${line}" == *complete* ]] && [[ "${line}" != *in\ progress* ]]; then
    printf '%s' "complete"
    return 0
  fi
  printf '%s' "other"
}

_team_canvas_is_complete() {
  local work_id="$1"
  [[ "$(_team_canvas_final_kind "${work_id}")" == "complete" ]]
}

_team_canvas_is_cancelled() {
  local work_id="$1"
  [[ "$(_team_canvas_final_kind "${work_id}")" == "cancelled" ]]
}

_team_canvas_is_archivable() {
  local work_id="$1"
  local kind
  kind="$(_team_canvas_final_kind "${work_id}")"
  [[ "${kind}" == "complete" || "${kind}" == "cancelled" ]]
}

_team_registry_note_for() {
  local work_id="$1"
  _team_registry_lookup_row "${work_id}" | awk -F '\t' '{ print $7; exit }'
}

_team_registry_lookup_row() {
  local work_id="$1"
  _team_registry_rows | awk -F '\t' -v id="${work_id}" '$1 == id { print; exit }'
}

_team_compose_note() {
  local existing="${1:-}"
  local branch="${2:-}"
  local pr="${3:-}"
  local jira="${4:-}"
  local extra="${5:-}"
  local out="" token
  for token in ${existing}; do
    [[ "${token}" == branch:* || "${token}" == pr:* || "${token}" == jira:* ]] && continue
    out+="${token} "
  done
  [[ -n "${branch}" ]] && out+="branch:${branch} "
  [[ -n "${pr}" ]] && out+="pr:${pr} "
  [[ -n "${jira}" ]] && out+="jira:${jira} "
  [[ -n "${extra}" ]] && out+="${extra} "
  printf '%s' "${out%" "}"
}

_team_auto_branch() {
  local branch="${1:-}"
  if [[ -n "${branch}" && "${branch}" != "auto" ]]; then
    printf '%s' "${branch}"
    return 0
  fi
  if [[ -z "${branch}" && "${SDLC_TEAM_AUTO_BRANCH:-1}" != "1" ]]; then
    return 0
  fi
  git -C "${SDLC_ROOT}" branch --show-current 2>/dev/null || true
}

_team_milestone_path() {
  local work_id="$1"
  local root="${SDLC_ROOT}"
  if declare -F sdlc_home >/dev/null 2>&1; then
    root="$(sdlc_home "${SDLC_ROOT}")"
  fi
  local path dir
  # Prefer subdirectory stubs when present.
  shopt -s nullglob
  for dir in "${root}"/requirements/milestones/milestone-*/; do
    path="${dir}${work_id}.md"
    if [[ -f "${path}" ]]; then
      shopt -u nullglob
      printf '%s' "${path}"
      return 0
    fi
  done
  shopt -u nullglob
  path="${root}/requirements/milestones/${work_id}.md"
  [[ -f "${path}" ]] && printf '%s' "${path}"
}

# Reads Jira key from requirement ## Jira section (- Key: ABC-123), or jira_key frontmatter.
_team_jira_from_milestone() {
  local work_id="$1"
  local path
  path="$(_team_milestone_path "${work_id}")"
  [[ -n "${path}" ]] || return 0
  local from_section
  from_section="$(awk '
    /^## Jira/ { in_jira=1; next }
    /^## / { if (in_jira) exit }
    in_jira && /^[[:space:]]*(-[[:space:]]+)?[Kk]ey:[[:space:]]*/ {
      sub(/^[[:space:]]*(-[[:space:]]+)?[Kk]ey:[[:space:]]*/, "")
      gsub(/^[[:space:]]+|[[:space:]]+$/, "")
      if ($0 ~ /^[A-Z][A-Z0-9]+-[0-9]+$/ && $0 !~ /^(TBD|TODO|NONE)$/i) {
        print $0
        exit
      }
    }
  ' "${path}")"
  if [[ -n "${from_section}" ]]; then
    printf '%s' "${from_section}"
    return 0
  fi
  awk '
    NR==1 && /^---[[:space:]]*$/ { in_fm=1; next }
    in_fm && /^---[[:space:]]*$/ { exit }
    in_fm && /^jira_key:[[:space:]]*/ {
      sub(/^jira_key:[[:space:]]*/, "")
      gsub(/^["[:space:]]+|["[:space:]]+$/, "")
      if ($0 ~ /^[A-Z][A-Z0-9]+-[0-9]+$/ && $0 !~ /^(TBD|TODO|NONE)$/i) {
        print $0
        exit
      }
    }
  ' "${path}"
}

_team_milestone_has_jira_draft() {
  local work_id="$1"
  local path
  path="$(_team_milestone_path "${work_id}")"
  [[ -n "${path}" ]] || return 1
  grep -q '^## Jira' "${path}"
}

_team_auto_jira() {
  local jira="${1:-}"
  local work_id="${2:-}"
  if [[ -n "${jira}" ]]; then
    printf '%s' "${jira}"
    return 0
  fi
  if [[ "${SDLC_TEAM_AUTO_JIRA:-1}" != "1" ]]; then
    return 0
  fi
  _team_jira_from_milestone "${work_id}"
}

_team_jira_from_note() {
  local note="${1:-}"
  local token
  for token in ${note}; do
    if [[ "${token}" == jira:* ]]; then
      printf '%s' "${token#jira:}"
      return 0
    fi
  done
}

# Resolve tracker key for a Work ID.
# Prints: <KEY> | draft | missing
# Prefer claim-note jira:TOKEN, then requirement Key, else draft if ## Jira exists.
sdlc_team_jira_status() {
  local work_id="${1:-}"
  [[ -n "${work_id}" ]] || { printf 'missing'; return 0; }
  local note="" key=""
  if [[ -f "${SDLC_TEAM_REGISTRY_JSONL}" ]] || [[ -f "${SDLC_TEAM_REGISTRY_LEGACY}" ]]; then
    note="$(_team_registry_note_for "${work_id}" || true)"
    key="$(_team_jira_from_note "${note}")"
  fi
  if [[ -n "${key}" ]]; then
    printf '%s' "${key}"
    return 0
  fi
  key="$(_team_jira_from_milestone "${work_id}" || true)"
  if [[ -n "${key}" ]]; then
    printf '%s' "${key}"
    return 0
  fi
  if _team_milestone_has_jira_draft "${work_id}"; then
    printf 'draft'
    return 0
  fi
  printf 'missing'
}

# Agent-facing instruction when Jira is unset. Empty when a key is known or
# SDLC_SESSION_ASK_JIRA=0. Use in Resume Prompt / next / whereami.
sdlc_team_jira_ask_prompt() {
  local work_id="${1:-}"
  [[ -n "${work_id}" ]] || return 0
  [[ "${SDLC_SESSION_ASK_JIRA:-1}" == "1" ]] || return 0
  local status
  status="$(sdlc_team_jira_status "${work_id}")"
  case "${status}" in
    missing)
      printf '%s\n' "Tracker link: Jira key is missing for ${work_id}. Ask the user for the issue key (or confirm none applies) before coding or claiming tracker progress. Then run \`./scripts/sdlc.sh claim ${work_id} --jira KEY\` (or set \`- Key:\` under \`## Jira\` on the requirement and re-claim). Do not invent a key."
      ;;
    draft)
      printf '%s\n' "Tracker link: Jira draft exists for ${work_id} but \`- Key:\` is unset. Ask the user for the issue key (or confirm none applies) before coding or claiming tracker progress. Then run \`./scripts/sdlc.sh claim ${work_id} --jira KEY\` (or set \`- Key:\` under \`## Jira\` and re-claim). Do not invent a key."
      ;;
  esac
}

_team_run_hook() {
  local work_id="$1"
  local status="$2"
  local phase="$3"
  local operation="$4"
  local owner="$5"
  local updated="$6"
  local note="$7"
  local hook="${SDLC_TEAM_REGISTRY_HOOK:-}"
  [[ -n "${hook}" && -x "${hook}" ]] || return 0
  "${hook}" "${work_id}" "${status}" "${phase}" "${operation}" "${owner}" "${updated}" "${note}" || true
}

sdlc_team_refresh_done_status() {
  local work_id kind cur_status cur_phase cur_op cur_note target_status note_token
  _team_registry_init
  while IFS= read -r work_id; do
    [[ -z "${work_id}" ]] && continue
    kind="$(_team_canvas_final_kind "${work_id}")"
    case "${kind}" in
      complete) target_status="done"; note_token="canvas Final Status: Complete" ;;
      cancelled) target_status="cancelled"; note_token="canvas Final Status: Cancelled" ;;
      *) continue ;;
    esac
    cur_status="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $2; exit }' <<< "$(_team_registry_rows)")"
    # Do not reopen archived rows from canvas sync.
    [[ "${cur_status}" == "archived" ]] && continue
    if [[ -z "${cur_status}" ]]; then
      sdlc_team_register "${work_id}" "${target_status}" "sync" "" "${note_token}"
      continue
    fi
    [[ "${cur_status}" == "${target_status}" ]] && continue
    cur_phase="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $3; exit }' <<< "$(_team_registry_rows)")"
    cur_op="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $4; exit }' <<< "$(_team_registry_rows)")"
    cur_note="$(_team_compose_note "$(_team_registry_note_for "${work_id}")" "" "" "" "${note_token}")"
    sdlc_team_register "${work_id}" "${target_status}" "${cur_phase}" "${cur_op}" "${cur_note}"
  done < <(sdlc_team_discover_work_ids)
}

_team_owner() {
  if [[ -n "${SDLC_USER:-}" ]]; then
    printf '%s' "${SDLC_USER}"
    return 0
  fi
  local name
  name="$(git -C "${SDLC_ROOT}" config user.name 2>/dev/null || true)"
  if [[ -n "${name}" ]]; then
    printf '%s' "${name}"
    return 0
  fi
  name="$(git -C "${SDLC_ROOT}" config user.email 2>/dev/null || true)"
  if [[ -n "${name}" ]]; then
    printf '%s' "${name}"
    return 0
  fi
  printf '%s' "$(whoami 2>/dev/null || echo unknown)"
}

_team_registry_init() {
  mkdir -p "$(dirname "${SDLC_TEAM_REGISTRY_JSONL}")" "${SDLC_DIR:-${SDLC_ROOT}/.sdlc}"
  if [[ ! -f "${SDLC_TEAM_REGISTRY_JSONL}" ]]; then
    : > "${SDLC_TEAM_REGISTRY_JSONL}"
  fi
}

_team_registry_read_events() {
  _team_registry_init
  if [[ -f "${SDLC_TEAM_REGISTRY_JSONL}" ]] && [[ -s "${SDLC_TEAM_REGISTRY_JSONL}" ]]; then
    python3 - <<PY
import json
from pathlib import Path
for line in Path(${SDLC_TEAM_REGISTRY_JSONL@Q}).read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        continue
    if ev.get("work_id"):
        print(json.dumps(ev, ensure_ascii=False))
PY
    return 0
  fi
  # Read-only TSV fallback (never written).
  if [[ ! -f "${SDLC_TEAM_REGISTRY_LEGACY}" ]]; then
    return 0
  fi
  python3 - <<PY
import json
from pathlib import Path
tsv = Path(${SDLC_TEAM_REGISTRY_LEGACY@Q})
for line in tsv.read_text(encoding="utf-8").splitlines():
    if not line or line.startswith("#") or line.startswith("work_id"):
        continue
    parts = line.split("\t")
    while len(parts) < 7:
        parts.append("")
    ev = {
        "event": "legacy-tsv",
        "work_id": parts[0],
        "status": parts[1],
        "phase": parts[2],
        "operation": parts[3],
        "owner": parts[4],
        "ts": parts[5],
        "note": parts[6],
    }
    print(json.dumps(ev, ensure_ascii=False))
PY
}

_team_registry_rows() {
  _team_registry_init
  python3 - <<PY
import json
from pathlib import Path

by_id = {}
jsonl = Path(${SDLC_TEAM_REGISTRY_JSONL@Q})
if jsonl.is_file() and jsonl.stat().st_size:
    for line in jsonl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        wid = ev.get("work_id", "")
        if wid:
            by_id[wid] = ev
legacy = Path(${SDLC_TEAM_REGISTRY_LEGACY@Q})
if not by_id and legacy.is_file():
    for line in legacy.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or line.startswith("work_id"):
            continue
        parts = line.split("\t")
        while len(parts) < 7:
            parts.append("")
        wid = parts[0]
        if not wid:
            continue
        by_id[wid] = {
            "work_id": wid,
            "status": parts[1],
            "phase": parts[2],
            "operation": parts[3],
            "owner": parts[4],
            "ts": parts[5],
            "note": parts[6],
        }
for wid in sorted(by_id):
    ev = by_id[wid]
    print("\t".join([
        ev.get("work_id", ""),
        ev.get("status", "available"),
        ev.get("phase", ""),
        ev.get("operation", ""),
        ev.get("owner", ""),
        ev.get("ts", ""),
        ev.get("note", ""),
    ]))
PY
}

_team_with_registry_lock() {
  if command -v flock >/dev/null 2>&1; then
    (
      flock -x 200 || exit 1
      "$@"
    ) 200>"${SDLC_TEAM_REGISTRY_LOCK}"
  else
    "$@"
  fi
}


_team_registry_lookup() {
  local work_id="$1"
  _team_registry_rows | awk -F '\t' -v id="${work_id}" '$1 == id { print; exit }'
}

_team_registry_upsert_impl() {
  local work_id="$1"
  local status="$2"
  local phase="${3:-}"
  local operation="${4:-}"
  local note="${5:-}"
  local event="${6:-update}"
  local owner updated
  owner="$(_team_owner)"
  updated="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  _team_registry_init
  if [[ -z "${note}" ]]; then
    note="$(_team_registry_note_for "${work_id}")"
  fi
  local payload
  payload="$(python3 - <<PY
import json
print(json.dumps({
    "event": ${event@Q},
    "work_id": ${work_id@Q},
    "status": ${status@Q},
    "phase": ${phase@Q},
    "operation": ${operation@Q},
    "owner": ${owner@Q},
    "note": ${note@Q},
    "ts": ${updated@Q},
}, ensure_ascii=False))
PY
)"
  if declare -F sdlc_append_jsonl >/dev/null 2>&1; then
    sdlc_append_jsonl "${SDLC_TEAM_REGISTRY_JSONL}" "${payload}"
  else
    printf '%s\n' "${payload}" >> "${SDLC_TEAM_REGISTRY_JSONL}"
  fi
}

sdlc_team_register() {
  local work_id="$1"
  local status="$2"
  local phase="${3:-}"
  local operation="${4:-}"
  local note="${5:-}"
  local event="${6:-update}"
  if [[ -z "${work_id}" ]]; then
    return 0
  fi
  if [[ "${SDLC_NO_TEAM_REGISTRY:-0}" == "1" ]]; then
    return 0
  fi
  _team_with_registry_lock _team_registry_upsert_impl \
    "${work_id}" "${status}" "${phase}" "${operation}" "${note}" "${event}"
  local hook_owner hook_updated hook_note row
  row="$(_team_registry_lookup_row "${work_id}")"
  hook_owner="$(awk -F '\t' '{ print $5 }' <<< "${row}")"
  hook_updated="$(awk -F '\t' '{ print $6 }' <<< "${row}")"
  hook_note="$(awk -F '\t' '{ print $7 }' <<< "${row}")"
  _team_run_hook "${work_id}" "${status}" "${phase}" "${operation}" \
    "${hook_owner}" "${hook_updated}" "${hook_note}"
}

sdlc_team_check_claim() {
  local work_id="$1"
  local force="${2:-0}"
  local owner status updated me
  _team_registry_init
  owner="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $5; exit }' <<< "$(_team_registry_rows)")"
  status="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $2; exit }' <<< "$(_team_registry_rows)")"
  updated="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $6; exit }' <<< "$(_team_registry_rows)")"
  [[ -n "${owner}" ]] || return 0
  me="$(_team_owner)"
  if [[ "${status}" == "active" && "${owner}" != "${me}" ]]; then
    if _team_is_stale_claim "${updated}" "${status}"; then
      echo "Team registry: ${work_id} is active for ${owner} but stale (>${_team_stale_days}d since ${updated})." >&2
      echo "You may proceed, or use --force to take over explicitly." >&2
      return 0
    fi
    echo "Team registry: ${work_id} is active for ${owner} (updated ${updated})" >&2
    if [[ "${force}" != "1" ]]; then
      echo "Coordinate with your teammate, or re-run with --force to take over." >&2
      return 3
    fi
    echo "Taking over ${work_id} from ${owner} (--force)." >&2
  fi
  return 0
}

sdlc_team_sync_from_workflow() {
  local work_id="$1"
  local status="$2"
  local note="${3:-}"
  local phase="" operation="" file event="update"
  file="${SDLC_DIR:-${SDLC_ROOT}/.sdlc}/workflows/${work_id}.state"
  if [[ -f "${file}" ]]; then
    phase="$(grep -m1 '^phase=' "${file}" 2>/dev/null | cut -d= -f2- || true)"
    operation="$(grep -m1 '^operation=' "${file}" 2>/dev/null | cut -d= -f2- || true)"
  fi
  case "${status}" in
    active) event="claim" ;;
    shelved) event="release" ;;
    archived) event="archive" ;;
    done|cancelled) event="refresh" ;;
  esac
  sdlc_team_register "${work_id}" "${status}" "${phase}" "${operation}" "${note}" "${event}"
}

sdlc_team_discover_work_ids() {
  local root="${SDLC_ROOT}"
  local home
  if declare -F sdlc_home >/dev/null 2>&1; then
    home="$(sdlc_home "${root}")"
  else
    home="${root}"
  fi
  local -A seen=()
  local path base
  shopt -s nullglob
  for path in \
    "${home}"/spdd/canvas/*.md \
    "${home}"/requirements/milestones/*.md \
    "${home}"/requirements/milestones/milestone-*/*.md; do
    base="$(basename "${path}" .md)"
    [[ "${base}" == "README" || "${base}" == "archive" ]] && continue
    [[ "${base}" == MILESTONE-* || "${base}" == milestone-* ]] && continue
    [[ -n "${base}" ]] || continue
    [[ "${path}" == */archive/* || "${path}" == */archive ]] && continue
    seen["${base}"]=1
  done
  shopt -u nullglob
  printf '%s\n' "${!seen[@]}" | sort
}

_team_move_path() {
  local src="$1"
  local dest="$2"
  local dry="${3:-0}"
  [[ -e "${src}" ]] || return 0
  if [[ "${dry}" -eq 1 ]]; then
    echo "[dry-run] would move ${src#${SDLC_ROOT}/} -> ${dest#${SDLC_ROOT}/}"
    return 0
  fi
  mkdir -p "$(dirname "${dest}")"
  if [[ -e "${dest}" ]]; then
    echo "archive: destination already exists, skipping ${dest#${SDLC_ROOT}/}" >&2
    return 1
  fi
  mv "${src}" "${dest}"
  echo "Moved ${src#${SDLC_ROOT}/} -> ${dest#${SDLC_ROOT}/}"
}

# Move completed/cancelled Work ID artifacts into archive/ folders.
# Keeps requirements/milestones/<WORK-ID>.md in place as historical requirement source.
sdlc_team_archive_work() {
  local work_id="${1:-}"
  local dry="${2:-0}"
  local force="${3:-0}"
  local root="${SDLC_ROOT}"
  local kind pointer moved=0

  if [[ -z "${work_id}" ]]; then
    echo "archive: Work ID required" >&2
    return 2
  fi

  kind="$(_team_canvas_final_kind "${work_id}")"
  if [[ "${force}" -ne 1 && "${kind}" != "complete" && "${kind}" != "cancelled" ]]; then
    echo "archive: ${work_id} is not Complete or Cancelled (Final Status kind=${kind}). Use --force to archive anyway." >&2
    return 1
  fi

  pointer="$(sdlc_get_pointer)"
  if [[ "${pointer}" == "${work_id}" ]]; then
    if [[ "${dry}" -eq 1 ]]; then
      echo "[dry-run] would clear pointer for ${work_id}"
    else
      sdlc_reset_pointer >/dev/null
      echo "Cleared local pointer (was ${work_id})"
    fi
  fi

  local feature_src="" feature_dest=""
  # No agent-context/features moves (storage v3).

  local canvas_src review_src analysis_src sync_src home
  if declare -F sdlc_home >/dev/null 2>&1; then
    home="$(sdlc_home "${root}")"
  else
    home="${root}"
  fi
  canvas_src="${home}/spdd/canvas/${work_id}.md"
  analysis_src="${home}/spdd/analysis/${work_id}-analysis.md"
  review_src="${home}/spdd/reviews/${work_id}-review.md"
  sync_src="${home}/spdd/sync/${work_id}-sync.md"
  [[ -f "${canvas_src}" ]] && _team_move_path "${canvas_src}" "${home}/spdd/canvas/archive/${work_id}.md" "${dry}" && moved=1
  [[ -f "${analysis_src}" ]] && _team_move_path "${analysis_src}" "${home}/spdd/analysis/archive/${work_id}-analysis.md" "${dry}" && moved=1
  [[ -f "${review_src}" ]] && _team_move_path "${review_src}" "${home}/spdd/reviews/archive/${work_id}-review.md" "${dry}" && moved=1
  [[ -f "${sync_src}" ]] && _team_move_path "${sync_src}" "${home}/spdd/sync/archive/${work_id}-sync.md" "${dry}" && moved=1

  local session_dir
  if declare -F sdlc_sessions_dir >/dev/null 2>&1; then
    session_dir="$(sdlc_sessions_dir "${root}")"
  else
    session_dir="${home}/.sdlc/sessions"
  fi
  if [[ -d "${session_dir}" ]]; then
    local sess
    shopt -s nullglob
    for sess in "${session_dir}"/*"${work_id}"*; do
      [[ -f "${sess}" ]] || continue
      [[ "$(basename "${sess}")" == "current-session.md" ]] && continue
      _team_move_path "${sess}" "${session_dir}/archive/$(basename "${sess}")" "${dry}" && moved=1
    done
    shopt -u nullglob
  fi

  local state_src="${root}/.sdlc/workflows/${work_id}.state"
  if [[ -f "${state_src}" ]]; then
    _team_move_path "${state_src}" "${root}/.sdlc/workflows/archive/${work_id}.state" "${dry}" && moved=1
  fi

  if [[ "${dry}" -eq 1 ]]; then
    echo "[dry-run] would mark ${work_id} archived in registry.jsonl"
    return 0
  fi

  local note_token="archived:${kind}"
  [[ "${force}" -eq 1 && "${kind}" == "other" ]] && note_token="archived:forced"
  sdlc_team_register "${work_id}" "archived" "archive" "" "${note_token}" "archive"
  if [[ "${moved}" -eq 0 ]]; then
    echo "archive: ${work_id} marked archived (no movable artifacts found; milestone left in place)"
  else
    echo "Archived ${work_id} (${kind}). Commit moved paths + spdd/memory/registry.jsonl."
  fi
  echo "Left in place: requirements/milestones/${work_id}.md (if present)."
}

# Archive every Work ID whose canvas Final Status is Complete or Cancelled.
sdlc_team_archive_eligible() {
  local dry="${1:-0}"
  local work_id count=0 cur
  _team_registry_init
  while IFS= read -r work_id; do
    [[ -z "${work_id}" ]] && continue
    _team_canvas_is_archivable "${work_id}" || continue
    cur="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $2; exit }' <<< "$(_team_registry_rows)" 2>/dev/null || true)"
    [[ "${cur}" == "archived" ]] && continue
    if sdlc_team_archive_work "${work_id}" "${dry}" 0; then
      count=$((count + 1))
    fi
  done < <(sdlc_team_discover_work_ids)
  echo "archive: processed ${count} eligible Work ID(s)"
}

sdlc_team_infer_work_summary() {
  local work_id="$1"
  local root="${SDLC_ROOT}"
  local home parts=()
  if declare -F sdlc_home >/dev/null 2>&1; then
    home="$(sdlc_home "${root}")"
  else
    home="${root}"
  fi
  [[ -f "${home}/spdd/canvas/${work_id}.md" ]] && parts+=("canvas")
  if [[ -n "$(_team_milestone_path "${work_id}" || true)" ]]; then
    parts+=("milestone")
  fi
  local jira_key
  jira_key="$(_team_jira_from_milestone "${work_id}")"
  if [[ -n "${jira_key}" ]]; then
    parts+=("jira:${jira_key}")
  elif _team_milestone_has_jira_draft "${work_id}"; then
    parts+=("jira draft")
  fi
  if ((${#parts[@]} == 0)); then
    printf 'artifacts unknown'
  else
    local IFS=', '
    printf '%s' "${parts[*]}"
  fi
}

sdlc_team_list_work() {
  local work_id
  sdlc_team_refresh_done_status
  echo "Work IDs in this repository:"
  echo
  printf '  %-40s %-12s %-8s %-10s %s\n' "WORK-ID" "REGISTRY" "PHASE" "OWNER" "ARTIFACTS"
  while IFS= read -r work_id; do
    [[ -z "${work_id}" ]] && continue
    local reg_status phase owner summary updated stale done_hint
    reg_status="available"
    phase="-"
    owner="-"
    updated=""
    reg_status="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $2; exit }' <<< "$(_team_registry_rows)")"
    if [[ -n "${reg_status}" ]]; then
      phase="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $3; exit }' <<< "$(_team_registry_rows)")"
      owner="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $5; exit }' <<< "$(_team_registry_rows)")"
      updated="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $6; exit }' <<< "$(_team_registry_rows)")"
      phase="${phase:--}"
      owner="${owner:--}"
      stale="$(_team_stale_label "${updated}" "${reg_status}")"
      reg_status="${reg_status}${stale}"
    else
      reg_status="available"
    fi
    if _team_canvas_is_complete "${work_id}" && [[ "${reg_status}" != done* ]]; then
      done_hint=" (canvas complete)"
    else
      done_hint=""
    fi
    summary="$(sdlc_team_infer_work_summary "${work_id}")${done_hint}"
    printf '  %-40s %-12s %-8s %-10s %s\n' "${work_id}" "${reg_status}" "${phase}" "${owner}" "${summary}"
  done < <(sdlc_team_discover_work_ids)
  echo
  echo "Claim: ./scripts/sdlc.sh claim <WORK-ID> [--branch NAME] [--pr #N] [--jira KEY]"
  echo "Team:  ./scripts/sdlc.sh team"
}

sdlc_team_status() {
  local pointer me
  sdlc_team_refresh_done_status
  pointer="$(sdlc_get_pointer)"
  me="$(_team_owner)"
  echo "SDLC Team View"
  echo "=============="
  echo "You: ${me}"
  echo "Stale claim TTL: $(_team_stale_days) days (override: SDLC_TEAM_STALE_DAYS)"
  if [[ -n "${pointer}" ]]; then
    echo "Your local pointer: ${pointer}"
  else
    echo "Your local pointer: (none)"
  fi
  echo
  echo "Team registry (commit spdd/memory/registry.jsonl to share):"
  if _team_registry_rows | grep -q .; then
    printf '  %-36s %-14s %-10s %-6s %-16s %s\n' "WORK-ID" "STATUS" "PHASE" "OP" "OWNER" "NOTE"
    local wid status phase op owner updated note status_disp
    while IFS= read -r row; do
      wid="$(awk -F '\t' '{ print $1 }' <<< "${row}")"
      status="$(awk -F '\t' '{ print $2 }' <<< "${row}")"
      phase="$(awk -F '\t' '{ print $3 }' <<< "${row}")"
      op="$(awk -F '\t' '{ print $4 }' <<< "${row}")"
      owner="$(awk -F '\t' '{ print $5 }' <<< "${row}")"
      updated="$(awk -F '\t' '{ print $6 }' <<< "${row}")"
      note="$(awk -F '\t' '{ print $7 }' <<< "${row}")"
      status_disp="${status}$(_team_stale_label "${updated}" "${status}")"
      local mark=""
      [[ "${owner}" == "${me}" && "${wid}" == "${pointer}" ]] && mark=" (you)"
      [[ "${owner}" == "${me}" && "${wid}" != "${pointer}" ]] && mark=" (you, pointer elsewhere)"
      printf '  %-36s %-14s %-10s %-6s %-16s %s%s\n' \
        "${wid}" "${status_disp}" "${phase:--}" "${op:--}" "${owner}" "${note:-${updated}}" "${mark}"
    done < <(_team_registry_rows)
  else
    echo "  (empty — claim work with ./scripts/sdlc.sh claim <WORK-ID>)"
  fi
  echo
  echo "Hooks: set SDLC_TEAM_REGISTRY_HOOK to agent-context/hooks/notify-team-registry.sh"
  echo "Discover all Work IDs: ./scripts/sdlc.sh list-work"
}

# Locate the workflow manager: same dir as this script (v3 installs place both
# under <home>/scripts/), then <home>/scripts/, then legacy agent-context/.
_team_workflow_script() {
  local self_dir
  self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local candidate
  for candidate in \
    "${self_dir}/sdlc-workflow.sh" \
    "${SDLC_ROOT}/sdlc-spdd/scripts/sdlc-workflow.sh" \
    "${SDLC_ROOT}/agent-context/sdlc-workflow.sh"; do
    if [[ -f "${candidate}" ]]; then
      printf '%s' "${candidate}"
      return 0
    fi
  done
  return 1
}

sdlc_team_claim() {
  local work_id="$1"
  local force="${2:-0}"
  local phase="${3:-}"
  local branch="${4:-}"
  local pr="${5:-}"
  local jira="${6:-}"
  local note_extra="${7:-}"
  if [[ -z "${work_id}" ]]; then
    echo "sdlc_team_claim: work id required" >&2
    return 2
  fi
  sdlc_team_check_claim "${work_id}" "${force}" || return $?
  local _workflow_script
  if ! _workflow_script="$(_team_workflow_script)"; then
    echo "sdlc_team_claim: sdlc-workflow.sh not installed" >&2
    return 1
  fi
  branch="$(_team_auto_branch "${branch}")"
  jira="$(_team_auto_jira "${jira}" "${work_id}")"
  local existing_note note
  existing_note="$(_team_registry_note_for "${work_id}")"
  note="$(_team_compose_note "${existing_note}" "${branch}" "${pr}" "${jira}" "${note_extra}")"
  # shellcheck source=/dev/null
  source "${_workflow_script}"
  # Pass force through so `sdlc.sh claim <ID> --force` can take over a foreign claim.
  # Mark already-checked so resume does not print "Taking over…" a second time.
  _SDLC_TEAM_CLAIM_CHECKED=1
  sdlc_workflow_resume "${work_id}" "${phase}" 1 "${force}" "${note}"
  local resume_rc=$?
  unset _SDLC_TEAM_CLAIM_CHECKED
  (( resume_rc == 0 )) || return "${resume_rc}"
  echo "Team registry updated — commit spdd/memory/registry.jsonl to share with teammates."
}

sdlc_team_release() {
  local reason="${1:-released}"
  local work_id
  work_id="$(sdlc_get_pointer)"
  if [[ -z "${work_id}" ]]; then
    echo "sdlc_team_release: no active pointer" >&2
    return 2
  fi
  local _workflow_script
  if ! _workflow_script="$(_team_workflow_script)"; then
    echo "sdlc_team_release: sdlc-workflow.sh not installed" >&2
    return 1
  fi
  # shellcheck source=/dev/null
  source "${_workflow_script}"
  sdlc_workflow_shelf "${reason}"
  echo "Team registry updated — commit spdd/memory/registry.jsonl to share with teammates."
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  cmd="${1:-team}"
  shift || true
  case "${cmd}" in
    team) sdlc_team_status ;;
    list-work) sdlc_team_list_work ;;
    claim)
      work_id="${1:-}"; shift || true
      force=0
      phase=""
      branch=""
      pr=""
      jira=""
      note_extra=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --force) force=1; shift ;;
          --phase) phase="${2:-}"; shift 2 ;;
          --branch) branch="${2:-}"; shift 2 ;;
          --pr) pr="${2:-}"; shift 2 ;;
          --jira) jira="${2:-}"; shift 2 ;;
          --note) note_extra="${2:-}"; shift 2 ;;
          *) shift ;;
        esac
      done
      sdlc_team_claim "${work_id}" "${force}" "${phase}" "${branch}" "${pr}" "${jira}" "${note_extra}"
      ;;
    sync-team|/sdlc-team-sync)
      sdlc_team_refresh_done_status
      echo "Team registry refreshed from canvas Final Status."
      ;;
    release)
      reason="released"
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --reason) reason="${2:-}"; shift 2 ;;
          *) shift ;;
        esac
      done
      sdlc_team_release "${reason}"
      ;;
    archive)
      dry=0
      force=0
      all=0
      work_id=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --dry-run) dry=1; shift ;;
          --force) force=1; shift ;;
          --all|--all-eligible) all=1; shift ;;
          *)
            if [[ -z "${work_id}" && "$1" != -* ]]; then
              work_id="$1"
            fi
            shift
            ;;
        esac
      done
      if [[ "${all}" -eq 1 ]]; then
        sdlc_team_archive_eligible "${dry}"
      else
        sdlc_team_archive_work "${work_id}" "${dry}" "${force}"
      fi
      ;;
    *)
      echo "Usage: $0 {team|list-work|claim|release|archive} ..." >&2
      exit 2
      ;;
  esac
fi
