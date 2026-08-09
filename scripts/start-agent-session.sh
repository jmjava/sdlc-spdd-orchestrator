#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/milestone.sh"

usage() {
  cat <<'EOF'
Usage: start-agent-session.sh [--target <path>] [--work-id <WORK-ID>] [--phase <phase>] [--milestone <file>] [--quiet]

Create a durable SDLC-SPDD session brief that helps a new agent session resume
previous work with the right SDLC phase, REASONS Canvas, memory, and handoff context.

Hot session briefs are written under .sdlc/sessions/ (gitignored).

Phases:
  init, analysis, plan, architect, code, api-test, review, prompt-update, retro, sync, resume

Options:
  --milestone <file>     Active milestone doc (root milestone-1.md or
                         requirements/milestones/milestone-1/MILESTONE-1.md).
                         When omitted and --work-id is set, searches known
                         milestone definitions for a matching Work ID.
  --session-limit <n>    Keep at most N timestamped briefs in sessions/
                         (older move to sessions/archive/; default 20)
  --no-session-rotate    Do not archive older timestamped session briefs
  --quiet                Suppress T## / dogfood recommended-command gravity (#91)
  --help                 Print this help

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
SESSION_LIMIT=20
SESSION_ROTATE=1
QUIET=0

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
    --session-limit)
      SESSION_LIMIT="${2:-20}"
      shift 2
      ;;
    --no-session-rotate)
      SESSION_ROTATE=0
      shift
      ;;
    --quiet)
      QUIET=1
      shift
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

TARGET="$(sdlc_resolve_target "${TARGET}")"
export SDLC_ROOT="${TARGET}"
HOME="$(sdlc_home "${TARGET}")"

pointer_script="${HOME}/scripts/sdlc-pointer.sh"
if [[ ! -f "${pointer_script}" ]]; then
  pointer_script="${TARGET}/agent-context/sdlc-pointer.sh"
fi
if [[ -f "${pointer_script}" && -n "${WORK_ID}" ]]; then
  SDLC_ROOT="${TARGET}"
  # shellcheck source=/dev/null
  source "${pointer_script}"
  sdlc_set_pointer "${WORK_ID}" >/dev/null
fi

workflow_script="${HOME}/scripts/sdlc-workflow.sh"
if [[ ! -f "${workflow_script}" ]]; then
  workflow_script="${TARGET}/agent-context/sdlc-workflow.sh"
fi
team_script="${HOME}/scripts/sdlc-team-registry.sh"
if [[ ! -f "${team_script}" ]]; then
  team_script="${TARGET}/agent-context/sdlc-team-registry.sh"
fi
workflow_brief_md="Workflow tools not installed."
jira_status=""
jira_ask_prompt=""
if [[ -f "${workflow_script}" && -n "${WORK_ID}" ]]; then
  SDLC_ROOT="${TARGET}"
  # shellcheck source=/dev/null
  source "${workflow_script}"
  sdlc_workflow_touch_session "${WORK_ID}" "${PHASE}" "${MILESTONE}"
  sdlc_workflow_sync "${WORK_ID}" >/dev/null 2>&1 || true
  workflow_brief_md="$(sdlc_workflow_brief_markdown "${WORK_ID}")"
elif [[ -f "${team_script}" && -n "${WORK_ID}" ]]; then
  SDLC_ROOT="${TARGET}"
  # shellcheck source=/dev/null
  source "${team_script}"
fi
if [[ -n "${WORK_ID}" ]] && declare -F sdlc_team_jira_status >/dev/null 2>&1; then
  jira_status="$(sdlc_team_jira_status "${WORK_ID}")"
fi
if [[ -n "${WORK_ID}" ]] && declare -F sdlc_team_jira_ask_prompt >/dev/null 2>&1; then
  jira_ask_prompt="$(sdlc_team_jira_ask_prompt "${WORK_ID}")"
fi

timestamp="$(sdlc_timestamp_iso)"
safe_timestamp="$(sdlc_timestamp_file)"
# Hot path (#85): gitignored .sdlc/sessions — never write new briefs to committed trees.
session_dir="$(sdlc_sessions_dir "${TARGET}")"
mkdir -p "${session_dir}"

# Quiet / product-test mode (#91)
if [[ "${QUIET}" -eq 0 ]]; then
  _q="$(printf '%s' "${SDLC_QUIET:-}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${_q}" == "1" || "${_q}" == "true" || "${_q}" == "yes" || "${_q}" == "on" ]]; then
    QUIET=1
  elif [[ -f "$(sdlc_harness_dir "${TARGET}")/quiet-mode.md" ]]; then
    QUIET=1
  fi
fi

session_name="${safe_timestamp}-${PHASE}"
if [[ -n "${WORK_ID}" ]]; then
  session_name="${session_name}-${WORK_ID}"
fi
session_file="${session_dir}/${session_name}.md"
current_file="${session_dir}/current-session.md"
roadmap_file="${HOME}/ROADMAP.md"
session_notes_dir="${HOME}/session-notes"
today_note="${session_notes_dir}/$(sdlc_timestamp_day).md"

canonical_canvas=""
if [[ -n "${WORK_ID}" ]]; then
  canonical_canvas="${HOME}/spdd/canvas/${WORK_ID}.md"
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
if [[ -n "${WORK_ID}" && -f "${canonical_canvas}" ]]; then
  canvas_sync_state="present"
elif [[ -n "${WORK_ID}" ]]; then
  canvas_sync_state="missing"
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

# Prefer workflow helper when installed — honors Ready For Coding gate for code phase.
export SDLC_ROOT="${TARGET}"
if [[ "${QUIET}" -eq 1 ]]; then
  export SDLC_QUIET=1
fi
if [[ "${QUIET}" -eq 0 ]] && declare -F sdlc_workflow_recommended_command >/dev/null 2>&1 && [[ -n "${WORK_ID}" ]]; then
  recommended_command="$(sdlc_workflow_recommended_command "${PHASE}" "${WORK_ID}")"
fi
if [[ "${QUIET}" -eq 1 ]]; then
  recommended_command="Quiet mode: retrieve context via SQLite/Guide/context store; no T## dogfood command."
fi

git_status="not a git repository"
if git -C "${TARGET}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git_status="$(git -C "${TARGET}" status --short)"
  if [[ -z "${git_status}" ]]; then
    git_status="clean"
  fi
fi

latest_session="none"
# Previous brief = newest existing *timestamped* file (exclude current-session.md).
shopt -s nullglob
mapfile -t _prior_briefs < <(ls -t "${session_dir}"/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]T*.md 2>/dev/null || true)
shopt -u nullglob
if ((${#_prior_briefs[@]} > 0)); then
  latest_session="${_prior_briefs[0]}"
fi

milestone_list="- none found"
mapfile -t milestone_files < <(list_milestone_files "${HOME}" absolute 2>/dev/null || true)
if ((${#milestone_files[@]} > 0)); then
  milestone_list=""
  for file in "${milestone_files[@]}"; do
    milestone_list+="- ${file#${TARGET}/}"$'\n'
  done
  milestone_list="${milestone_list%$'\n'}"
fi

active_milestone="$(resolve_milestone "${HOME}" "${WORK_ID}" "${MILESTONE}" relative || true)"
today_note_rel="session-notes/$(sdlc_timestamp_day).md"

# Command + docs hints in the brief must match the actual layout: v3 installs
# use sdlc-spdd/scripts + sdlc-spdd/docs; the orchestrator repo keeps scripts/.
if [[ "${HOME}" != "${TARGET}" ]]; then
  scripts_hint="./sdlc-spdd/scripts"
  sdlc_sh_hint="./sdlc-spdd/scripts/sdlc.sh"
  docs_hint="sdlc-spdd/docs"
else
  scripts_hint="./scripts"
  sdlc_sh_hint="./scripts/sdlc.sh"
  docs_hint="docs/sdlc-spdd"
  [[ -d "${TARGET}/docs/sdlc-spdd" ]] || docs_hint="docs"
fi

resolve_script=""
if [[ -x "${HOME}/scripts/resolve-agent-context.sh" ]]; then
  resolve_script="${HOME}/scripts/resolve-agent-context.sh"
elif [[ -x "${TARGET}/scripts/sdlc-spdd/resolve-agent-context.sh" ]]; then
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

# Soft-fail Local SQLite Index lookup for the active Work ID (FEAT-007).
# Never fails session start when the Python engine / index is unavailable.
sqlite_section_md=""
sqlite_lookup_loaded=0
if [[ -n "${WORK_ID}" ]]; then
  _run_db_lookup() {
    local out=""
    if [[ -x "${TARGET}/scripts/sdlc-spdd/sdlc.sh" ]]; then
      out="$(
        SDLC_ENGINE=python SDLC_ROOT="${TARGET}" \
          "${TARGET}/scripts/sdlc-spdd/sdlc.sh" db lookup \
          --work-id "${WORK_ID}" \
          --markdown 2>/dev/null || true
      )"
    fi
    if [[ -z "${out}" ]] && python3 -c 'import sdlc_engine' 2>/dev/null; then
      out="$(
        python3 -m sdlc_engine --root "${TARGET}" db lookup \
          --work-id "${WORK_ID}" \
          --markdown 2>/dev/null || true
      )"
    fi
    printf '%s' "${out}"
  }
  sqlite_section_md="$(_run_db_lookup)"
  if [[ -n "${sqlite_section_md}" ]] && grep -Fq 'Local SQLite Index' <<<"${sqlite_section_md}"; then
    sqlite_lookup_loaded=1
  else
    sqlite_section_md=""
  fi
fi

resume_prompt="For ${WORK_ID:-<WORK-ID>}, read @.sdlc/sessions/current-session.md first."
resume_prompt+=$'\n\n'"Load only the files listed under **Resolved Context** in that brief for the ${PHASE} phase (SDLC Agents progressive disclosure)."
if [[ "${sqlite_lookup_loaded}" -eq 1 ]]; then
  resume_prompt+=$'\n'"Also treat **Local SQLite Index (query cache)** in that brief as loaded lookup context for Work ID ${WORK_ID} (regenerable cache; prefer canvas/requirement files if they disagree)."
fi
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
if [[ "${QUIET}" -eq 1 ]]; then
  resume_prompt+=$'\n'"Quiet/product-test mode: skip T## dogfood recommended commands; retrieve context via SQLite/Guide/context store as needed."
else
  resume_prompt+=$'\n'"Recommended command: ${recommended_command}"
fi
if [[ -n "${jira_ask_prompt}" ]]; then
  resume_prompt+=$'\n\n'"${jira_ask_prompt}"
elif [[ -n "${jira_status}" && "${jira_status}" != "missing" && "${jira_status}" != "draft" ]]; then
  resume_prompt+=$'\n'"Jira: ${jira_status}"
fi

resume_prompt_indented="$(printf '%s\n' "${resume_prompt}" | sed 's/^/    /')"

digest_md=""
if [[ -n "${WORK_ID}" ]]; then
  _milestone_path="${HOME}/requirements/milestones/${WORK_ID}.md"
  _analysis_path="${HOME}/spdd/analysis/${WORK_ID}-analysis.md"
  digest_md="$(python3 - <<PY
import json, re, subprocess
from pathlib import Path

root = Path(${TARGET@Q})
home = Path(${HOME@Q})
wid = ${WORK_ID@Q}
ledger = home / "spdd/memory/lessons.jsonl"
stage = home / ".sdlc/staged/lessons.jsonl"
milestone = Path(${_milestone_path@Q})
analysis = Path(${_analysis_path@Q})

areas = []
keywords = []

def bullets(path, heading):
    if not path.is_file():
        return []
    out = []
    in_sec = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_sec = line[3:].strip().lower() == heading.lower()
            continue
        if in_sec and re.match(r"^[-*]\s+", line):
            out.append(re.sub(r"^[-*]\s+", "", line).strip())
    return out

areas.extend(bullets(analysis, "Code Areas"))
keywords.extend(bullets(analysis, "Domain Keywords"))
areas = [a for a in areas if a]
keywords = [k for k in keywords if k]
area_set = set(areas)
kw_set = {k.lower() for k in keywords}

def read_jsonl(path):
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows

matches = {}
for rec in read_jsonl(ledger) + read_jsonl(stage):
    hit = False
    if rec.get("work_id") == wid:
        hit = True
    if rec.get("area") in area_set:
        hit = True
    if kw_set and kw_set.intersection(k.lower() for k in rec.get("keywords") or []):
        hit = True
    if hit:
        matches[rec.get("id", "")] = rec

sorted_recs = sorted(matches.values(), key=lambda r: (r.get("ts", ""), r.get("id", "")), reverse=True)
counts = {}
for rec in sorted_recs:
    counts[rec.get("kind", "?")] = counts.get(rec.get("kind", "?"), 0) + 1

lines = ["## Related Past Work (digest — fetch bodies on demand)", ""]
if not sorted_recs:
    lines.append("No matching ledger records yet.")
else:
    count_parts = [f"{k}={v}" for k, v in sorted(counts.items())]
    lines.append("Counts: " + ", ".join(count_parts))
    lines.append("")
    for rec in sorted_recs[:8]:
        lines.append(f"- {rec.get('id','')} — {rec.get('title','')}")
lines.append("")
lines.append("Query menu:")
if areas:
    lines.append(f"- sdlc-engine context retrieve --area {areas[0]} --kind decision")
else:
    lines.append("- sdlc-engine context retrieve --work-id " + wid)
lines.append("- sdlc-engine context show <id>")
lines.append("- spdd_areaLessons / spdd_workSubgraph MCP tools (when Guide enabled)")
lines.append("- sdlc.sh db query <term> (when sqlite enabled)")

# Hard cap ≤15 lines for digest section body (excluding heading)
body = lines[1:]
if len(body) > 14:
    body = body[:13] + ["…"]
print("\n".join([lines[0]] + body))
PY
)"
fi

cat > "${session_file}" <<EOF
# SDLC-SPDD Agent Session

## Metadata

- Timestamp: ${timestamp}
- Target: ${TARGET}
- Work ID: ${WORK_ID:-none}
- Phase: ${PHASE}
- Jira: ${jira_status:-unknown}
- Active milestone: ${active_milestone:-none}
- Recommended command: ${recommended_command}
- Canvas sync state: ${canvas_sync_state}
- Previous session brief: ${latest_session}

## Workflow State

Local phase + gate tracking (not committed). Refresh with \`${sdlc_sh_hint} next\` or \`/sdlc-spdd-whereami\`.

${workflow_brief_md}

## Framework Orientation

New agents: load these first so you know how to operate within the SDLC-SPDD framework before doing any work.

- Operating model + work rules: the always-on grounding file (.cursor/rules/sdlc-spdd.mdc, .github/copilot-instructions.md, or CLAUDE.md) is loaded on every request.
- How the framework works: ${docs_hint}/three-part-operating-path.md, ${docs_hint}/workflow.md.
- Session + context-loading rules: ${docs_hint}/context-loading-and-scaling.md#bootstrap-and-index-based-loading (bootstrap layers, index catalog, retrieval, capture).
- Resolve phase skills/extensions: ${scripts_hint}/resolve-agent-context.sh --target . --phase ${PHASE}

## Hybrid Operating Model

- SDLC Agents side: use the phase-specific role, load only relevant context, preserve handoffs, and capture learning.
- SPDD side: treat the REASONS Canvas as the governing prompt contract and keep prompt artifacts synchronized with code.

## Artifact Status

| Artifact | Path | Status |
|----------|------|--------|
| Canonical canvas | ${canonical_canvas:-not applicable} | $(status_for "${canonical_canvas}") |

## Roadmap and Milestone Context

| Artifact | Path | Status |
|----------|------|--------|
| Roadmap | ROADMAP.md | $(status_for "${roadmap_file}") |
| Today's session notes | session-notes/$(sdlc_timestamp_day).md | $(status_for "${today_note}") |

Milestone docs:

${milestone_list}

${digest_md}

## Resolved Context

Phase-specific extensions, playbooks, Work ID artifacts, and area-filtered index matches for **${PHASE}** (from resolve-agent-context.sh):

${resolved_context_md}

Refresh after adding extensions, code areas, or `#SkillName` skills:

    ${scripts_hint}/resolve-agent-context.sh --target . --phase ${PHASE}${WORK_ID:+ --work-id ${WORK_ID}}
    ${scripts_hint}/resolve-agent-context.sh --target . --phase ${PHASE} --text "#TDD #java"

$(if [[ "${sqlite_lookup_loaded}" -eq 1 ]]; then printf '%s\n' "${sqlite_section_md}"; fi)

## Git Status

    ${git_status//$'\n'/$'\n'    }

## Resume Prompt

Use this prompt at the start of the new agent session. See ${docs_hint}/session-prompt-standard.md for the full prompt contract.

${resume_prompt_indented}

## Session Notes

Add notes here during the session, then persist them with:

    ${scripts_hint}/capture-session-memory.sh --target . --work-id ${WORK_ID:-<WORK-ID>} --phase ${PHASE} --summary "<summary>" --validation "<validation>" --next "<next command>"
EOF

cp "${session_file}" "${current_file}"

# Index hot session into SQLite when engine is available (#85).
if [[ -n "${WORK_ID}" ]]; then
  python3 -m sdlc_engine --root "${TARGET}" db query \
    --sql "SELECT 1" >/dev/null 2>&1 || true
  python3 - <<PY 2>/dev/null || true
from sdlc_engine.db import LocalIndex
from sdlc_engine.project import Project
idx = LocalIndex(Project("${TARGET}"))
idx.upsert_context_session(
    session_id="${session_name}",
    work_id="${WORK_ID}",
    phase="${PHASE}",
    path=".sdlc/sessions/${session_name}.md",
    summary="hot session brief",
)
PY
fi

rotate_session_briefs() {
  # Keep the newest ${limit} timestamped briefs; move older ones to archive/.
  # Never moves current-session.md.
  local dir="$1"
  local limit="$2"
  local archive_dir="${dir}/archive"
  local -a briefs=()
  local file base count move_count

  [[ "${limit}" =~ ^[0-9]+$ ]] || return 0
  (( limit >= 1 )) || return 0

  shopt -s nullglob
  mapfile -t briefs < <(ls -t "${dir}"/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]T*.md 2>/dev/null || true)
  shopt -u nullglob
  count="${#briefs[@]}"
  if (( count <= limit )); then
    return 0
  fi

  mkdir -p "${archive_dir}"
  move_count=0
  for file in "${briefs[@]:limit}"; do
    base="$(basename "${file}")"
    mv "${file}" "${archive_dir}/${base}"
    move_count=$((move_count + 1))
  done
  if (( move_count > 0 )); then
    echo "Archived ${move_count} older session brief(s) to ${archive_dir}/"
  fi
}

if [[ "${SESSION_ROTATE}" -eq 1 ]]; then
  rotate_session_briefs "${session_dir}" "${SESSION_LIMIT}"
fi

echo "Created session brief:"
echo "  ${session_file}"
echo "Updated current session:"
echo "  ${current_file}"
echo "Recommended command:"
echo "  ${recommended_command}"
