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
  echo "Work IDs in this repository:"
  echo
  printf '  %-40s %-10s %-8s %-10s %s\n' "WORK-ID" "REGISTRY" "PHASE" "OWNER" "ARTIFACTS"
  while IFS= read -r work_id; do
    [[ -z "${work_id}" ]] && continue
    local reg_status phase owner summary
    reg_status="available"
    phase="-"
    owner="-"
    reg_status="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $2; exit }' "${SDLC_TEAM_REGISTRY}")"
    if [[ -n "${reg_status}" ]]; then
      phase="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $3; exit }' "${SDLC_TEAM_REGISTRY}")"
      owner="$(awk -F '\t' -v id="${work_id}" '$1 == id { print $5; exit }' "${SDLC_TEAM_REGISTRY}")"
      phase="${phase:--}"
      owner="${owner:--}"
    else
      reg_status="available"
    fi
    summary="$(sdlc_team_infer_work_summary "${work_id}")"
    printf '  %-40s %-10s %-8s %-10s %s\n' "${work_id}" "${reg_status}" "${phase}" "${owner}" "${summary}"
  done < <(sdlc_team_discover_work_ids)
  echo
  echo "Claim work: ./scripts/sdlc.sh claim <WORK-ID>"
  echo "Team view:  ./scripts/sdlc.sh team"
}

sdlc_team_status() {
  local pointer me
  pointer="$(sdlc_get_pointer)"
  me="$(_team_owner)"
  echo "SDLC Team View"
  echo "=============="
  echo "You: ${me}"
  if [[ -n "${pointer}" ]]; then
    echo "Your local pointer: ${pointer}"
  else
    echo "Your local pointer: (none)"
  fi
  echo
  echo "Team registry (commit agent-context/work-registry.tsv to share):"
  if _team_registry_rows | grep -q .; then
    printf '  %-36s %-8s %-10s %-6s %-16s %s\n' "WORK-ID" "STATUS" "PHASE" "OP" "OWNER" "UPDATED"
    local wid status phase op owner updated note
    while IFS= read -r row; do
      wid="$(awk -F '\t' '{ print $1 }' <<< "${row}")"
      status="$(awk -F '\t' '{ print $2 }' <<< "${row}")"
      phase="$(awk -F '\t' '{ print $3 }' <<< "${row}")"
      op="$(awk -F '\t' '{ print $4 }' <<< "${row}")"
      owner="$(awk -F '\t' '{ print $5 }' <<< "${row}")"
      updated="$(awk -F '\t' '{ print $6 }' <<< "${row}")"
      note="$(awk -F '\t' '{ print $7 }' <<< "${row}")"
      local mark=""
      [[ "${owner}" == "${me}" && "${wid}" == "${pointer}" ]] && mark=" (you)"
      [[ "${owner}" == "${me}" && "${wid}" != "${pointer}" ]] && mark=" (you, pointer elsewhere)"
      printf '  %-36s %-8s %-10s %-6s %-16s %s%s\n' \
        "${wid}" "${status}" "${phase:--}" "${op:--}" "${owner}" "${updated}" "${note}" "${mark}"
    done < <(_team_registry_rows)
  else
    echo "  (empty — claim work with ./scripts/sdlc.sh claim <WORK-ID>)"
  fi
  echo
  echo "Discover all Work IDs: ./scripts/sdlc.sh list-work"
}

sdlc_team_claim() {
  local work_id="$1"
  local force="${2:-0}"
  local phase="${3:-}"
  if [[ -z "${work_id}" ]]; then
    echo "sdlc_team_claim: work id required" >&2
    return 2
  fi
  sdlc_team_check_claim "${work_id}" "${force}" || return $?
  if [[ ! -f "${SDLC_ROOT}/agent-context/sdlc-workflow.sh" ]]; then
    echo "sdlc_team_claim: sdlc-workflow.sh not installed" >&2
    return 1
  fi
  # shellcheck source=/dev/null
  source "${SDLC_ROOT}/agent-context/sdlc-workflow.sh"
  sdlc_workflow_resume "${work_id}" "${phase}" 1 0
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
  sdlc_team_register "${work_id}" "shelved" "" "" "${reason}"
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
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --force) force=1; shift ;;
          --phase) phase="${2:-}"; shift 2 ;;
          *) shift ;;
        esac
      done
      sdlc_team_claim "${work_id}" "${force}" "${phase}"
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
