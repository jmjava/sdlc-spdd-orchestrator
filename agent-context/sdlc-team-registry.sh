#!/usr/bin/env bash
# Team-visible Work ID registry — committed coordination layer on top of local .sdlc/ state.
#
# Local pointer (.sdlc/pointer) stays machine-private.
# agent-context/work-registry.tsv is committed so teammates see claims, phase, and shelf notes.
#
# Usage (via sdlc-workflow.sh / scripts/sdlc.sh):
#   team | list-work | claim WORK-ID | release [--reason TEXT]

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  set -euo pipefail
fi

_TEAM_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_TEAM_SCRIPT_DIR}/sdlc-pointer.sh"

SDLC_TEAM_REGISTRY="${SDLC_ROOT}/agent-context/work-registry.tsv"
SDLC_TEAM_REGISTRY_LOCK="${SDLC_ROOT}/agent-context/.work-registry.lock"

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
  local canvas="${root}/spdd/canvas/${work_id}.md"
  if [[ ! -f "${canvas}" ]]; then
    canvas="${root}/agent-context/features/${work_id}/reasons-canvas.md"
  fi
  [[ -f "${canvas}" ]] && printf '%s' "${canvas}"
}

_team_canvas_is_complete() {
  local work_id="$1"
  local canvas line
  canvas="$(_team_canvas_path "${work_id}")"
  [[ -n "${canvas}" ]] || return 1
  line="$(awk '
    /^## Final Status/ { in_final=1; next }
    /^## / { if (in_final) in_final=0 }
    in_final && /^- Status:/ {
      sub(/^- Status:[[:space:]]*/, "")
      print
      exit
    }
  ' "${canvas}")"
  [[ -z "${line}" ]] && return 1
  line="$(printf '%s' "${line}" | tr '[:upper:]' '[:lower:]')"
  [[ "${line}" == *complete* ]] && [[ "${line}" != *in\ progress* ]]
}

_team_registry_note_for() {
  local work_id="$1"
  awk -F '\t' -v id="${work_id}" '$1 == id { print $7; exit }' "${SDLC_TEAM_REGISTRY}"
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
  local work_id
  _team_registry_init
  while IFS= read -r work_id; do
    [[ -z "${work_id}" ]] && continue
    _team_canvas_is_complete "${work_id}" || continue
    local cur_status cur_phase cur_op cur_note
    cur_status="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $2; exit }' "${SDLC_TEAM_REGISTRY}")"
    if [[ -z "${cur_status}" ]]; then
      sdlc_team_register "${work_id}" "done" "sync" "" "canvas complete"
      continue
    fi
    [[ "${cur_status}" == "done" ]] && continue
    cur_phase="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $3; exit }' "${SDLC_TEAM_REGISTRY}")"
    cur_op="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $4; exit }' "${SDLC_TEAM_REGISTRY}")"
    cur_note="$(_team_compose_note "$(_team_registry_note_for "${work_id}")" "" "" "" "canvas Final Status: Complete")"
    sdlc_team_register "${work_id}" "done" "${cur_phase}" "${cur_op}" "${cur_note}"
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
  mkdir -p "${SDLC_ROOT}/agent-context"
  if [[ ! -f "${SDLC_TEAM_REGISTRY}" ]]; then
    cat > "${SDLC_TEAM_REGISTRY}" <<'EOF'
# Team Work Registry — tab-separated. Commit updates so teammates see who is on which Work ID.
# Columns: work_id status phase operation owner updated note
# status: active | shelved | done | available
# note tokens: branch:<name> pr:<url-or-#> jira:<KEY> <free text>
work_id	status	phase	operation	owner	updated	note
EOF
  fi
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

_team_registry_rows() {
  _team_registry_init
  grep -v '^#' "${SDLC_TEAM_REGISTRY}" | grep -v '^work_id' | grep -v '^[[:space:]]*$' || true
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
  local owner updated header tmp
  owner="$(_team_owner)"
  updated="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  _team_registry_init
  header="$(grep -m1 '^work_id' "${SDLC_TEAM_REGISTRY}" || echo 'work_id	status	phase	operation	owner	updated	note')"
  tmp="${SDLC_TEAM_REGISTRY}.tmp.$$"
  {
    grep '^#' "${SDLC_TEAM_REGISTRY}" || true
    printf '%s\n' "${header}"
    local found=0 row wid
    while IFS= read -r row; do
      wid="${row%%$'\t'*}"
      if [[ "${wid}" == "${work_id}" ]]; then
        found=1
        if [[ -z "${note}" ]]; then
          note="$(awk -F '\t' '{ print $7 }' <<< "${row}")"
        fi
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
          "${work_id}" "${status}" "${phase}" "${operation}" "${owner}" "${updated}" "${note}"
      else
        printf '%s\n' "${row}"
      fi
    done < <(_team_registry_rows)
    if [[ "${found}" -eq 0 ]]; then
      printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "${work_id}" "${status}" "${phase}" "${operation}" "${owner}" "${updated}" "${note}"
    fi
  } > "${tmp}"
  mv -f "${tmp}" "${SDLC_TEAM_REGISTRY}"
}

sdlc_team_register() {
  local work_id="$1"
  local status="$2"
  local phase="${3:-}"
  local operation="${4:-}"
  local note="${5:-}"
  if [[ -z "${work_id}" ]]; then
    return 0
  fi
  if [[ "${SDLC_NO_TEAM_REGISTRY:-0}" == "1" ]]; then
    return 0
  fi
  _team_with_registry_lock _team_registry_upsert_impl \
    "${work_id}" "${status}" "${phase}" "${operation}" "${note}"
  local hook_owner hook_updated hook_note
  hook_owner="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $5; exit }' "${SDLC_TEAM_REGISTRY}")"
  hook_updated="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $6; exit }' "${SDLC_TEAM_REGISTRY}")"
  hook_note="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $7; exit }' "${SDLC_TEAM_REGISTRY}")"
  _team_run_hook "${work_id}" "${status}" "${phase}" "${operation}" \
    "${hook_owner}" "${hook_updated}" "${hook_note}"
}

sdlc_team_check_claim() {
  local work_id="$1"
  local force="${2:-0}"
  local owner status updated me
  _team_registry_init
  owner="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $5; exit }' "${SDLC_TEAM_REGISTRY}")"
  status="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $2; exit }' "${SDLC_TEAM_REGISTRY}")"
  updated="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $6; exit }' "${SDLC_TEAM_REGISTRY}")"
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
  local phase="" operation="" file
  file="${SDLC_ROOT}/.sdlc/workflows/${work_id}.state"
  if [[ -f "${file}" ]]; then
    phase="$(grep -m1 '^phase=' "${file}" 2>/dev/null | cut -d= -f2- || true)"
    operation="$(grep -m1 '^operation=' "${file}" 2>/dev/null | cut -d= -f2- || true)"
  fi
  sdlc_team_register "${work_id}" "${status}" "${phase}" "${operation}" "${note}"
}

sdlc_team_discover_work_ids() {
  local root="${SDLC_ROOT}"
  local -A seen=()
  local path base
  shopt -s nullglob
  for path in \
    "${root}"/agent-context/features/*/ \
    "${root}"/spdd/canvas/*.md \
    "${root}"/requirements/milestones/*.md; do
    if [[ -d "${path}" ]]; then
      base="$(basename "${path}")"
    else
      base="$(basename "${path}" .md)"
    fi
    [[ "${base}" == "README" ]] && continue
    [[ -n "${base}" ]] || continue
    seen["${base}"]=1
  done
  shopt -u nullglob
  printf '%s\n' "${!seen[@]}" | sort
}

sdlc_team_infer_work_summary() {
  local work_id="$1"
  local root="${SDLC_ROOT}"
  local parts=()
  [[ -d "${root}/agent-context/features/${work_id}" ]] && parts+=("feature workspace")
  [[ -f "${root}/spdd/canvas/${work_id}.md" ]] && parts+=("canvas")
  [[ -f "${root}/requirements/milestones/${work_id}.md" ]] && parts+=("milestone")
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
    reg_status="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $2; exit }' "${SDLC_TEAM_REGISTRY}")"
    if [[ -n "${reg_status}" ]]; then
      phase="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $3; exit }' "${SDLC_TEAM_REGISTRY}")"
      owner="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $5; exit }' "${SDLC_TEAM_REGISTRY}")"
      updated="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $6; exit }' "${SDLC_TEAM_REGISTRY}")"
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
  echo "Team registry (commit agent-context/work-registry.tsv to share):"
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
  if [[ ! -f "${SDLC_ROOT}/agent-context/sdlc-workflow.sh" ]]; then
    echo "sdlc_team_claim: sdlc-workflow.sh not installed" >&2
    return 1
  fi
  branch="$(_team_auto_branch "${branch}")"
  local existing_note note
  existing_note="$(_team_registry_note_for "${work_id}")"
  note="$(_team_compose_note "${existing_note}" "${branch}" "${pr}" "${jira}" "${note_extra}")"
  # shellcheck source=/dev/null
  source "${SDLC_ROOT}/agent-context/sdlc-workflow.sh"
  sdlc_workflow_resume "${work_id}" "${phase}" 1 0 "${note}"
  echo "Team registry updated — commit agent-context/work-registry.tsv to share with teammates."
}

sdlc_team_release() {
  local reason="${1:-released}"
  local work_id
  work_id="$(sdlc_get_pointer)"
  if [[ -z "${work_id}" ]]; then
    echo "sdlc_team_release: no active pointer" >&2
    return 2
  fi
  if [[ ! -f "${SDLC_ROOT}/agent-context/sdlc-workflow.sh" ]]; then
    echo "sdlc_team_release: sdlc-workflow.sh not installed" >&2
    return 1
  fi
  # shellcheck source=/dev/null
  source "${SDLC_ROOT}/agent-context/sdlc-workflow.sh"
  sdlc_workflow_shelf "${reason}"
  echo "Team registry updated — commit agent-context/work-registry.tsv to share with teammates."
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
    *)
      echo "Usage: $0 {team|list-work|claim|release} ..." >&2
      exit 2
      ;;
  esac
fi
