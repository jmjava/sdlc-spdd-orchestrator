#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: start-agent-session.sh [--target <path>] [--work-id <WORK-ID>] [--phase <phase>]

Create a durable SDLC-SPDD session brief that helps a new agent session resume
previous work with the right SDLC phase, REASONS Canvas, memory, and handoff context.

Phases:
  init, plan, architect, code, review, prompt-update, retro, sync, resume

Examples:
  ./scripts/start-agent-session.sh --target /path/to/app --work-id FEAT-001-order-status-api --phase code
  ./scripts/start-agent-session.sh --target . --phase plan
EOF
}

TARGET="."
WORK_ID=""
PHASE="resume"

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
  init|plan|architect|code|review|prompt-update|retro|sync|resume) ;;
  *)
    echo "Unsupported phase: ${PHASE}" >&2
    usage >&2
    exit 1
    ;;
esac

TARGET="$(cd "${TARGET}" && pwd)"
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
  plan)
    recommended_command="/sdlc-spdd-plan @requirements/<requirement>.md"
    ;;
  architect)
    recommended_command="/sdlc-spdd-architect @spdd/canvas/${WORK_ID:-<WORK-ID>}.md"
    ;;
  code)
    recommended_command="/sdlc-spdd-code @spdd/canvas/${WORK_ID:-<WORK-ID>}.md operation <T##>"
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

cat > "${session_file}" <<EOF
# SDLC-SPDD Agent Session

## Metadata

- Timestamp: ${timestamp}
- Target: ${TARGET}
- Work ID: ${WORK_ID:-none}
- Phase: ${PHASE}
- Recommended command: ${recommended_command}
- Canvas sync state: ${canvas_sync_state}
- Previous session brief: ${latest_session}

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

- ROADMAP.md
- milestone-*.md
- session-notes/
- agent-context/memory/project-memory.md
- agent-context/memory/session-history.md
- agent-context/memory/architecture-decisions.md
- agent-context/memory/known-pitfalls.md
- agent-context/memory/reusable-patterns.md
- agent-context/harness/quality-gates.md
- agent-context/harness/validation-rules.md

## Playbooks To Consider

- agent-context/playbooks/java-feature-playbook.md
- agent-context/playbooks/bugfix-playbook.md
- agent-context/playbooks/refactor-playbook.md
- agent-context/playbooks/pr-review-playbook.md
- agent-context/playbooks/session-handoff-playbook.md

## Git Status

    ${git_status//$'\n'/$'\n'    }

## Resume Prompt

Use this prompt at the start of the new agent session:

    For ${WORK_ID:-<WORK-ID>}, read @agent-context/sessions/current-session.md, the relevant canvas, progress log, memory files, and current git status. Continue in the ${PHASE} phase using the hybrid SDLC Agents + SPDD workflow. Recommended command: ${recommended_command}

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
