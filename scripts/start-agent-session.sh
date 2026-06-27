#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: start-agent-session.sh [--target <path>] [--work-id <WORK-ID>] [--phase <phase>] [--milestone <file>]

Create a durable SDLC-SPDD session brief that helps a new agent session resume
previous work with the right SDLC phase, REASONS Canvas, memory, and handoff context.

Phases:
  init, analysis, plan, architect, code, api-test, review, prompt-update, retro, sync, resume

Options:
  --milestone <file>    Active milestone doc, such as milestone-1.md. When omitted
                        and --work-id is set, the script searches milestone-*.md
                        files for a matching Work ID.

Examples:
  ./scripts/start-agent-session.sh --target /path/to/app --work-id FEAT-001-order-status-api --phase code
  ./scripts/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code --milestone milestone-1.md
  ./scripts/start-agent-session.sh --target . --phase plan
EOF
}

TARGET="."
WORK_ID=""
PHASE="resume"
MILESTONE=""

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
    --phase)
      PHASE="${2:-}"
      shift 2
      ;;
    --milestone)
      MILESTONE="${2:-}"
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

case "${PHASE}" in
  init|analysis|plan|architect|code|api-test|review|prompt-update|retro|sync|resume) ;;
  *)
    echo "Unsupported phase: ${PHASE}" >&2
    usage >&2
    exit 1
    ;;
esac

TARGET="$(cd "${TARGET}" && pwd)"

pointer_script="${TARGET}/agent-context/sdlc-pointer.sh"
if [[ -f "${pointer_script}" && -n "${WORK_ID}" ]]; then
  SDLC_ROOT="${TARGET}"
  # shellcheck source=/dev/null
  source "${pointer_script}"
  sdlc_set_pointer "${WORK_ID}" >/dev/null
fi

workflow_script="${TARGET}/agent-context/sdlc-workflow.sh"
workflow_brief_md="Workflow tools not installed."
if [[ -f "${workflow_script}" && -n "${WORK_ID}" ]]; then
  SDLC_ROOT="${TARGET}"
  # shellcheck source=/dev/null
  source "${workflow_script}"
  sdlc_workflow_touch_session "${WORK_ID}" "${PHASE}" "${MILESTONE}"
  sdlc_workflow_sync "${WORK_ID}" >/dev/null 2>&1 || true
  workflow_brief_md="$(sdlc_workflow_brief_markdown "${WORK_ID}")"
fi

timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
safe_timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
session_dir="${TARGET}/agent-context/sessions"
mkdir -p "${session_dir}"

session_name="${safe_timestamp}-${PHASE}"
if [[ -n "${WORK_ID}" ]]; then
  session_name="${session_name}-${WORK_ID}"
fi
session_file="${session_dir}/${session_name}.md"
current_file="${session_dir}/current-session.md"
roadmap_file="${TARGET}/ROADMAP.md"
session_notes_dir="${TARGET}/session-notes"
today_note="${session_notes_dir}/$(date -u +"%Y-%m-%d").md"

feature_dir=""
feature_canvas=""
canonical_canvas=""
progress_log=""
review_report=""
sync_log=""
retro_file=""
if [[ -n "${WORK_ID}" ]]; then
  feature_dir="${TARGET}/agent-context/features/${WORK_ID}"
  feature_canvas="${feature_dir}/reasons-canvas.md"
  canonical_canvas="${TARGET}/spdd/canvas/${WORK_ID}.md"
  progress_log="${feature_dir}/progress-log.md"
  review_report="${TARGET}/spdd/reviews/${WORK_ID}-review.md"
  sync_log="${TARGET}/spdd/sync/${WORK_ID}-sync.md"
  retro_file="${feature_dir}/retro.md"
fi

status_for() {
  local path="$1"
  if [[ -z "${path}" ]]; then
    echo "not applicable"
  elif [[ -e "${path}" ]]; then
    echo "present"
  else
    echo "missing"
  fi
}

canvas_sync_state="not applicable"
if [[ -n "${WORK_ID}" ]]; then
  if [[ -f "${feature_canvas}" && -f "${canonical_canvas}" ]]; then
    if cmp -s "${feature_canvas}" "${canonical_canvas}"; then
      canvas_sync_state="in sync"
    else
      canvas_sync_state="drift detected"
    fi
  elif [[ -f "${feature_canvas}" || -f "${canonical_canvas}" ]]; then
    canvas_sync_state="one canvas copy missing"
  else
    canvas_sync_state="no canvas found"
  fi
fi

recommended_command="/sdlc-spdd-init"
case "${PHASE}" in
  init)
    recommended_command="/sdlc-spdd-init"
    ;;
  analysis)
    recommended_command="/sdlc-spdd-analysis @requirements/<requirement>.md"
    ;;
  plan)
    recommended_command="/sdlc-spdd-plan @spdd/analysis/${WORK_ID:-<WORK-ID>}-analysis.md"
    ;;
  architect)
    recommended_command="/sdlc-spdd-architect @spdd/canvas/${WORK_ID:-<WORK-ID>}.md"
    ;;
  code)
    recommended_command="/sdlc-spdd-code @spdd/canvas/${WORK_ID:-<WORK-ID>}.md operation <T##>"
    ;;
  api-test)
    recommended_command="/sdlc-spdd-api-test @spdd/canvas/${WORK_ID:-<WORK-ID>}.md"
    ;;
  review)
    recommended_command="/sdlc-spdd-review @spdd/canvas/${WORK_ID:-<WORK-ID>}.md"
    ;;
  prompt-update)
    recommended_command="/sdlc-spdd-prompt-update @spdd/canvas/${WORK_ID:-<WORK-ID>}.md"
    ;;
  retro)
    recommended_command="/sdlc-spdd-retro @spdd/canvas/${WORK_ID:-<WORK-ID>}.md"
    ;;
  sync)
    recommended_command="/sdlc-spdd-sync @spdd/canvas/${WORK_ID:-<WORK-ID>}.md"
    ;;
  resume)
    recommended_command="Read this session brief, then choose plan, architect, code, review, prompt-update, retro, or sync."
    ;;
esac

git_status="not a git repository"
if git -C "${TARGET}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git_status="$(git -C "${TARGET}" status --short)"
  if [[ -z "${git_status}" ]]; then
    git_status="clean"
  fi
fi

latest_session="none"
shopt -s nullglob
session_files=("${session_dir}"/*.md)
shopt -u nullglob
if ((${#session_files[@]} > 0)); then
  latest_session="$(ls -t "${session_dir}"/*.md 2>/dev/null | head -n 1 || true)"
fi

milestone_list="- none found"
shopt -s nullglob
milestone_files=("${TARGET}"/milestone-*.md)
shopt -u nullglob
if ((${#milestone_files[@]} > 0)); then
  milestone_list=""
  for file in "${milestone_files[@]}"; do
    milestone_list+="- ${file#${TARGET}/}"$'\n'
  done
  milestone_list="${milestone_list%$'\n'}"
fi

resolve_milestone() {
  local candidate="${1:-}"
  if [[ -n "${candidate}" ]]; then
    if [[ "${candidate}" != *.md ]]; then
      candidate="${candidate}.md"
    fi
    if [[ -f "${TARGET}/${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
    if [[ -f "${candidate}" ]]; then
      echo "${candidate#${TARGET}/}"
      return 0
    fi
    echo ""
    return 1
  fi

  if [[ -z "${WORK_ID}" ]]; then
    echo ""
    return 1
  fi

  shopt -s nullglob
  for file in "${milestone_files[@]}"; do
    if grep -q "${WORK_ID}" "${file}" 2>/dev/null; then
      echo "${file#${TARGET}/}"
      shopt -u nullglob
      return 0
    fi
  done
  shopt -u nullglob
  echo ""
  return 1
}

active_milestone="$(resolve_milestone "${MILESTONE}" || true)"
today_note_rel="session-notes/$(date -u +"%Y-%m-%d").md"

resolve_script=""
if [[ -x "${TARGET}/scripts/sdlc-spdd/resolve-agent-context.sh" ]]; then
  resolve_script="${TARGET}/scripts/sdlc-spdd/resolve-agent-context.sh"
elif [[ -x "$(dirname "${BASH_SOURCE[0]}")/resolve-agent-context.sh" ]]; then
  resolve_script="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/resolve-agent-context.sh"
fi

resolved_context_md="No resolved context (run with a supported --phase)."
resolved_paths_raw=""
if [[ -n "${resolve_script}" && "${PHASE}" != "resume" ]]; then
  resolve_args=(--target "${TARGET}" --phase "${PHASE}" --format markdown)
  resolve_path_args=(--target "${TARGET}" --phase "${PHASE}" --format paths)
  if [[ -n "${WORK_ID}" ]]; then
    resolve_args+=(--work-id "${WORK_ID}")
    resolve_path_args+=(--work-id "${WORK_ID}")
  fi
  resolved_context_md="$("${resolve_script}" "${resolve_args[@]}" 2>/dev/null || true)"
  resolved_paths_raw="$("${resolve_script}" "${resolve_path_args[@]}" 2>/dev/null || true)"
  if [[ -z "${resolved_context_md}" ]]; then
    resolved_context_md="No resolved context files for phase ${PHASE}."
  fi
fi

resolved_includes() {
  local needle="$1"
  grep -Fxq "${needle}" <<< "${resolved_paths_raw}"
}

resume_prompt="For ${WORK_ID:-<WORK-ID>}, read @agent-context/sessions/current-session.md first."
resume_prompt+=$'\n\n'"Load only the files listed under **Resolved Context** in that brief for the ${PHASE} phase (SDLC Agents progressive disclosure)."
if [[ -n "${WORK_ID}" && ( "${PHASE}" == "code" || "${PHASE}" == "review" || "${PHASE}" == "architect" || "${PHASE}" == "api-test" || "${PHASE}" == "retro" || "${PHASE}" == "sync" ) ]]; then
  if ! resolved_includes "spdd/canvas/${WORK_ID}.md"; then
    resume_prompt+=$'\n'"Also read @spdd/canvas/${WORK_ID}.md for this Work ID."
  fi
fi
if [[ "${PHASE}" == "plan" && -n "${WORK_ID}" ]]; then
  if ! resolved_includes "spdd/analysis/${WORK_ID}-analysis.md"; then
    resume_prompt+=$'\n'"Also read @spdd/analysis/${WORK_ID}-analysis.md before planning."
  fi
fi
if [[ "${PHASE}" == "analysis" ]]; then
  resume_prompt+=$'\n'"Use @requirements/ or milestone sources named in the brief; filter indexes before scanning code."
fi

resume_prompt+=$'\n\n'"Continue in the ${PHASE} phase using the hybrid SDLC Agents + SPDD workflow."
resume_prompt+=$'\n'"Recommended command: ${recommended_command}"

resume_prompt_indented="$(printf '%s\n' "${resume_prompt}" | sed 's/^/    /')"

cat > "${session_file}" <<EOF
# SDLC-SPDD Agent Session

## Metadata

- Timestamp: ${timestamp}
- Target: ${TARGET}
- Work ID: ${WORK_ID:-none}
- Phase: ${PHASE}
- Active milestone: ${active_milestone:-none}
- Recommended command: ${recommended_command}
- Canvas sync state: ${canvas_sync_state}
- Previous session brief: ${latest_session}

## Workflow State

Local phase + gate tracking (not committed). Refresh with \`./scripts/sdlc.sh next\` or \`/sdlc-spdd-whereami\`.

${workflow_brief_md}

## Framework Orientation

New agents: load these first so you know how to operate within the SDLC-SPDD framework before doing any work.

- Operating model + work rules: the always-on grounding file (.cursor/rules/sdlc-spdd.mdc, .github/copilot-instructions.md, or CLAUDE.md) is loaded on every request.
- How the framework works: docs/sdlc-spdd/three-part-operating-path.md, docs/sdlc-spdd/ten-thousand-foot-view.md.
- Session + context-loading rules: docs/sdlc-spdd/context-loading-and-scaling.md#bootstrap-and-index-based-loading (bootstrap layers, index catalog, retrieval, capture).
- Resolve phase skills/extensions: ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase ${PHASE}

## Hybrid Operating Model

- SDLC Agents side: use the phase-specific role, load only relevant context, preserve handoffs, and capture learning.
- SPDD side: treat the REASONS Canvas as the governing prompt contract and keep prompt artifacts synchronized with code.

## Artifact Status

| Artifact | Path | Status |
|----------|------|--------|
| Feature workspace | ${feature_dir:-not applicable} | $(status_for "${feature_dir}") |
| Feature canvas | ${feature_canvas:-not applicable} | $(status_for "${feature_canvas}") |
| Canonical canvas | ${canonical_canvas:-not applicable} | $(status_for "${canonical_canvas}") |
| Progress log | ${progress_log:-not applicable} | $(status_for "${progress_log}") |
| Review report | ${review_report:-not applicable} | $(status_for "${review_report}") |
| Sync log | ${sync_log:-not applicable} | $(status_for "${sync_log}") |
| Retro | ${retro_file:-not applicable} | $(status_for "${retro_file}") |

## Roadmap and Milestone Context

| Artifact | Path | Status |
|----------|------|--------|
| Roadmap | ROADMAP.md | $(status_for "${roadmap_file}") |
| Today's session notes | session-notes/$(date -u +"%Y-%m-%d").md | $(status_for "${today_note}") |

Milestone docs:

${milestone_list}

## Persistent Memory To Read

Use **Resolved Context** below first (static + area-filtered index rows). For manual lookup:

- agent-context/memory/context-index.md — filter by Area when you know the code area
- agent-context/memory/domain-index.md — filter by Keyword during analysis
- agent-context/memory/session-index.md — session-only view (newest first)
- agent-context/memory/code-areas.md — canonical area categories

Do not read session-history.md top-to-bottom or load whole memory logs when index rows already point at the relevant entries.

## Resolved Context

Phase-specific extensions, playbooks, Work ID artifacts, and area-filtered index matches for **${PHASE}** (from resolve-agent-context.sh):

${resolved_context_md}

Refresh after adding extensions, code areas, or `#SkillName` skills:

    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase ${PHASE}${WORK_ID:+ --work-id ${WORK_ID}}
    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase ${PHASE} --text "#TDD #java"

## Git Status

    ${git_status//$'\n'/$'\n'    }

## Resume Prompt

Use this prompt at the start of the new agent session. See docs/sdlc-spdd/session-prompt-standard.md for the full prompt contract.

${resume_prompt_indented}

## Session Notes

Add notes here during the session, then persist them with:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id ${WORK_ID:-<WORK-ID>} --phase ${PHASE} --summary "<summary>" --validation "<validation>" --next "<next command>"
EOF

cp "${session_file}" "${current_file}"

echo "Created session brief:"
echo "  ${session_file}"
echo "Updated current session:"
echo "  ${current_file}"
echo "Recommended command:"
echo "  ${recommended_command}"
