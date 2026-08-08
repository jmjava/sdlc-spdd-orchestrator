#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/areas.sh"

# Resolve SDLC Agents-style context for progressive disclosure:
#   - #SkillName / !SkillName directives in prompt text
#   - Phase-specific extension folders (_all-agents + *-agent)
#   - Work ID ledger progress excerpt (.sdlc/resolved/progress-<ID>.md)
#
# Prints paths relative to --target (one per line with --format paths).

usage() {
  cat <<'EOF'
Usage: resolve-agent-context.sh [options]

Resolve skills, phase extensions, and Work ID context for progressive loading.
Combines SDLC Agents static resolution with a ledger progress excerpt (storage
v3): matching lesson records are summarized into .sdlc/resolved/progress-<ID>.md.

Options:
  --target <path>     Target project (default: .)
  --phase <phase>     SDLC phase: init, analysis, plan, architect, code,
                      api-test, review, prompt-update, retro, sync
  --work-id <id>      Load code areas from analysis + Work ID artifacts; scope
                      the ledger progress excerpt by those areas
  --areas <list>      Comma-separated code areas (overrides/supplements work-id)
  --index-limit <n>   Ignored (legacy; kept for CLI compatibility)
  --text <string>     Prompt text containing #SkillName and !SkillName tokens
  --text-file <path>  Read prompt text from a file
  --format <fmt>      Output: paths (default), markdown, json
  --list-skills       List discoverable skill names (no resolution)
  --dry-run           Same as default; included for symmetry with other scripts
  -h, --help          Show this help

Examples:
  ./sdlc-spdd/scripts/resolve-agent-context.sh --target . --phase code --work-id FEAT-001
  ./sdlc-spdd/scripts/resolve-agent-context.sh --phase code --areas src/billing,com.acme.billing
  ./sdlc-spdd/scripts/resolve-agent-context.sh --text "Implement auth #TDD #java !Kafka"
  ./sdlc-spdd/scripts/resolve-agent-context.sh --list-skills
EOF
}

TARGET="."
PHASE=""
WORK_ID=""
AREAS_ARG=""
TEXT=""
TEXT_FILE=""
FORMAT="paths"
INDEX_LIMIT=12
LIST_SKILLS=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --phase) PHASE="${2:-}"; shift 2 ;;
    --work-id) WORK_ID="${2:-}"; shift 2 ;;
    --areas) AREAS_ARG="${2:-}"; shift 2 ;;
    --index-limit) INDEX_LIMIT="${2:-}"; shift 2 ;;
    --text) TEXT="${2:-}"; shift 2 ;;
    --text-file) TEXT_FILE="${2:-}"; shift 2 ;;
    --format) FORMAT="${2:-}"; shift 2 ;;
    --list-skills) LIST_SKILLS=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "${FORMAT}" in
  paths|markdown|json) ;;
  *)
    echo "Invalid --format '${FORMAT}'. Use paths, markdown, or json." >&2
    exit 2
    ;;
esac

if [[ -n "${PHASE}" ]]; then
  case "${PHASE}" in
    init|analysis|plan|architect|code|api-test|review|prompt-update|retro|sync) ;;
    *)
      echo "Unsupported phase: ${PHASE}" >&2
      exit 1
      ;;
  esac
fi

TARGET="$(sdlc_resolve_target "${TARGET}")"
FRAMEWORK_HOME="$(sdlc_home "${TARGET}")"
export SDLC_ROOT="${TARGET}"

if [[ -n "${TEXT_FILE}" ]]; then
  if [[ ! -f "${TEXT_FILE}" ]]; then
    echo "Text file not found: ${TEXT_FILE}" >&2
    exit 1
  fi
  TEXT="$(cat "${TEXT_FILE}")"
fi

declare -a filter_areas=()
declare -A filter_area_set=()

register_area() {
  local norm
  norm="$(normalize_area "$1")"
  [[ -z "${norm}" ]] && return 0
  [[ -n "${filter_area_set[${norm}]:-}" ]] && return 0
  filter_area_set["${norm}"]=1
  filter_areas+=("${norm}")
}

collect_areas_from_work_id() {
  local wid="$1"
  local candidate="${FRAMEWORK_HOME}/spdd/analysis/${wid}-analysis.md"
  while IFS= read -r _ar; do
    register_area "${_ar}"
  done < <(parse_section_bullets "${candidate}" "Code Areas")
}

if [[ -n "${WORK_ID}" ]]; then
  collect_areas_from_work_id "${WORK_ID}"
fi

if [[ -n "${AREAS_ARG}" ]]; then
  _item="${AREAS_ARG}"
  while [[ "${_item}" == *","* ]]; do
    _part="${_item%%,*}"
    register_area "${_part}"
    _item="${_item#*,}"
  done
  register_area "${_item}"
fi

area_scoped=0
((${#filter_areas[@]} > 0)) && area_scoped=1

_write_progress_excerpt_from_ledger() {
  local wid="$1"
  local ledger stage excerpt_dir excerpt
  ledger="$(sdlc_ledger "${TARGET}")"
  stage="$(sdlc_stage "${TARGET}")"
  excerpt_dir="$(sdlc_runtime_dir "${TARGET}")/resolved"
  excerpt="${excerpt_dir}/progress-${wid}.md"
  python3 - <<PY
import json
from pathlib import Path

wid = ${wid@Q}
ledger = Path(${ledger@Q})
stage = Path(${stage@Q})
excerpt = Path(${excerpt@Q})

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

rows = {}
for rec in read_jsonl(ledger) + read_jsonl(stage):
    if rec.get("work_id") != wid:
        continue
    rows[rec.get("id", "")] = rec
matches = sorted(rows.values(), key=lambda r: (r.get("ts", ""), r.get("id", "")), reverse=True)
if not matches:
    raise SystemExit(0)
lines = [f"# Progress (ledger): {wid}", ""]
for rec in matches:
    lines.append(f"- {rec.get('id','')} | {rec.get('kind','')} | {rec.get('title','')} | {rec.get('ts','')}")
excerpt.parent.mkdir(parents=True, exist_ok=True)
excerpt.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(str(excerpt))
PY
}

add_work_id_artifacts() {
  local wid="$1"
  add_path "${FRAMEWORK_HOME}/spdd/canvas/${wid}.md"
  add_path "${FRAMEWORK_HOME}/spdd/analysis/${wid}-analysis.md"
  local excerpt
  excerpt="$(_write_progress_excerpt_from_ledger "${wid}" 2>/dev/null || true)"
  if [[ -n "${excerpt}" && -f "${excerpt}" ]]; then
    add_path "${excerpt}"
  fi
}

phase_agent_dir() {
  case "${1:-}" in
    init) printf '%s' "initializer-agent" ;;
    analysis|plan|prompt-update) printf '%s' "planning-agent" ;;
    architect) printf '%s' "architect-agent" ;;
    code|api-test) printf '%s' "coding-agent" ;;
    review) printf '%s' "codereview-agent" ;;
    retro) printf '%s' "retro-agent" ;;
    sync) printf '%s' "curator-agent" ;;
    *) printf '%s' "" ;;
  esac
}

extension_manifest_path() {
  printf '%s' "$(sdlc_extensions_dir "${TARGET}")/manifest.md"
}

manifest_phase_table_usable() {
  local manifest="$1"
  [[ -f "${manifest}" ]] || return 1
  grep -q '^## Phase extensions' "${manifest}" || return 1
  grep -q '^| Folder | Phases |' "${manifest}" || return 1
  return 0
}

manifest_phase_matches() {
  local phases_col="$1"
  local phase="$2"
  phases_col="${phases_col#"${phases_col%%[![:space:]]*}"}"
  phases_col="${phases_col%"${phases_col##*[![:space:]]}"}"
  [[ "${phases_col}" == "*" ]] && return 0
  local part
  IFS=',' read -ra parts <<< "${phases_col}"
  for part in "${parts[@]}"; do
    part="${part#"${part%%[![:space:]]*}"}"
    part="${part%"${part##*[![:space:]]}"}"
    [[ "${part}" == "${phase}" ]] && return 0
  done
  return 1
}

collect_manifest_phase_extensions() {
  local phase="$1"
  local manifest
  manifest="$(extension_manifest_path)"
  manifest_phase_table_usable "${manifest}" || return 1

  declare -A folders=()
  local row folder phases_col
  local collected=0
  while IFS= read -r row; do
    [[ -z "${row}" ]] || continue
    folder="$(printf '%s' "${row}" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); gsub(/`/, "", $2); print $2}')"
    phases_col="$(printf '%s' "${row}" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3}')"
    [[ -z "${folder}" || "${folder}" == "Folder" ]] && continue
    manifest_phase_matches "${phases_col}" "${phase}" || continue
    folders["${folder}"]=1
  done < <(
    awk '
      /^## Phase extensions/ { in_section = 1; next }
      in_section && /^## / { exit }
      in_section && /^\| / && $0 !~ /^\|[- ]+\|/ && $0 !~ /^\| Folder \|/ { print }
    ' "${manifest}"
  )

  if ((${#folders[@]} == 0)); then
    return 1
  fi

  local -a ordered=()
  if [[ -n "${folders[_all-agents]:-}" ]]; then
    ordered+=("_all-agents")
  fi
  local name
  for name in "${!folders[@]}"; do
    [[ "${name}" == "_all-agents" ]] && continue
    ordered+=("${name}")
  done
  IFS=$'\n' ordered_sorted=($(printf '%s\n' "${ordered[@]}" | sort))
  unset IFS

  for name in "${ordered_sorted[@]}"; do
    collect_extension_md "${ext_base}/${name}"
    collected=1
  done
  (( collected == 1 ))
}

collect_convention_phase_extensions() {
  local phase="$1"
  collect_extension_md "${ext_base}/_all-agents"
  local agent_dir
  agent_dir="$(phase_agent_dir "${phase}")"
  if [[ -n "${agent_dir}" ]]; then
    collect_extension_md "${ext_base}/${agent_dir}"
  fi
}

rel_path() {
  local abs="$1"
  if [[ "${abs}" == "${FRAMEWORK_HOME}/"* ]]; then
    printf '%s' "${abs#${FRAMEWORK_HOME}/}"
  elif [[ "${abs}" == "${TARGET}/"* ]]; then
    printf '%s' "${abs#${TARGET}/}"
  else
    printf '%s' "${abs}"
  fi
}

# Dedupe while preserving order.
declare -a resolved_paths=()
declare -A seen_paths=()

add_path() {
  local abs="$1"
  [[ -f "${abs}" ]] || return 0
  local rel
  rel="$(rel_path "${abs}")"
  [[ -n "${seen_paths[${rel}]:-}" ]] && return 0
  seen_paths["${rel}"]=1
  resolved_paths+=("${rel}")
}

collect_extension_md() {
  local dir="$1"
  [[ -d "${dir}" ]] || return 0
  shopt -s nullglob
  local f
  for f in "${dir}"/*.md; do
    [[ "$(basename "${f}")" == "README.md" ]] && continue
    add_path "${f}"
  done
  shopt -u nullglob
}

resolve_skill_file() {
  local skill="$1"
  local lower
  lower="$(printf '%s' "${skill}" | tr '[:upper:]' '[:lower:]')"
  local ext_base play_base
  ext_base="$(sdlc_extensions_dir "${TARGET}")"
  play_base="$(sdlc_playbooks_dir "${TARGET}")"
  local candidate
  for candidate in \
    "${ext_base}/skills/${skill}.md" \
    "${ext_base}/skills/${lower}.md" \
    "${play_base}/${lower}-playbook.md" \
    "${play_base}/${skill}-playbook.md" \
    "${play_base}/${lower}.md" \
    "${play_base}/${skill}.md"; do
    if [[ -f "${candidate}" ]]; then
      add_path "${candidate}"
      return 0
    fi
  done
  return 1
}

declare -a skill_includes=()
declare -a skill_excludes=()
declare -A exclude_set=()

parse_skill_directives() {
  local input="$1"
  local token
  while IFS= read -r token; do
    [[ -n "${token}" ]] || continue
    exclude_set["${token}"]=1
    skill_excludes+=("${token}")
  done < <(printf '%s' "${input}" | grep -oE '![A-Za-z0-9][A-Za-z0-9_-]*' | sed 's/^!//' || true)

  while IFS= read -r token; do
    [[ -n "${token}" ]] || continue
    [[ -n "${exclude_set[${token}]:-}" ]] && continue
    skill_includes+=("${token}")
  done < <(printf '%s' "${input}" | grep -oE '#[A-Za-z0-9][A-Za-z0-9_-]*' | sed 's/^#//' || true)
}

list_discoverable_skills() {
  declare -A names=()
  shopt -s nullglob
  local f base name ext_base play_base
  ext_base="$(sdlc_extensions_dir "${TARGET}")"
  play_base="$(sdlc_playbooks_dir "${TARGET}")"
  for f in "${ext_base}"/skills/*.md; do
    base="$(basename "${f}" .md)"
    names["${base}"]=1
  done
  for f in "${play_base}"/*-playbook.md; do
    base="$(basename "${f}")"
    base="${base%-playbook.md}"
    names["${base}"]=1
  done
  shopt -u nullglob
  local n
  for n in "${!names[@]}"; do
    printf '%s\n' "${n}"
  done | sort -f
}

phase_index_row_matches() {
  local row_phase="$1"
  local active="$2"
  row_phase="${row_phase#"${row_phase%%[![:space:]]*}"}"
  row_phase="${row_phase%"${row_phase##*[![:space:]]}"}"
  [[ "${row_phase}" == "${active}" ]] && return 0
  if [[ "${row_phase}" == *"/"* ]]; then
    local part
    IFS='/' read -ra _parts <<< "${row_phase}"
    for part in "${_parts[@]}"; do
      part="${part#"${part%%[![:space:]]*}"}"
      part="${part%"${part##*[![:space:]]}"}"
      [[ "${part}" == "${active}" ]] && return 0
    done
  fi
  return 1
}

phase_index_path_area_scoped_skip() {
  # Lesson bodies live in the ledger and are retrieved on demand — never
  # bulk-resolved into the context list.
  local rel="$1"
  case "${rel}" in
    spdd/memory/lessons.jsonl|lessons.jsonl) return 0 ;;
  esac
  return 1
}

add_phase_index_glob() {
  local pattern="$1"
  shopt -s nullglob
  local match
  for match in "${FRAMEWORK_HOME}/${pattern}"; do
    if [[ -f "${match}" ]]; then
      add_path "${match}"
    fi
  done
  shopt -u nullglob
}

add_phase_index_directory() {
  local rel_dir="$1"
  local dir="${FRAMEWORK_HOME}/${rel_dir}"
  [[ -d "${dir}" ]] || return 0

  case "${rel_dir}" in
    spdd/tasks|spdd/tasks/)
      if [[ -n "${WORK_ID}" ]]; then
        shopt -s nullglob
        local task
        for task in "${dir}/${WORK_ID}"*.md "${dir}/${WORK_ID}-"*.md; do
          add_path "${task}"
        done
        shopt -u nullglob
      fi
      ;;
    spdd/analysis|spdd/analysis/)
      if [[ -n "${WORK_ID}" ]]; then
        add_path "${FRAMEWORK_HOME}/spdd/analysis/${WORK_ID}-analysis.md"
      fi
      ;;
    requirements/milestones|requirements/milestones/)
      shopt -s nullglob
      local f
      for f in "${dir}"/*.md; do
        add_path "${f}"
      done
      shopt -u nullglob
      ;;
    *)
      shopt -s nullglob
      local f
      for f in "${dir}"/*.md; do
        add_path "${f}"
      done
      shopt -u nullglob
      ;;
  esac
}

add_phase_index_path() {
  local raw="$1"
  local scoped="${2:-0}"
  raw="${raw#"${raw%%[![:space:]]*}"}"
  raw="${raw%"${raw##*[![:space:]]}"}"
  raw="${raw#\`}"
  raw="${raw%\`}"
  [[ -z "${raw}" ]] && return 0

  if (( scoped == 1 )) && phase_index_path_area_scoped_skip "${raw}"; then
    return 0
  fi

  if [[ "${raw}" == *"*"* ]]; then
    add_phase_index_glob "${raw}"
    return 0
  fi

  if [[ "${raw}" == */ ]]; then
    add_phase_index_directory "${raw%/}"
    return 0
  fi

  if [[ "${raw}" == */* && -d "${FRAMEWORK_HOME}/${raw}" ]]; then
    add_phase_index_directory "${raw}"
    return 0
  fi

  add_path "${FRAMEWORK_HOME}/${raw}"
}

load_phase_index_paths() {
  local phase="$1"
  local scoped="${2:-0}"
  local index_file
  index_file="$(sdlc_harness_dir "${TARGET}")/phase-index.md"
  [[ -f "${index_file}" ]] || return 0

  while IFS= read -r row; do
    [[ -n "${row}" ]] || continue
    local row_phase raw_path
    row_phase="$(printf '%s' "${row}" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2}')"
    raw_path="$(printf '%s' "${row}" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3}')"
    phase_index_row_matches "${row_phase}" "${phase}" || continue
    add_phase_index_path "${raw_path}" "${scoped}"
  done < <(awk '/^\| / && $0 !~ /^\| Phase/' "${index_file}")
}

declare -a index_rows=()

if [[ "${LIST_SKILLS}" -eq 1 ]]; then
  list_discoverable_skills
  exit 0
fi

ext_base="$(sdlc_extensions_dir "${TARGET}")"
if [[ -n "${PHASE}" ]]; then
  if ! collect_manifest_phase_extensions "${PHASE}"; then
    collect_convention_phase_extensions "${PHASE}"
  fi
  load_phase_index_paths "${PHASE}" "${area_scoped}"
fi

if [[ -n "${WORK_ID}" ]]; then
  add_work_id_artifacts "${WORK_ID}"
fi

if [[ -n "${TEXT}" ]]; then
  parse_skill_directives "${TEXT}"
  for skill in "${skill_includes[@]}"; do
    resolve_skill_file "${skill}" || true
  done
fi

emit_paths() {
  local p
  for p in "${resolved_paths[@]}"; do
    printf '%s\n' "${p}"
  done
}

emit_markdown() {
  local p kind
  if ((${#resolved_paths[@]} == 0)); then
    echo "No resolved context files."
    return 0
  fi
  echo "### Static and phase files"
  echo ""
  echo "| Kind | Path |"
  echo "|------|------|"
  for p in "${resolved_paths[@]}"; do
    kind="file"
    if [[ "${p}" == */extensions/* || "${p}" == agent-context/extensions/* ]]; then
      kind="extension"
    elif [[ "${p}" == */playbooks/* || "${p}" == agent-context/playbooks/* ]]; then
      kind="playbook"
    elif [[ "${p}" == */harness/* || "${p}" == agent-context/harness/* ]]; then
      kind="harness"
    elif [[ "${p}" == spdd/* || "${p}" == */spdd/* ]]; then
      kind="spdd"
    elif [[ "${p}" == .sdlc/* ]]; then
      kind="resolved"
    fi
    echo "| ${kind} | ${p} |"
  done
  if ((${#filter_areas[@]} > 0)); then
    echo ""
    echo "Code areas: ${filter_areas[*]}"
  fi
  if ((${#skill_includes[@]} > 0)); then
    echo ""
    echo "Skills requested: ${skill_includes[*]}"
  fi
  if ((${#skill_excludes[@]} > 0)); then
    echo "Skills excluded: ${skill_excludes[*]}"
  fi
}

json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '%s' "${s}"
}

emit_json() {
  printf '{"phase":"%s","workId":"%s","areas":[' \
    "$(json_escape "${PHASE}")" "$(json_escape "${WORK_ID}")"
  local first=1 a
  for a in "${filter_areas[@]}"; do
    [[ ${first} -eq 1 ]] || printf ','
    first=0
    printf '"%s"' "$(json_escape "${a}")"
  done
  printf '],"includes":['
  first=1
  local s
  for s in "${skill_includes[@]}"; do
    [[ ${first} -eq 1 ]] || printf ','
    first=0
    printf '"%s"' "$(json_escape "${s}")"
  done
  printf '],"excludes":['
  first=1
  for s in "${skill_excludes[@]}"; do
    [[ ${first} -eq 1 ]] || printf ','
    first=0
    printf '"%s"' "$(json_escape "${s}")"
  done
  printf '],"paths":['
  first=1
  local p
  for p in "${resolved_paths[@]}"; do
    [[ ${first} -eq 1 ]] || printf ','
    first=0
    printf '"%s"' "$(json_escape "${p}")"
  done
  printf '],"indexRows":[]}\n'
}

case "${FORMAT}" in
  paths) emit_paths ;;
  markdown) emit_markdown ;;
  json) emit_json ;;
esac
