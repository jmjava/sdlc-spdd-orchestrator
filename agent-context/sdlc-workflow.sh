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
if [[ -f "${_SCRIPT_DIR}/sdlc-team-registry.sh" ]]; then
  # shellcheck source=/dev/null
  source "${_SCRIPT_DIR}/sdlc-team-registry.sh"
fi

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
  local operation="${3:-}"
  if [[ -z "${operation}" && -n "${work_id}" ]]; then
    operation="$(_wf_resolve_operation "${work_id}" "${phase}")"
  fi
  case "${phase}" in
    init) echo "/sdlc-spdd-init" ;;
    analysis) echo "/sdlc-spdd-analysis @requirements/<requirement>.md" ;;
    plan) echo "/sdlc-spdd-plan @spdd/analysis/${work_id:-<WORK-ID>}-analysis.md" ;;
    architect) echo "/sdlc-spdd-architect @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    code) echo "/sdlc-spdd-code @spdd/canvas/${work_id:-<WORK-ID>}.md operation ${operation:-<T##>}" ;;
    api-test) echo "/sdlc-spdd-api-test @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    review) echo "/sdlc-spdd-review @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    prompt-update) echo "/sdlc-spdd-prompt-update @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    retro) echo "/sdlc-spdd-retro @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    sync) echo "/sdlc-spdd-sync @spdd/canvas/${work_id:-<WORK-ID>}.md" ;;
    resume) echo "Read agent-context/sessions/current-session.md, then choose the next phase command." ;;
    *) echo "/sdlc-spdd-init" ;;
  esac
}

sdlc_workflow_shell_start() {
  local work_id="${1:-}"
  local phase="${2:-}"
  local root="${SDLC_ROOT}"
  if [[ -z "${work_id}" ]]; then
    work_id="$(sdlc_get_pointer)"
  fi
  if [[ -z "${work_id}" ]]; then
    echo "<WORK-ID>"
    return 0
  fi
  if [[ -z "${phase}" ]]; then
    phase="$(_wf_read_state_var "$(_wf_state_file "${work_id}")" phase init)"
  fi
  if [[ -x "${root}/scripts/sdlc-spdd/start-agent-session.sh" ]]; then
    echo "./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id ${work_id} --phase ${phase}"
  else
    echo "./scripts/start-agent-session.sh --target . --work-id ${work_id} --phase ${phase}"
  fi
}

sdlc_workflow_shell_capture() {
  local work_id="${1:-}"
  local phase="${2:-}"
  local helper
  helper="$(_wf_shell_helper_path)"
  if [[ -z "${work_id}" ]]; then
    work_id="$(sdlc_get_pointer)"
  fi
  if [[ -z "${work_id}" ]]; then
    echo "${helper} capture --summary \"<summary>\""
    return 0
  fi
  if [[ -z "${phase}" ]]; then
    phase="$(_wf_read_state_var "$(_wf_state_file "${work_id}")" phase resume)"
  fi
  echo "${helper} capture --phase ${phase} --summary \"<summary>\""
}

_wf_gates_for_phase() {
  case "${1:-}" in
    analysis) printf '%s\n' requirement_documented ;;
    plan) printf '%s\n' canvas_exists ;;
    architect) printf '%s\n' architect_review operations_task_sized ;;
    code) printf '%s\n' code_maps_to_ops tests_updated ;;
    api-test) printf '%s\n' tests_updated ;;
    review) printf '%s\n' review_completed safeguards_checked ;;
    retro) printf '%s\n' retro_completed ;;
    sync) printf '%s\n' canvas_synced ;;
    *) ;;
  esac
}

_wf_pass_gates_for_phase() {
  local work_id="$1"
  local phase="$2"
  local gate
  while IFS= read -r gate; do
    [[ -z "${gate}" ]] && continue
    local current
    current="$(_wf_read_state_var "$(_wf_state_file "${work_id}")" "gate_${gate}" pending)"
    if [[ "${current}" != "skipped" ]]; then
      _wf_set_state_var "${work_id}" "gate_${gate}" passed
    fi
  done < <(_wf_gates_for_phase "${phase}")
}

_wf_json_escape() {
  local s="${1:-}"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/}"
  printf '%s' "${s}"
}

_wf_pending_gates() {
  local file="$1"
  local gi gate state label pending=""
  for ((gi = 0; gi < ${#SDLC_GATE_NAMES[@]}; gi++)); do
    gate="${SDLC_GATE_NAMES[$gi]}"
    label="${SDLC_GATE_LABELS[$gi]}"
    state="$(_wf_read_state_var "${file}" "gate_${gate}" pending)"
    if [[ "${state}" == "pending" ]]; then
      pending+="${label}"$'\n'
    fi
  done
  printf '%s' "${pending%$'\n'}"
}

sdlc_workflow_brief_markdown() {
  local work_id="${1:-}"
  if [[ -z "${work_id}" ]]; then
    work_id="$(sdlc_get_pointer)"
  fi
  if [[ -z "${work_id}" ]]; then
    echo "No active Work ID. Run \`./scripts/sdlc.sh resume <WORK-ID>\`."
    return 0
  fi

  _wf_ensure_state "${work_id}"
  local file phase operation active pending op_title
  file="$(_wf_state_file "${work_id}")"
  phase="$(_wf_read_state_var "${file}" phase init)"
  operation="$(_wf_read_state_var "${file}" operation)"
  active="$(_wf_read_state_var "${file}" active 1)"
  pending="$(_wf_pending_gates "${file}")"
  op_title=""
  if [[ -n "${operation}" ]]; then
    op_title="$(_wf_operation_title "${work_id}" "${operation}")"
  fi

  cat <<EOF
| Field | Value |
|-------|-------|
| Work ID | ${work_id} |
| Workflow status | $([[ "${active}" == "1" ]] && echo active || echo shelved) |
| Phase | ${phase} ($(( $(_wf_phase_index "${phase}") + 1 ))/${#SDLC_PHASE_ORDER[@]}) |
| Next operation | ${op_title:-${operation:-none}} |
| Assistant command | $(sdlc_workflow_recommended_command "${phase}" "${work_id}" "${operation}") |
| After this phase | \`./scripts/sdlc.sh advance\` |
| Capture (guarded) | \`$(_wf_shell_helper_path) capture --summary "<summary>"\` |
| Orient / status | \`./scripts/sdlc.sh next\` or \`/sdlc-spdd-whereami\` |

$(if [[ -n "${pending}" ]]; then
  echo "Pending gates:"
  while IFS= read -r line; do
    [[ -z "${line}" ]] && continue
    echo "- ${line}"
  done <<< "${pending}"
fi)
EOF
}

sdlc_workflow_next() {
  local work_id="${1:-}"
  if [[ -z "${work_id}" ]]; then
    work_id="$(sdlc_get_pointer)"
  fi
  if [[ -z "${work_id}" ]]; then
    echo "No active Work ID."
    echo
    echo "Start here:"
    echo "  ./scripts/sdlc.sh resume <WORK-ID>     # pick up or switch task"
    echo "  ./scripts/sdlc.sh list-shelved         # see parked work"
    sdlc_workflow_list_shelved | while IFS=$'\t' read -r wid ph at rs; do
      echo "  ./scripts/sdlc.sh resume ${wid}  # shelved at ${ph}"
    done
    return 0
  fi

  sdlc_workflow_sync "${work_id}" >/dev/null
  _wf_ensure_state "${work_id}"

  local file phase operation pending next_phase op_title
  file="$(_wf_state_file "${work_id}")"
  phase="$(_wf_read_state_var "${file}" phase init)"
  operation="$(_wf_read_state_var "${file}" operation)"
  pending="$(_wf_pending_gates "${file}")"
  next_phase="$(_wf_next_phase "${phase}")"
  op_title=""
  if [[ -n "${operation}" ]]; then
    op_title="$(_wf_operation_title "${work_id}" "${operation}")"
  fi

  echo "== SDLC: what to do now =="
  echo "Work ID: ${work_id}"
  echo "Phase: ${phase} ($(( $(_wf_phase_index "${phase}") + 1 ))/${#SDLC_PHASE_ORDER[@]})"
  if [[ -n "${operation}" ]]; then
    echo "Next operation: ${op_title}"
  elif [[ "${phase}" == "code" ]]; then
    echo "Next operation: (all canvas operations complete — advance or review)"
  fi
  echo
  echo "Do now (assistant):"
  echo "  $(sdlc_workflow_recommended_command "${phase}" "${work_id}" "${operation}")"
  echo
  echo "Or run in terminal:"
  echo "  $(sdlc_workflow_shell_start "${work_id}" "${phase}")"
  echo
  if [[ -n "${pending}" ]]; then
    echo "Gates still open:"
    while IFS= read -r line; do
      [[ -z "${line}" ]] && continue
      echo "  [ ] ${line}"
    done <<< "${pending}"
    echo
  fi
  echo "When this phase is done:"
  echo "  ./scripts/sdlc.sh advance"
  if [[ -n "${next_phase}" ]]; then
    echo "  (moves to: ${next_phase})"
  fi
  echo "  $(sdlc_workflow_shell_capture "${work_id}" "${phase}")"
  echo
  if sdlc_workflow_list_shelved | grep -q .; then
    echo "Shelved (switch with resume):"
    sdlc_workflow_list_shelved | while IFS=$'\t' read -r wid ph at rs; do
      echo "  ${wid} @ ${ph}"
    done
  fi
}

sdlc_workflow_start() {
  local work_id
  work_id="$(sdlc_get_pointer)"
  if [[ -z "${work_id}" ]]; then
    echo "sdlc_workflow_start: no active pointer — run: ./scripts/sdlc.sh resume <WORK-ID>" >&2
    return 2
  fi
  sdlc_workflow_sync "${work_id}" >/dev/null
  local phase start_script
  phase="$(_wf_read_state_var "$(_wf_state_file "${work_id}")" phase init)"
  start_script="${SDLC_ROOT}/scripts/sdlc-spdd/start-agent-session.sh"
  if [[ ! -x "${start_script}" ]]; then
    start_script="${SDLC_ROOT}/scripts/start-agent-session.sh"
  fi
  if [[ ! -x "${start_script}" ]]; then
    echo "sdlc_workflow_start: start-agent-session.sh not found" >&2
    return 1
  fi
  "${start_script}" --target "${SDLC_ROOT}" --work-id "${work_id}" --phase "${phase}"
}

sdlc_workflow_status_json() {
  local work_id="${1:-}"
  if [[ -z "${work_id}" ]]; then
    work_id="$(sdlc_get_pointer)"
  fi

  local pointer phases_json gates_json shelved_json=""
  pointer="$(sdlc_get_pointer)"

  phases_json=""
  local p first=1
  for p in "${SDLC_PHASE_ORDER[@]}"; do
    [[ "${first}" -eq 1 ]] || phases_json+=","
    phases_json+="\"${p}\""
    first=0
  done

  gates_json=""
  if [[ -n "${work_id}" ]]; then
    _wf_ensure_state "${work_id}"
    local file phase operation active gi gate state
    file="$(_wf_state_file "${work_id}")"
    phase="$(_wf_read_state_var "${file}" phase init)"
    operation="$(_wf_read_state_var "${file}" operation)"
    active="$(_wf_read_state_var "${file}" active 1)"
    first=1
    gates_json="{"
    for ((gi = 0; gi < ${#SDLC_GATE_NAMES[@]}; gi++)); do
      gate="${SDLC_GATE_NAMES[$gi]}"
      state="$(_wf_read_state_var "${file}" "gate_${gate}" pending)"
      [[ "${first}" -eq 1 ]] || gates_json+=","
      gates_json+="\"${gate}\":\"${state}\""
      first=0
    done
    gates_json+="}"

    local op_title=""
    if [[ -n "${operation}" ]]; then
      op_title="$(_wf_operation_title "${work_id}" "${operation}")"
    fi

    printf '{'
    printf '"pointer":"%s",' "$(_wf_json_escape "${pointer}")"
    printf '"work_id":"%s",' "$(_wf_json_escape "${work_id}")"
    printf '"active":%s,' "$([[ "${active}" == "1" ]] && echo true || echo false)"
    printf '"phase":"%s",' "$(_wf_json_escape "${phase}")"
    printf '"phase_index":%s,' "$(_wf_phase_index "${phase}")"
    printf '"phase_total":%s,' "${#SDLC_PHASE_ORDER[@]}"
    printf '"operation":"%s",' "$(_wf_json_escape "${operation}")"
    printf '"operation_title":"%s",' "$(_wf_json_escape "${op_title}")"
    printf '"recommended_command":"%s",' "$(_wf_json_escape "$(sdlc_workflow_recommended_command "${phase}" "${work_id}" "${operation}")")"
    printf '"shell_start":"%s",' "$(_wf_json_escape "$(sdlc_workflow_shell_start "${work_id}" "${phase}")")"
    printf '"shell_capture":"%s",' "$(_wf_json_escape "$(sdlc_workflow_shell_capture "${work_id}" "${phase}")")"
    printf '"phases":[%s],' "${phases_json}"
    printf '"gates":%s' "${gates_json}"
    printf '}\n'
    return 0
  fi

  printf '{"pointer":"%s","work_id":null,"phases":[%s],"shelved":[' "$(_wf_json_escape "${pointer}")" "${phases_json}"
  first=1
  while IFS=$'\t' read -r wid ph at rs; do
    [[ -z "${wid}" ]] && continue
    [[ "${first}" -eq 1 ]] || printf ','
    first=0
    printf '{"work_id":"%s","phase":"%s","shelved_at":"%s","reason":"%s"}' \
      "$(_wf_json_escape "${wid}")" "$(_wf_json_escape "${ph}")" \
      "$(_wf_json_escape "${at}")" "$(_wf_json_escape "${rs}")"
  done < <(sdlc_workflow_list_shelved)
  printf ']}\n'
}

sdlc_workflow_help() {
  cat <<'EOF'
SDLC workflow helper — short paths for humans and agents

  ./scripts/sdlc.sh              # full status (auto-syncs from artifacts)
  ./scripts/sdlc.sh next         # concise "what do I do now?"
  ./scripts/sdlc.sh start        # open session brief at current phase
  ./scripts/sdlc.sh capture --summary "..."   # guarded capture (pointer must match)
  ./scripts/sdlc.sh status --json

  ./scripts/sdlc.sh resume <WORK-ID> [--phase PHASE]
  ./scripts/sdlc.sh advance [--to PHASE]
  ./scripts/sdlc.sh skip <PHASE> --reason "why"
  ./scripts/sdlc.sh shelf --reason "why"
  ./scripts/sdlc.sh sync [--work-id ID]
  ./scripts/sdlc.sh list-shelved
  ./scripts/sdlc.sh team              # team registry + your pointer
  ./scripts/sdlc.sh list-work         # all Work IDs in the repo
  ./scripts/sdlc.sh claim <WORK-ID>   # resume + register for team
  ./scripts/sdlc.sh release --reason "why"

In chat: /sdlc-spdd-whereami

Team sharing: commit agent-context/work-registry.tsv after claim/release/shelf.
Set SDLC_USER to override the owner name. SDLC_NO_TEAM_REGISTRY=1 opts out.

Typical loop:
  1. ./scripts/sdlc.sh next
  2. run the assistant command (or ./scripts/sdlc.sh start)
  3. ./scripts/sdlc.sh advance
  4. ./scripts/sdlc.sh capture --summary "..."

Code phase: next operation (T01, T02, ...) is read from the REASONS Canvas automatically.
EOF
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

_wf_canvas_path() {
  local work_id="$1"
  local root="${SDLC_ROOT}"
  local canvas="${root}/spdd/canvas/${work_id}.md"
  if [[ ! -f "${canvas}" ]]; then
    canvas="${root}/agent-context/features/${work_id}/reasons-canvas.md"
  fi
  if [[ -f "${canvas}" ]]; then
    printf '%s' "${canvas}"
  fi
}

_wf_infer_next_operation() {
  local work_id="$1"
  local canvas
  canvas="$(_wf_canvas_path "${work_id}")"
  [[ -n "${canvas}" ]] || return 0

  awk '
    BEGIN { op = ""; have_status = 0; complete = 0 }
    /^### T[0-9]{2}/ {
      if (op != "" && (!have_status || !complete)) {
        print op
        exit
      }
      op = $2
      sub(/-.*/, "", op)
      have_status = 0
      complete = 0
      next
    }
    op != "" && /^- Status:/ {
      have_status = 1
      line = tolower($0)
      if (line ~ /complete|: done/) {
        complete = 1
      } else {
        complete = 0
      }
      next
    }
    END {
      if (op != "" && (!have_status || !complete)) {
        print op
      }
    }
  ' "${canvas}"
}

_wf_operation_title() {
  local work_id="$1"
  local operation="$2"
  local canvas line
  canvas="$(_wf_canvas_path "${work_id}")"
  [[ -n "${canvas}" && -n "${operation}" ]] || return 0
  line="$(grep -m1 "^### ${operation} " "${canvas}" 2>/dev/null || true)"
  if [[ -n "${line}" ]]; then
    printf '%s' "${line#### }"
  else
    printf '%s' "${operation}"
  fi
}

_wf_sync_operation() {
  local work_id="$1"
  local phase="$2"
  local next_op=""
  case "${phase}" in
    code|review|architect)
      next_op="$(_wf_infer_next_operation "${work_id}")"
      ;;
  esac
  if [[ -n "${next_op}" ]]; then
    _wf_set_state_var "${work_id}" operation "${next_op}"
  else
    _wf_set_state_var "${work_id}" operation ""
  fi
}

_wf_resolve_operation() {
  local work_id="$1"
  local phase="$2"
  local operation
  operation="$(_wf_read_state_var "$(_wf_state_file "${work_id}")" operation)"
  if [[ -z "${operation}" && "${phase}" == "code" ]]; then
    operation="$(_wf_infer_next_operation "${work_id}")"
  fi
  printf '%s' "${operation}"
}

_wf_shell_helper_path() {
  if [[ -x "${SDLC_ROOT}/scripts/sdlc-spdd/sdlc.sh" ]]; then
    echo "./scripts/sdlc-spdd/sdlc.sh"
  else
    echo "./scripts/sdlc.sh"
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

  _wf_sync_operation "${work_id}" "${resolved}"
  _wf_log_history "${work_id}" sync "phase=${resolved} operation=$(_wf_read_state_var "${file}" operation)"
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

sdlc_workflow_capture() {
  local work_id=""
  local phase=""
  local -a passthrough=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --work-id)
        work_id="${2:-}"
        shift 2
        ;;
      --phase)
        phase="${2:-}"
        shift 2
        ;;
      *)
        passthrough+=("$1")
        shift
        ;;
    esac
  done

  local pointer
  pointer="$(sdlc_get_pointer)"
  if [[ -z "${work_id}" ]]; then
    work_id="${pointer}"
  elif [[ -n "${pointer}" && "${pointer}" != "${work_id}" ]]; then
    echo "sdlc_workflow_capture: --work-id '${work_id}' does not match pointer '${pointer}'" >&2
    echo "Run: $(_wf_shell_helper_path) resume ${work_id}" >&2
    return 3
  fi

  if [[ -z "${work_id}" ]]; then
    echo "sdlc_workflow_capture: no active pointer — run: $(_wf_shell_helper_path) resume <WORK-ID>" >&2
    return 2
  fi

  if [[ -z "${phase}" ]]; then
    phase="$(_wf_read_state_var "$(_wf_state_file "${work_id}")" phase resume)"
  fi

  local capture_script="${SDLC_ROOT}/scripts/sdlc-spdd/capture-session-memory.sh"
  if [[ ! -x "${capture_script}" ]]; then
    capture_script="${SDLC_ROOT}/scripts/capture-session-memory.sh"
  fi
  if [[ ! -x "${capture_script}" ]]; then
    echo "sdlc_workflow_capture: capture-session-memory.sh not found" >&2
    return 1
  fi

  run_against_pointer "${work_id}" -- "${capture_script}" \
    --target "${SDLC_ROOT}" \
    --work-id "${work_id}" \
    --phase "${phase}" \
    "${passthrough[@]}"
}

sdlc_workflow_resume() {
  local work_id="$1"
  local phase="${2:-}"
  local auto_shelf="${3:-1}"
  local force_claim="${4:-0}"

  if [[ -z "${work_id}" ]]; then
    echo "sdlc_workflow_resume: work id required" >&2
    return 2
  fi

  if declare -F sdlc_team_check_claim >/dev/null 2>&1; then
    sdlc_team_check_claim "${work_id}" "${force_claim}" || return $?
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
  echo "Quick check: ./scripts/sdlc.sh next"
  echo "Start session: $(sdlc_workflow_shell_start "${work_id}" "${resolved_phase}")"
  if declare -F sdlc_team_sync_from_workflow >/dev/null 2>&1; then
    sdlc_team_sync_from_workflow "${work_id}" "active" ""
    echo "Team: commit agent-context/work-registry.tsv to share this claim."
  fi
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

  _wf_pass_gates_for_phase "${work_id}" "${current}"
  _wf_set_state_var "${work_id}" phase "${next}"
  _wf_log_history "${work_id}" advance "${current}->${next}"
  if declare -F sdlc_team_sync_from_workflow >/dev/null 2>&1; then
    sdlc_team_sync_from_workflow "${work_id}" "active" ""
  fi
  echo "Advanced ${work_id}: ${current} -> ${next}"
  echo "Recommended command: $(sdlc_workflow_recommended_command "${next}" "${work_id}")"
  echo "Quick check: ./scripts/sdlc.sh next"
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
  if declare -F sdlc_team_sync_from_workflow >/dev/null 2>&1; then
    sdlc_team_sync_from_workflow "${work_id}" "shelved" "${reason}"
    echo "Team: commit agent-context/work-registry.tsv to share shelf status."
  fi
  echo "Shelved ${work_id}"
  echo "Reason: ${reason}"
  echo "Resume later: ./scripts/sdlc.sh resume ${work_id}"
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
  echo "Quick commands:"
  echo "  ./scripts/sdlc.sh next              # concise what-to-do-now"
  echo "  ./scripts/sdlc.sh start             # open session brief"
  echo "  ./scripts/sdlc.sh advance           # move to next phase"
  echo "  ./scripts/sdlc.sh skip api-test --reason \"...\""
  echo "  ./scripts/sdlc.sh shelf --reason \"...\""
  echo "  ./scripts/sdlc.sh sync              # re-read artifacts"
  echo "  ./scripts/sdlc.sh resume <WORK-ID>  # pick up shelved work"
}

# CLI when script executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  cmd="${1:-status}"
  shift || true
  case "${cmd}" in
    status|/sdlc-workflow-status)
      work_id=""
      format="text"
      do_sync=1
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --work-id) work_id="${2:-}"; shift 2 ;;
          --json) format="json"; shift ;;
          --no-sync) do_sync=0; shift ;;
          --sync) do_sync=1; shift ;;
          -h|--help) sdlc_workflow_help; exit 0 ;;
          *) work_id="${1}"; shift ;;
        esac
      done
      if [[ -z "${work_id}" ]]; then
        work_id="$(sdlc_get_pointer)"
      fi
      if [[ "${do_sync}" -eq 1 && -n "${work_id}" ]]; then
        sdlc_workflow_sync "${work_id}" >/dev/null
      fi
      if [[ "${format}" == "json" ]]; then
        sdlc_workflow_status_json "${work_id}"
      else
        sdlc_workflow_status "${work_id}"
      fi
      ;;
    next|/sdlc-workflow-next)
      work_id=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --work-id) work_id="${2:-}"; shift 2 ;;
          *) work_id="${1}"; shift ;;
        esac
      done
      sdlc_workflow_next "${work_id}"
      ;;
    start|/sdlc-workflow-start)
      sdlc_workflow_start
      ;;
    help|-h|--help)
      sdlc_workflow_help
      ;;
    resume|/sdlc-workflow-resume)
      work_id="${1:-}"; shift || true
      phase=""
      force_claim=0
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --phase) phase="${2:-}"; shift 2 ;;
          --force) force_claim=1; shift ;;
          --no-auto-shelf) AUTO_SHELF=0; shift ;;
          *) shift ;;
        esac
      done
      sdlc_workflow_resume "${work_id}" "${phase}" "${AUTO_SHELF:-1}" "${force_claim}"
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
    capture|/sdlc-workflow-capture)
      sdlc_workflow_capture "$@"
      ;;
    team|/sdlc-team-status)
      if declare -F sdlc_team_status >/dev/null 2>&1; then
        sdlc_team_status
      else
        echo "team registry not installed" >&2
        exit 1
      fi
      ;;
    list-work|/sdlc-list-work)
      if declare -F sdlc_team_list_work >/dev/null 2>&1; then
        sdlc_team_list_work
      else
        echo "team registry not installed" >&2
        exit 1
      fi
      ;;
    claim|/sdlc-team-claim)
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
      if declare -F sdlc_team_claim >/dev/null 2>&1; then
        sdlc_team_claim "${work_id}" "${force}" "${phase}"
      else
        echo "team registry not installed" >&2
        exit 1
      fi
      ;;
    release|/sdlc-team-release)
      reason="released"
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --reason) reason="${2:-}"; shift 2 ;;
          *) shift ;;
        esac
      done
      if declare -F sdlc_team_release >/dev/null 2>&1; then
        sdlc_team_release "${reason}"
      else
        echo "team registry not installed" >&2
        exit 1
      fi
      ;;
    *)
      echo "Usage: $0 {status|next|start|capture|resume|advance|skip|shelf|sync|team|list-work|claim|release|list-shelved|help} ..." >&2
      echo "Try: $0 help" >&2
      exit 2
      ;;
  esac
fi
