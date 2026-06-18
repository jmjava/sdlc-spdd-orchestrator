#!/usr/bin/env bash
set -euo pipefail

# Resolve SDLC Agents-style context for progressive disclosure:
#   - #SkillName / !SkillName directives in prompt text
#   - Phase-specific extension folders (_all-agents + *-agent)
#   - Static playbooks for the active phase
#   - context-index.md rows filtered by --work-id / --areas (dynamic memory)
#
# Prints paths relative to --target (one per line with --format paths).

usage() {
  cat <<'EOF'
Usage: resolve-agent-context.sh [options]

Resolve skills, phase extensions, and indexed context for progressive loading.
Combines SDLC Agents static resolution with area-keyed context-index rows.

Options:
  --target <path>     Target project (default: .)
  --phase <phase>     SDLC phase: init, analysis, plan, architect, code,
                      api-test, review, prompt-update, retro, sync
  --work-id <id>      Load code areas from analysis + Work ID artifacts; filter
                      context-index.md by those areas
  --areas <list>      Comma-separated code areas (overrides/supplements work-id)
  --index-limit <n>   Max context-index rows to resolve (default: 12)
  --text <string>     Prompt text containing #SkillName and !SkillName tokens
  --text-file <path>  Read prompt text from a file
  --format <fmt>      Output: paths (default), markdown, json
  --list-skills       List discoverable skill names (no resolution)
  --dry-run           Same as default; included for symmetry with other scripts
  -h, --help          Show this help

Examples:
  ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase code --work-id FEAT-001
  ./scripts/sdlc-spdd/resolve-agent-context.sh --phase code --areas src/billing,com.acme.billing
  ./scripts/sdlc-spdd/resolve-agent-context.sh --text "Implement auth #TDD #java !Kafka"
  ./scripts/sdlc-spdd/resolve-agent-context.sh --list-skills
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

TARGET="$(cd "${TARGET}" && pwd)"

if [[ -n "${TEXT_FILE}" ]]; then
  if [[ ! -f "${TEXT_FILE}" ]]; then
    echo "Text file not found: ${TEXT_FILE}" >&2
    exit 1
  fi
  TEXT="$(cat "${TEXT_FILE}")"
fi

normalize_area() {
  local a="$1"
  a="$(printf '%s' "${a}" | tr '[:upper:]' '[:lower:]')"
  a="${a#"${a%%[![:space:]]*}"}"
  a="${a%"${a##*[![:space:]]}"}"
  a="$(printf '%s' "${a}" | tr -s '/')"
  a="${a%/}"
  printf '%s' "${a}"
}

parse_section_bullets() {
  local file="$1"
  local section="$2"
  [[ -f "${file}" ]] || return 0
  awk -v section="${section}" '
    BEGIN { in_section = 0 }
    $0 ~ "^##[[:space:]]+" section "[[:space:]]*$" { in_section = 1; next }
    in_section && /^## / { exit }
    in_section && /^-[[:space:]]+/ {
      line = $0
      sub(/^-[[:space:]]+/, "", line)
      sub(/[[:space:]]+\(.+\)$/, "", line)
      gsub(/`/, "", line)
      if (length(line) > 0) print line
    }
  ' "${file}"
}

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
  local candidate
  for candidate in \
    "${TARGET}/spdd/analysis/${wid}-analysis.md" \
    "${TARGET}/agent-context/features/${wid}/analysis-context.md"; do
    while IFS= read -r _ar; do
      register_area "${_ar}"
    done < <(parse_section_bullets "${candidate}" "Code Areas")
  done
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

declare -a index_rows=()

resolve_index_source_path() {
  local source="$1"
  source="${source#"${source%%[![:space:]]*}"}"
  source="${source%"${source##*[![:space:]]}"}"
  [[ -z "${source}" ]] && return 1
  if [[ "${source}" == */* ]]; then
    if [[ -f "${TARGET}/${source}" ]]; then
      add_path "${TARGET}/${source}"
      return 0
    fi
    return 1
  fi
  local candidate="${TARGET}/agent-context/memory/${source}"
  if [[ -f "${candidate}" ]]; then
    add_path "${candidate}"
    return 0
  fi
  candidate="${TARGET}/${source}"
  if [[ -f "${candidate}" ]]; then
    add_path "${candidate}"
    return 0
  fi
  return 1
}

resolve_index_entry_path() {
  local entry="$1"
  local source="$2"
  entry="${entry#"${entry%%[![:space:]]*}"}"
  entry="${entry%"${entry##*[![:space:]]}"}"
  [[ -z "${entry}" ]] && return 0
  if [[ "${entry}" == */* ]]; then
    add_path "${TARGET}/${entry}"
    return 0
  fi
  resolve_index_source_path "${source}" || true
}

collect_context_index_matches() {
  local index_file="${TARGET}/agent-context/memory/context-index.md"
  [[ -f "${index_file}" ]] || return 0
  ((${#filter_areas[@]} > 0)) || return 0

  local areas_csv=""
  local _a
  for _a in "${filter_areas[@]}"; do
    areas_csv+="${_a},"
  done
  areas_csv="${areas_csv%,}"

  while IFS= read -r row; do
    [[ -n "${row}" ]] || continue
    index_rows+=("${row}")
    local entry source
    entry="$(printf '%s' "${row}" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $8); print $8}')"
    source="$(printf '%s' "${row}" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $7); print $7}')"
    resolve_index_entry_path "${entry}" "${source}"
  done < <(
    awk -F'|' -v areas="${areas_csv}" -v limit="${INDEX_LIMIT}" '
      BEGIN {
        n = split(areas, want, ",")
        for (i = 1; i <= n; i++) area_set[want[i]] = 1
        count = 0
      }
      /^\| / && $0 !~ /^\| Area/ {
        if (count >= limit) exit
        a = $2
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", a)
        if (a in area_set) {
          print
          count++
        }
      }
    ' "${index_file}"
  )
}

add_work_id_artifacts() {
  local wid="$1"
  add_path "${TARGET}/spdd/canvas/${wid}.md"
  add_path "${TARGET}/spdd/analysis/${wid}-analysis.md"
  add_path "${TARGET}/agent-context/features/${wid}/progress-log.md"
  add_path "${TARGET}/agent-context/features/${wid}/analysis-context.md"
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

rel_path() {
  local abs="$1"
  if [[ "${abs}" == "${TARGET}/"* ]]; then
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
  local base="${TARGET}/agent-context"
  local candidate
  for candidate in \
    "${base}/extensions/skills/${skill}.md" \
    "${base}/extensions/skills/${lower}.md" \
    "${base}/playbooks/${lower}-playbook.md" \
    "${base}/playbooks/${skill}-playbook.md" \
    "${base}/playbooks/${lower}.md" \
    "${base}/playbooks/${skill}.md"; do
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
  local f base name
  for f in "${TARGET}"/agent-context/extensions/skills/*.md; do
    base="$(basename "${f}" .md)"
    names["${base}"]=1
  done
  for f in "${TARGET}"/agent-context/playbooks/*-playbook.md; do
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

phase_static_playbooks() {
  local phase="$1"
  local scoped="${2:-0}"
  case "${phase}" in
    code)
      add_path "${TARGET}/agent-context/playbooks/java-feature-playbook.md"
      add_path "${TARGET}/agent-context/playbooks/bugfix-playbook.md"
      add_path "${TARGET}/agent-context/playbooks/refactor-playbook.md"
      if (( scoped == 0 )); then
        add_path "${TARGET}/agent-context/memory/known-pitfalls.md"
      fi
      ;;
    api-test)
      add_path "${TARGET}/agent-context/harness/quality-gates.md"
      ;;
    review)
      add_path "${TARGET}/agent-context/playbooks/pr-review-playbook.md"
      add_path "${TARGET}/agent-context/harness/quality-gates.md"
      ;;
    retro|sync)
      add_path "${TARGET}/agent-context/playbooks/session-handoff-playbook.md"
      if (( scoped == 0 )); then
        add_path "${TARGET}/agent-context/memory/reusable-patterns.md"
      fi
      ;;
    architect)
      add_path "${TARGET}/agent-context/harness/validation-rules.md"
      if (( scoped == 0 )); then
        add_path "${TARGET}/agent-context/memory/architecture-decisions.md"
      fi
      ;;
    analysis)
      add_path "${TARGET}/agent-context/memory/domain-index.md"
      add_path "${TARGET}/agent-context/memory/code-areas.md"
      add_path "${TARGET}/agent-context/memory/context-index.md"
      ;;
    plan)
      add_path "${TARGET}/ROADMAP.md"
      ;;
  esac
}

if [[ "${LIST_SKILLS}" -eq 1 ]]; then
  list_discoverable_skills
  exit 0
fi

ext_base="${TARGET}/agent-context/extensions"
if [[ -n "${PHASE}" ]]; then
  collect_extension_md "${ext_base}/_all-agents"
  agent_dir="$(phase_agent_dir "${PHASE}")"
  if [[ -n "${agent_dir}" ]]; then
    collect_extension_md "${ext_base}/${agent_dir}"
  fi
  phase_static_playbooks "${PHASE}" "${area_scoped}"
fi

if [[ -n "${WORK_ID}" ]]; then
  add_work_id_artifacts "${WORK_ID}"
fi

if (( area_scoped == 1 )); then
  collect_context_index_matches
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
  local p kind row
  if ((${#resolved_paths[@]} == 0 && ${#index_rows[@]} == 0)); then
    echo "No resolved context files."
    return 0
  fi
  if ((${#resolved_paths[@]} > 0)); then
    echo "### Static and phase files"
    echo ""
    echo "| Kind | Path |"
    echo "|------|------|"
    for p in "${resolved_paths[@]}"; do
      kind="file"
      if [[ "${p}" == agent-context/extensions/* ]]; then
        kind="extension"
      elif [[ "${p}" == agent-context/playbooks/* ]]; then
        kind="playbook"
      elif [[ "${p}" == agent-context/memory/* ]]; then
        kind="memory"
      elif [[ "${p}" == agent-context/harness/* ]]; then
        kind="harness"
      elif [[ "${p}" == spdd/* ]]; then
        kind="spdd"
      fi
      echo "| ${kind} | ${p} |"
    done
  fi
  if ((${#index_rows[@]} > 0)); then
    echo ""
    echo "### Indexed context (newest first, area-filtered)"
    echo ""
    echo "Read the **Entry** column — session/analysis paths load directly; decision/pitfall/pattern rows point at anchors in **Source**."
    echo ""
    echo "| Area | Kind | Work ID | Entry | Source |"
    echo "|------|------|---------|-------|--------|"
    for row in "${index_rows[@]}"; do
      printf '%s\n' "${row}" | awk -F'|' '{
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", $4)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", $8)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", $7)
        print "| " $2 " | " $3 " | " $4 " | " $8 " | " $7 " |"
      }'
    done
  fi
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

emit_json() {
  printf '{"phase":"%s","workId":"%s","areas":[' "${PHASE}" "${WORK_ID}"
  local first=1 a
  for a in "${filter_areas[@]}"; do
    [[ ${first} -eq 1 ]] || printf ','
    first=0
    printf '"%s"' "${a}"
  done
  printf '],"includes":['
  first=1
  local s
  for s in "${skill_includes[@]}"; do
    [[ ${first} -eq 1 ]] || printf ','
    first=0
    printf '"%s"' "${s}"
  done
  printf '],"excludes":['
  first=1
  for s in "${skill_excludes[@]}"; do
    [[ ${first} -eq 1 ]] || printf ','
    first=0
    printf '"%s"' "${s}"
  done
  printf '],"paths":['
  first=1
  local p
  for p in "${resolved_paths[@]}"; do
    [[ ${first} -eq 1 ]] || printf ','
    first=0
    printf '"%s"' "${p}"
  done
  printf '],"indexRows":['
  first=1
  local row esc
  for row in "${index_rows[@]}"; do
    [[ ${first} -eq 1 ]] || printf ','
    first=0
    esc="${row//\\/\\\\}"
    esc="${esc//\"/\\\"}"
    printf '"%s"' "${esc}"
  done
  printf ']}\n'
}

case "${FORMAT}" in
  paths) emit_paths ;;
  markdown) emit_markdown ;;
  json) emit_json ;;
esac
