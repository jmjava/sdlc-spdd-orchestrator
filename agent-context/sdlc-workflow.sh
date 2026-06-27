#!/usr/bin/env bash
# Workflow state manager for SDLC-SPDD — tracks phase, gates, shelf/resume on top of sdlc-pointer.sh
#
# Usage:
#   source agent-context/sdlc-workflow.sh
#   sdlc_workflow_status
#   sdlc_workflow_resume WORK_ID [--phase PHASE]
#   sdlc_workflow_advance [--to PHASE]
#   sdlc_workflow_skip PHASE [--reason TEXT]
#   sdlc_workflow_shelf [--reason TEXT]
#   sdlc_workflow_sync [--work-id WORK_ID]
#
# State: .sdlc/workflows/<WORK-ID>.state and .sdlc/workflows/<WORK-ID>.history

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  set -euo pipefail
fi

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/sdlc-pointer.sh"

SDLC_WORKFLOW_DIR="${SDLC_DIR}/workflows"
SDLC_WORKFLOW_LOCK="${SDLC_DIR}/workflow.lock"

mkdir -p "${SDLC_WORKFLOW_DIR}"

SDLC_PHASE_ORDER=(init analysis plan architect code api-test review prompt-update retro sync)

SDLC_GATE_NAMES=(
  requirement_documented
  canvas_exists
  architect_review
  operations_task_sized
  code_maps_to_ops
  tests_updated
  review_completed
  safeguards_checked
  retro_completed
  canvas_synced
)

SDLC_GATE_LABELS=(
  "Requirement documented"
  "REASONS Canvas exists"
  "Architect review completed"
  "Operations are task-sized"
  "Code changes map to approved operations"
  "Tests added or updated"
  "Review completed"
  "Safeguards checked"
  "Retro completed"
  "Canvas synced with implementation"
)

_have_flock() {
  command -v flock >/dev/null 2>&1
}

_wf_now() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

_wf_state_file() {
  printf '%s/%s.state' "${SDLC_WORKFLOW_DIR}" "$1"
}

_wf_history_file() {
  printf '%s/%s.history' "${SDLC_WORKFLOW_DIR}" "$1"
}

_wf_valid_phase() {
  local phase="$1"
  local p
  for p in "${SDLC_PHASE_ORDER[@]}"; do
    [[ "${p}" == "${phase}" ]] && return 0
  done
  return 1
}

_wf_phase_index() {
  local phase="$1"
  local i=0
  for p in "${SDLC_PHASE_ORDER[@]}"; do
    if [[ "${p}" == "${phase}" ]]; then
      echo "${i}"
      return 0
    fi
    i=$((i + 1))
  done
  echo "-1"
  return 1
}

_wf_phase_at() {
  local idx="$1"
  if (( idx < 0 || idx >= ${#SDLC_PHASE_ORDER[@]} )); then
    return 1
  fi
  echo "${SDLC_PHASE_ORDER[$idx]}"
}

_wf_next_phase() {
  local phase="$1"
  local idx next
  idx="$(_wf_phase_index "${phase}")"
  next=$((idx + 1))
  _wf_phase_at "${next}" || true
}

_wf_read_state_var() {
  local file="$1"
  local key="$2"
  local default="${3:-}"
  if [[ ! -f "${file}" ]]; then
    printf '%s' "${default}"
    return 0
  fi
  local line
  line="$(grep -m1 "^${key}=" "${file}" 2>/dev/null || true)"
  if [[ -z "${line}" ]]; then
    printf '%s' "${default}"
    return 0
  fi
  printf '%s' "${line#*=}"
}

_wf_write_state_file() {
  local work_id="$1"
  local file
  file="$(_wf_state_file "${work_id}")"
  local tmp="${file}.tmp.$$"
  {
    printf 'work_id=%s\n' "${work_id}"
    printf 'phase=%s\n' "$(_wf_read_state_var "${file}" phase init)"
    printf 'operation=%s\n' "$(_wf_read_state_var "${file}" operation)"
    printf 'active=%s\n' "$(_wf_read_state_var "${file}" active 1)"
    printf 'shelved_at=%s\n' "$(_wf_read_state_var "${file}" shelved_at)"
    printf 'shelved_reason=%s\n' "$(_wf_read_state_var "${file}" shelved_reason)"
    printf 'milestone=%s\n' "$(_wf_read_state_var "${file}" milestone)"
    printf 'last_session_at=%s\n' "$(_wf_read_state_var "${file}" last_session_at)"
    printf 'last_capture_at=%s\n' "$(_wf_read_state_var "${file}" last_capture_at)"
    local gate
    for gate in "${SDLC_GATE_NAMES[@]}"; do
      printf 'gate_%s=%s\n' "${gate}" "$(_wf_read_state_var "${file}" "gate_${gate}" pending)"
    done
    if [[ -f "${file}" ]]; then
      grep '^skip_' "${file}" 2>/dev/null || true
    fi
  } > "${tmp}"
  mv -f "${tmp}" "${file}"
}

_wf_set_state_var() {
  local work_id="$1"
  local key="$2"
  local value="$3"
  local file tmp
  file="$(_wf_state_file "${work_id}")"
  tmp="${file}.tmp.$$"
  if [[ ! -f "${file}" ]]; then
    _wf_write_state_file "${work_id}"
  fi
  if grep -q "^${key}=" "${file}" 2>/dev/null; then
    grep -v "^${key}=" "${file}" > "${tmp}" || true
  else
    cp "${file}" "${tmp}"
  fi
  printf '%s=%s\n' "${key}" "${value}" >> "${tmp}"
  mv -f "${tmp}" "${file}"
}

_wf_with_workflow_lock() {
  if _have_flock; then
    (
      flock -x 200 || exit 1
      "$@"
    ) 200>"${SDLC_WORKFLOW_LOCK}"
  else
    "$@"
  fi
}

_wf_log_history() {
  local work_id="$1"
  local action="$2"
  shift 2
  local hist
  hist="$(_wf_history_file "${work_id}")"
  printf '%s\t%s\t%s\n' "$(_wf_now)" "${action}" "$*" >> "${hist}"
}

_wf_ensure_state() {
  local work_id="$1"
  local file
  file="$(_wf_state_file "${work_id}")"
  if [[ ! -f "${file}" ]]; then
    _wf_write_state_file "${work_id}"
    _wf_set_state_var "${work_id}" phase init
    _wf_log_history "${work_id}" create "work_id=${work_id}"
  fi
}

sdlc_workflow_recommended_command() {
  local phase="${1:-init}"
  local work_id="${2:-}"
  case "${phase}" in
    init) echo "/sdlc-spdd-init" ;;
    analysis) echo "/sdlc-spdd-analysis @requirements/<requirement>.md" ;;
    plan) echo "/sdlc-spdd-plan @spdd/analysis/${work_id:-<WORK-ID>}-analysis.md" ;;
    architect) echo "/sdlc-spdd-architect @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    code) echo "/sdlc-spdd-code @spdd/canvas/${work_id:-<WORK-ID>}.md operation <T##>" ;;
    api-test) echo "/sdlc-spdd-api-test @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    review) echo "/sdlc-spdd-review @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    prompt-update) echo "/sdlc-spdd-prompt-update @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    retro) echo "/sdlc-spdd-retro @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    sync) echo "/sdlc-spdd-sync @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    resume) echo "Read agent-context/sessions/current-session.md, then choose the next phase command." ;;
    *) echo "/sdlc-spdd-init" ;;
  esac
}

_wf_infer_phase_from_artifacts() {
  local work_id="$1"
  local root="${SDLC_ROOT}"
  local inferred="init"
  local req feature_req analysis canvas review retro sync_log progress

  feature_req="${root}/agent-context/features/${work_id}/requirement.md"
  req="${root}/requirements/milestones/${work_id}.md"
  analysis="${root}/spdd/analysis/${work_id}-analysis.md"
  canvas="${root}/spdd/canvas/${work_id}.md"
  review="${root}/spdd/reviews/${work_id}-review.md"
  retro="${root}/agent-context/features/${work_id}/retro.md"
  sync_log="${root}/spdd/sync/${work_id}-sync.md"
  progress="${root}/agent-context/features/${work_id}/progress-log.md"

  if [[ -f "${req}" || -f "${feature_req}" ]]; then
    inferred="analysis"
  fi
  if [[ -f "${analysis}" ]]; then
    inferred="plan"
  fi
  if [[ -f "${canvas}" ]]; then
    inferred="architect"
    if grep -Eqi 'ready[[:space:]]+for[[:space:]]+coding' "${canvas}" 2>/dev/null; then
      inferred="code"
    fi
  fi
  if [[ -f "${progress}" ]] && grep -Eqi '(T[0-9]{2}.*complete|implemented|merged)' "${progress}" 2>/dev/null; then
    inferred="code"
  fi
  if [[ -f "${review}" ]]; then
    inferred="review"
  fi
  if [[ -f "${retro}" ]]; then
    inferred="retro"
  fi
  if [[ -f "${sync_log}" ]]; then
    inferred="sync"
  fi

  local session_file="${root}/agent-context/sessions/current-session.md"
  if [[ -f "${session_file}" ]] && grep -Fq "${work_id}" "${session_file}"; then
    local session_phase
    session_phase="$(grep -m1 '^- Phase:' "${session_file}" 2>/dev/null | sed 's/^- Phase:[[:space:]]*//' || true)"
    if [[ -n "${session_phase}" ]] && _wf_valid_phase "${session_phase}"; then
      local stored_idx inferred_idx session_idx
      stored_idx="$(_wf_phase_index "${inferred}")"
      session_idx="$(_wf_phase_index "${session_phase}")"
      inferred_idx="${stored_idx}"
      if (( session_idx > inferred_idx )); then
        inferred="${session_phase}"
      fi
    fi
  fi

  echo "${inferred}"
}

_wf_infer_gates_from_artifacts() {
  local work_id="$1"
  local root="${SDLC_ROOT}"
  local req feature_req analysis canvas review retro sync_log progress

  feature_req="${root}/agent-context/features/${work_id}/requirement.md"
  req="${root}/requirements/milestones/${work_id}.md"
  analysis="${root}/spdd/analysis/${work_id}-analysis.md"
  canvas="${root}/spdd/canvas/${work_id}.md"
  review="${root}/spdd/reviews/${work_id}-review.md"
  retro="${root}/agent-context/features/${work_id}/retro.md"
  sync_log="${root}/spdd/sync/${work_id}-sync.md"
  progress="${root}/agent-context/features/${work_id}/progress-log.md"

  [[ -f "${req}" || -f "${feature_req}" ]] && echo "requirement_documented=passed"
  [[ -f "${canvas}" || -f "${root}/agent-context/features/${work_id}/reasons-canvas.md" ]] && echo "canvas_exists=passed"
  if [[ -f "${canvas}" ]] && grep -Eqi 'ready[[:space:]]+for[[:space:]]+coding' "${canvas}" 2>/dev/null; then
    echo "architect_review=passed"
    echo "operations_task_sized=passed"
  fi
  if [[ -f "${canvas}" ]] && grep -Eqi '^###[[:space:]]+T[0-9]{2}' "${canvas}" 2>/dev/null; then
    echo "operations_task_sized=passed"
  fi
  if [[ -f "${progress}" ]] && grep -Eqi '(T[0-9]{2}.*complete|implemented|merged|mvn test|pytest)' "${progress}" 2>/dev/null; then
    echo "code_maps_to_ops=passed"
    echo "tests_updated=passed"
  fi
  [[ -f "${review}" ]] && echo "review_completed=passed" && echo "safeguards_checked=passed"
  [[ -f "${retro}" ]] && echo "retro_completed=passed"
  if [[ -f "${sync_log}" ]]; then
    echo "canvas_synced=passed"
  elif [[ -f "${canvas}" && -f "${root}/agent-context/features/${work_id}/reasons-canvas.md" ]] \
    && cmp -s "${canvas}" "${root}/agent-context/features/${work_id}/reasons-canvas.md" 2>/dev/null; then
    echo "canvas_synced=passed"
  fi
  [[ -f "${analysis}" ]] && true
}

_wf_resolve_phase() {
  local stored="$1"
  local inferred="$2"
  local explicit="${3:-}"
  if [[ -n "${explicit}" ]]; then
    echo "${explicit}"
    return 0
  fi
  local stored_idx inferred_idx
  stored_idx="$(_wf_phase_index "${stored}")"
  inferred_idx="$(_wf_phase_index "${inferred}")"
  if (( inferred_idx > stored_idx )); then
    echo "${inferred}"
  else
    echo "${stored}"
  fi
}

_wf_sync_impl() {
  local work_id="$1"
  local file stored inferred resolved gate_line gate value current
  _wf_ensure_state "${work_id}"
  file="$(_wf_state_file "${work_id}")"
  stored="$(_wf_read_state_var "${file}" phase init)"
  inferred="$(_wf_infer_phase_from_artifacts "${work_id}")"
  resolved="$(_wf_resolve_phase "${stored}" "${inferred}")"
  _wf_set_state_var "${work_id}" phase "${resolved}"

  while IFS= read -r gate_line; do
    [[ -z "${gate_line}" ]] && continue
    gate="${gate_line%%=*}"
    value="${gate_line#*=}"
    current="$(_wf_read_state_var "${file}" "gate_${gate}" pending)"
    if [[ "${current}" != "skipped" ]]; then
      _wf_set_state_var "${work_id}" "gate_${gate}" "${value}"
    fi
  done < <(_wf_infer_gates_from_artifacts "${work_id}")

  _wf_log_history "${work_id}" sync "phase=${resolved}"
}

sdlc_workflow_sync() {
  local work_id="${1:-}"
  if [[ -z "${work_id}" ]]; then
    work_id="$(sdlc_get_pointer)"
  fi
  if [[ -z "${work_id}" ]]; then
    echo "sdlc_workflow_sync: no work id (set pointer or pass --work-id)" >&2
    return 2
  fi

  _wf_with_workflow_lock _wf_sync_impl "${work_id}"
  echo "workflow synced for ${work_id}"
}

_wf_touch_session_impl() {
  local work_id="$1"
  local phase="$2"
  local milestone="${3:-}"
  _wf_ensure_state "${work_id}"
  _wf_set_state_var "${work_id}" phase "${phase}"
  _wf_set_state_var "${work_id}" active 1
  _wf_set_state_var "${work_id}" shelved_at ""
  _wf_set_state_var "${work_id}" shelved_reason ""
  _wf_set_state_var "${work_id}" last_session_at "$(_wf_now)"
  [[ -n "${milestone}" ]] && _wf_set_state_var "${work_id}" milestone "${milestone}"
  _wf_log_history "${work_id}" session "phase=${phase}"
}

sdlc_workflow_touch_session() {
  local work_id="$1"
  local phase="$2"
  local milestone="${3:-}"
  _wf_with_workflow_lock _wf_touch_session_impl "${work_id}" "${phase}" "${milestone}"
}

_wf_record_capture_impl() {
  local work_id="$1"
  local phase="${2:-resume}"
  _wf_ensure_state "${work_id}"
  _wf_set_state_var "${work_id}" last_capture_at "$(_wf_now)"
  [[ "${phase}" != "resume" ]] && _wf_set_state_var "${work_id}" phase "${phase}"
  _wf_log_history "${work_id}" capture "phase=${phase}"
}

sdlc_workflow_record_capture() {
  local work_id="$1"
  local phase="${2:-resume}"
  _wf_with_workflow_lock _wf_record_capture_impl "${work_id}" "${phase}"
}

sdlc_workflow_resume() {
  local work_id="$1"
  local phase="${2:-}"
  local auto_shelf="${3:-1}"

  if [[ -z "${work_id}" ]]; then
    echo "sdlc_workflow_resume: work id required" >&2
    return 2
  fi

  local current
  current="$(sdlc_get_pointer)"
  if [[ -n "${current}" && "${current}" != "${work_id}" && "${auto_shelf}" == "1" ]]; then
    sdlc_workflow_shelf "auto-shelf before resuming ${work_id}" >/dev/null
  fi

  sdlc_set_pointer "${work_id}" >/dev/null
  _wf_ensure_state "${work_id}"
  sdlc_workflow_sync "${work_id}" >/dev/null

  if [[ -n "${phase}" ]]; then
    if ! _wf_valid_phase "${phase}"; then
      echo "sdlc_workflow_resume: invalid phase '${phase}'" >&2
      return 2
    fi
    _wf_set_state_var "${work_id}" phase "${phase}"
    _wf_log_history "${work_id}" resume "phase=${phase} (explicit)"
  else
    _wf_log_history "${work_id}" resume "phase=$(_wf_read_state_var "$(_wf_state_file "${work_id}")" phase init)"
  fi

  _wf_set_state_var "${work_id}" active 1
  _wf_set_state_var "${work_id}" shelved_at ""
  _wf_set_state_var "${work_id}" shelved_reason ""

  local resolved_phase
  resolved_phase="$(_wf_read_state_var "$(_wf_state_file "${work_id}")" phase init)"
  echo "Resumed ${work_id} at phase: ${resolved_phase}"
  echo "Recommended command: $(sdlc_workflow_recommended_command "${resolved_phase}" "${work_id}")"
  echo "Start session:"
  echo "  ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id ${work_id} --phase ${resolved_phase}"
}

sdlc_workflow_advance() {
  local to_phase="${1:-}"
  local work_id
  work_id="$(sdlc_get_pointer)"
  if [[ -z "${work_id}" ]]; then
    echo "sdlc_workflow_advance: no active pointer" >&2
    return 2
  fi

  _wf_ensure_state "${work_id}"
  local file current next
  file="$(_wf_state_file "${work_id}")"
  current="$(_wf_read_state_var "${file}" phase init)"

  if [[ -n "${to_phase}" ]]; then
    if ! _wf_valid_phase "${to_phase}"; then
      echo "sdlc_workflow_advance: invalid phase '${to_phase}'" >&2
      return 2
    fi
    local cur_idx to_idx
    cur_idx="$(_wf_phase_index "${current}")"
    to_idx="$(_wf_phase_index "${to_phase}")"
    if (( to_idx < cur_idx )); then
      echo "sdlc_workflow_advance: cannot move backward to '${to_phase}' (use resume --phase)" >&2
      return 2
    fi
    next="${to_phase}"
  else
    next="$(_wf_next_phase "${current}")"
    if [[ -z "${next}" ]]; then
      echo "Already at final phase (sync). Capture memory and refresh roadmap." >&2
      return 0
    fi
  fi

  _wf_set_state_var "${work_id}" phase "${next}"
  _wf_log_history "${work_id}" advance "${current}->${next}"
  echo "Advanced ${work_id}: ${current} -> ${next}"
  echo "Recommended command: $(sdlc_workflow_recommended_command "${next}" "${work_id}")"
}

sdlc_workflow_skip() {
  local phase="$1"
  local reason="${2:-manual skip}"
  local work_id
  work_id="$(sdlc_get_pointer)"
  if [[ -z "${work_id}" ]]; then
    echo "sdlc_workflow_skip: no active pointer" >&2
    return 2
  fi
  if ! _wf_valid_phase "${phase}"; then
    echo "sdlc_workflow_skip: invalid phase '${phase}'" >&2
    return 2
  fi

  _wf_ensure_state "${work_id}"
  local file current cur_idx skip_idx next
  file="$(_wf_state_file "${work_id}")"
  current="$(_wf_read_state_var "${file}" phase init)"
  cur_idx="$(_wf_phase_index "${current}")"
  skip_idx="$(_wf_phase_index "${phase}")"

  if (( skip_idx < cur_idx )); then
    echo "sdlc_workflow_skip: '${phase}' is before current phase '${current}'" >&2
    return 2
  fi

  _wf_set_state_var "${work_id}" "skip_${phase}" "$(_wf_now)|${reason}"
  _wf_log_history "${work_id}" skip "phase=${phase} reason=${reason}"

  if (( skip_idx == cur_idx )); then
    next="$(_wf_next_phase "${phase}")"
    if [[ -n "${next}" ]]; then
      _wf_set_state_var "${work_id}" phase "${next}"
      echo "Skipped ${phase} -> now at ${next}"
      echo "Reason: ${reason}"
      echo "Recommended command: $(sdlc_workflow_recommended_command "${next}" "${work_id}")"
    else
      echo "Skipped ${phase} (final optional phase)"
    fi
  else
    echo "Recorded skip for future phase ${phase}"
    echo "Reason: ${reason}"
  fi
}

sdlc_workflow_shelf() {
  local reason="${1:-manual shelf}"
  local work_id
  work_id="$(sdlc_get_pointer)"
  if [[ -z "${work_id}" ]]; then
    echo "sdlc_workflow_shelf: no active pointer" >&2
    return 2
  fi

  _wf_ensure_state "${work_id}"
  _wf_set_state_var "${work_id}" active 0
  _wf_set_state_var "${work_id}" shelved_at "$(_wf_now)"
  _wf_set_state_var "${work_id}" shelved_reason "${reason}"
  _wf_log_history "${work_id}" shelf "reason=${reason}"
  sdlc_reset_pointer >/dev/null
  echo "Shelved ${work_id}"
  echo "Reason: ${reason}"
  echo "Resume later: ./agent-context/sdlc-workflow.sh resume ${work_id}"
}

sdlc_workflow_list_shelved() {
  local file work_id phase shelved_at reason
  shopt -s nullglob
  for file in "${SDLC_WORKFLOW_DIR}"/*.state; do
    if [[ "$(_wf_read_state_var "${file}" active 1)" == "0" ]]; then
      work_id="$(_wf_read_state_var "${file}" work_id)"
      phase="$(_wf_read_state_var "${file}" phase init)"
      shelved_at="$(_wf_read_state_var "${file}" shelved_at)"
      reason="$(_wf_read_state_var "${file}" shelved_reason)"
      printf '%s\t%s\t%s\t%s\n' "${work_id}" "${phase}" "${shelved_at}" "${reason}"
    fi
  done
  shopt -u nullglob
}

sdlc_workflow_status() {
  local work_id="${1:-}"
  if [[ -z "${work_id}" ]]; then
    work_id="$(sdlc_get_pointer)"
  fi

  echo "SDLC Workflow Status"
  echo "===================="
  local pointer
  pointer="$(sdlc_get_pointer)"
  if [[ -n "${pointer}" ]]; then
    echo "Active pointer: ${pointer}"
  else
    echo "Active pointer: (none — resume or set a work id)"
  fi

  if [[ -z "${work_id}" ]]; then
    echo
    echo "Shelved work:"
    if sdlc_workflow_list_shelved | grep -q .; then
      sdlc_workflow_list_shelved | while IFS=$'\t' read -r wid ph at rs; do
        echo "  - ${wid} (phase: ${ph}, shelved: ${at})"
        [[ -n "${rs}" ]] && echo "    reason: ${rs}"
      done
    else
      echo "  (none)"
    fi
    return 0
  fi

  _wf_ensure_state "${work_id}"
  local file phase operation active milestone last_session last_capture
  file="$(_wf_state_file "${work_id}")"
  phase="$(_wf_read_state_var "${file}" phase init)"
  operation="$(_wf_read_state_var "${file}" operation)"
  active="$(_wf_read_state_var "${file}" active 1)"
  milestone="$(_wf_read_state_var "${file}" milestone)"
  last_session="$(_wf_read_state_var "${file}" last_session_at)"
  last_capture="$(_wf_read_state_var "${file}" last_capture_at)"

  echo
  echo "Work ID: ${work_id}"
  echo "Status: $([[ "${active}" == "1" ]] && echo active || echo shelved)"
  echo "Phase: ${phase}"

  local idx total bar filled i
  idx="$(_wf_phase_index "${phase}")"
  total="${#SDLC_PHASE_ORDER[@]}"
  filled=$((idx + 1))
  bar=""
  for ((i = 0; i < total; i++)); do
    if (( i < filled )); then bar+="="; else bar+="-"; fi
  done
  echo "Progress: [${bar}] $((filled))/${total} phases"

  if [[ -n "${operation}" ]]; then
    echo "Operation in flight: ${operation}"
  fi
  [[ -n "${milestone}" ]] && echo "Milestone: ${milestone}"
  [[ -n "${last_session}" ]] && echo "Last session: ${last_session}"
  [[ -n "${last_capture}" ]] && echo "Last capture: ${last_capture}"

  echo
  echo "Phase track:"
  local p skip_line skip_reason
  for p in "${SDLC_PHASE_ORDER[@]}"; do
    skip_line="$(_wf_read_state_var "${file}" "skip_${p}")"
    if [[ -n "${skip_line}" ]]; then
      skip_reason="${skip_line#*|}"
      echo "  - ${p}: skipped (${skip_reason})"
    elif [[ "$(_wf_phase_index "${p}")" -lt "$(_wf_phase_index "${phase}")" ]]; then
      echo "  - ${p}: done"
    elif [[ "${p}" == "${phase}" ]]; then
      echo "  - ${p}: <-- current"
    else
      echo "  - ${p}: pending"
    fi
  done

  echo
  echo "Quality gates:"
  local gi gate state label
  for ((gi = 0; gi < ${#SDLC_GATE_NAMES[@]}; gi++)); do
    gate="${SDLC_GATE_NAMES[$gi]}"
    label="${SDLC_GATE_LABELS[$gi]}"
    state="$(_wf_read_state_var "${file}" "gate_${gate}" pending)"
    case "${state}" in
      passed) echo "  [x] ${label}" ;;
      skipped) echo "  [-] ${label} (skipped)" ;;
      failed) echo "  [!] ${label} (failed)" ;;
      *) echo "  [ ] ${label}" ;;
    esac
  done

  echo
  echo "Shelved work:"
  if sdlc_workflow_list_shelved | grep -q .; then
    sdlc_workflow_list_shelved | while IFS=$'\t' read -r wid ph at rs; do
      echo "  - ${wid} (phase: ${ph}, shelved: ${at})"
    done
  else
    echo "  (none)"
  fi

  echo
  echo "Next step:"
  echo "  $(sdlc_workflow_recommended_command "${phase}" "${work_id}")"
  echo
  echo "Commands:"
  echo "  ./agent-context/sdlc-workflow.sh advance          # move to next phase"
  echo "  ./agent-context/sdlc-workflow.sh skip api-test --reason \"no HTTP surface\""
  echo "  ./agent-context/sdlc-workflow.sh shelf --reason \"blocked on review\""
  echo "  ./agent-context/sdlc-workflow.sh sync             # re-read artifacts"
  echo "  ./agent-context/sdlc-workflow.sh resume <WORK-ID> # pick up shelved work"
}

# CLI when script executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  cmd="${1:-status}"
  shift || true
  case "${cmd}" in
    status|/sdlc-workflow-status)
      work_id=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --work-id) work_id="${2:-}"; shift 2 ;;
          *) work_id="${1}"; shift ;;
        esac
      done
      sdlc_workflow_status "${work_id}"
      ;;
    resume|/sdlc-workflow-resume)
      work_id="${1:-}"; shift || true
      phase=""
      reason=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --phase) phase="${2:-}"; shift 2 ;;
          --no-auto-shelf) AUTO_SHELF=0; shift ;;
          *) shift ;;
        esac
      done
      sdlc_workflow_resume "${work_id}" "${phase}" "${AUTO_SHELF:-1}"
      ;;
    advance|/sdlc-workflow-advance)
      to=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --to) to="${2:-}"; shift 2 ;;
          *) to="${1}"; shift ;;
        esac
      done
      sdlc_workflow_advance "${to}"
      ;;
    skip|/sdlc-workflow-skip)
      phase="${1:-}"; shift || true
      reason="manual skip"
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --reason) reason="${2:-}"; shift 2 ;;
          *) shift ;;
        esac
      done
      sdlc_workflow_skip "${phase}" "${reason}"
      ;;
    shelf|/sdlc-workflow-shelf)
      reason="manual shelf"
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --reason) reason="${2:-}"; shift 2 ;;
          *) shift ;;
        esac
      done
      sdlc_workflow_shelf "${reason}"
      ;;
    sync|/sdlc-workflow-sync)
      work_id=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --work-id) work_id="${2:-}"; shift 2 ;;
          *) work_id="${1}"; shift ;;
        esac
      done
      sdlc_workflow_sync "${work_id}"
      ;;
    list-shelved|/sdlc-workflow-list-shelved)
      sdlc_workflow_list_shelved
      ;;
    *)
      echo "Usage: $0 {status|resume|advance|skip|shelf|sync|list-shelved} ..." >&2
      exit 2
      ;;
  esac
fi
