#!/usr/bin/env bash
set -euo pipefail

# Resolve SDLC Agents-style context for progressive disclosure:
#   - #SkillName / !SkillName directives in prompt text
#   - Phase-specific extension folders (_all-agents + *-agent)
#   - Static playbooks linked from phase-index.md for the active phase
#
# Prints paths relative to --target (one per line with --format paths).

usage() {
  cat <<'EOF'
Usage: resolve-agent-context.sh [options]

Resolve skills and phase extensions for SDLC Agents-style progressive loading.
Agents and session scripts use this to list only the files to load — not whole
directories.

Options:
  --target <path>     Target project (default: .)
  --phase <phase>     SDLC phase: init, analysis, plan, architect, code,
                      api-test, review, prompt-update, retro, sync
  --text <string>     Prompt text containing #SkillName and !SkillName tokens
  --text-file <path>  Read prompt text from a file
  --format <fmt>      Output: paths (default), markdown, json
  --list-skills       List discoverable skill names (no resolution)
  --dry-run           Same as default; included for symmetry with other scripts
  -h, --help          Show this help

Examples:
  ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase code
  ./scripts/sdlc-spdd/resolve-agent-context.sh --text "Implement auth #TDD #java !Kafka"
  ./scripts/sdlc-spdd/resolve-agent-context.sh --phase architect --text "#security"
  ./scripts/sdlc-spdd/resolve-agent-context.sh --list-skills
EOF
}

TARGET="."
PHASE=""
TEXT=""
TEXT_FILE=""
FORMAT="paths"
LIST_SKILLS=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --phase) PHASE="${2:-}"; shift 2 ;;
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
  case "${phase}" in
    code)
      add_path "${TARGET}/agent-context/playbooks/java-feature-playbook.md"
      add_path "${TARGET}/agent-context/playbooks/bugfix-playbook.md"
      add_path "${TARGET}/agent-context/playbooks/refactor-playbook.md"
      add_path "${TARGET}/agent-context/memory/known-pitfalls.md"
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
      add_path "${TARGET}/agent-context/memory/reusable-patterns.md"
      ;;
    architect)
      add_path "${TARGET}/agent-context/harness/validation-rules.md"
      add_path "${TARGET}/agent-context/memory/architecture-decisions.md"
      ;;
    analysis)
      add_path "${TARGET}/agent-context/memory/domain-index.md"
      add_path "${TARGET}/agent-context/memory/code-areas.md"
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
  phase_static_playbooks "${PHASE}"
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
  if ((${#resolved_paths[@]} == 0)); then
    echo "No resolved context files."
    return 0
  fi
  echo "| Kind | Path |"
  echo "|------|------|"
  local p kind
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
    fi
    echo "| ${kind} | ${p} |"
  done
  if ((${#skill_includes[@]} > 0)); then
    echo ""
    echo "Skills requested: ${skill_includes[*]}"
  fi
  if ((${#skill_excludes[@]} > 0)); then
    echo "Skills excluded: ${skill_excludes[*]}"
  fi
}

emit_json() {
  printf '{"phase":"%s","includes":[' "${PHASE}"
  local first=1 s
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
  printf ']}\n'
}

case "${FORMAT}" in
  paths) emit_paths ;;
  markdown) emit_markdown ;;
  json) emit_json ;;
esac
