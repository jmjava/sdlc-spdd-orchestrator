#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: index-spdd-analysis.sh --work-id <WORK-ID> [options]

Index a Fowler SPDD analysis artifact into decision-memory indexes:
  - agent-context/memory/domain-index.md (keyword -> area + artifact)
  - agent-context/memory/context-index.md (Kind: analysis, by code area)
  - agent-context/memory/code-areas.md (append new code areas)

Run after /sdlc-spdd-analysis writes spdd/analysis/<WORK-ID>-analysis.md.

Options:
  --target <path>   Target project path (default: .)
  --work-id <id>    Work ID (required)
  --phase <phase>   Phase label for index rows (default: analysis)
  --dry-run         Print actions without writing files
  --help            Print this help message

Example:
  ./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id FEAT-001-billing
EOF
}

TARGET="."
WORK_ID=""
PHASE="analysis"
DRY_RUN=0

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
    --dry-run)
      DRY_RUN=1
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

if [[ -z "${WORK_ID}" ]]; then
  echo "Error: --work-id is required" >&2
  usage >&2
  exit 1
fi

TARGET="$(cd "${TARGET}" && pwd)"
timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
memory_dir="${TARGET}/agent-context/memory"
analysis_file="${TARGET}/spdd/analysis/${WORK_ID}-analysis.md"
feature_analysis="${TARGET}/agent-context/features/${WORK_ID}/analysis-context.md"
domain_index="${memory_dir}/domain-index.md"
context_index="${memory_dir}/context-index.md"
code_areas="${memory_dir}/code-areas.md"
entry_rel="spdd/analysis/${WORK_ID}-analysis.md"

if [[ ! -f "${analysis_file}" ]]; then
  echo "Analysis file not found: ${analysis_file}" >&2
  exit 1
fi

normalize_token() {
  local t="$1"
  t="$(printf '%s' "${t}" | tr '[:upper:]' '[:lower:]')"
  t="${t#"${t%%[![:space:]]*}"}"
  t="${t%"${t##*[![:space:]]}"}"
  t="${t%%[.,;:)]}"
  t="${t##[.,;(]}"
  printf '%s' "${t}"
}

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

declare -a keywords=()
declare -a areas=()
while IFS= read -r _kw; do
  _kw="$(normalize_token "${_kw}")"
  [[ -n "${_kw}" ]] && keywords+=("${_kw}")
done < <(parse_section_bullets "${analysis_file}" "Domain Keywords")

while IFS= read -r _ar; do
  _ar="$(normalize_area "${_ar}")"
  [[ -n "${_ar}" ]] && areas+=("${_ar}")
done < <(parse_section_bullets "${analysis_file}" "Code Areas")

if ((${#keywords[@]} == 0 && ${#areas[@]} == 0)); then
  echo "No Domain Keywords or Code Areas found in ${analysis_file}" >&2
  echo "Ensure the analysis document has ## Domain Keywords and ## Code Areas sections." >&2
  exit 1
fi

declare -A known_areas=()
if [[ -f "${code_areas}" ]]; then
  while IFS= read -r _line; do
    [[ "${_line}" =~ ^-\ (.+)$ ]] || continue
    _canon="${BASH_REMATCH[1]}"
    known_areas["$(normalize_area "${_canon}")"]="${_canon}"
  done < "${code_areas}"
fi

new_areas=()
for _a in "${areas[@]}"; do
  _norm="$(normalize_area "${_a}")"
  if [[ -z "${known_areas[${_norm}]:-}" ]]; then
    known_areas["${_norm}"]="${_a}"
    new_areas+=("${_a}")
  fi
done

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "[dry-run] keywords: ${keywords[*]:-none}"
  echo "[dry-run] areas: ${areas[*]:-none}"
  echo "[dry-run] would update ${domain_index}, ${context_index}, ${code_areas}"
  exit 0
fi

mkdir -p "${memory_dir}" "$(dirname "${analysis_file}")"

if ((${#new_areas[@]} > 0)); then
  if [[ ! -f "${code_areas}" ]]; then
    printf '# Code Areas\n\nCanonical code-area categories. Populated from session capture and analysis indexing.\n\n' > "${code_areas}"
  fi
  for _a in "${new_areas[@]}"; do
    printf -- '- %s\n' "${_a}" >> "${code_areas}"
  done
fi

domain_header="$(cat <<'DOM'
# Domain Index

Maps Fowler SPDD **domain keywords** to code areas and governed artifacts. Filter
by Keyword before scanning code or loading prior analysis/canvas context. Newest
first within each keyword group.

| Keyword | Area | Kind | Work ID | Timestamp | Entry |
|---------|------|------|---------|-----------|-------|
DOM
)"

domain_rows=""
for _kw in "${keywords[@]}"; do
  if ((${#areas[@]} == 0)); then
    domain_rows+="| ${_kw} | - | analysis | ${WORK_ID} | ${timestamp} | ${entry_rel} |"$'\n'
  else
    for _a in "${areas[@]}"; do
      domain_rows+="| ${_kw} | ${_a} | analysis | ${WORK_ID} | ${timestamp} | ${entry_rel} |"$'\n'
    done
  fi
done
domain_rows="${domain_rows%$'\n'}"

existing_domain=""
if [[ -f "${domain_index}" ]]; then
  existing_domain="$(awk '/^\| / && $0 !~ /^\| Keyword/' "${domain_index}")"
fi
{
  printf '%s\n' "${domain_header}"
  printf '%s\n' "${domain_rows}"
  if [[ -n "${existing_domain}" ]]; then
    printf '%s\n' "${existing_domain}"
  fi
} > "${domain_index}"

context_header="$(cat <<'CTX'
# Context Index

Maps code areas to indexed project context. Filter by Area to find prior sessions,
analysis artifacts, architecture decisions, known pitfalls, and reusable patterns
for the code you are about to touch — across any Work ID or date. Newest first.

| Area | Kind | Work ID | Phase | Timestamp | Source | Entry |
|------|------|---------|-------|-----------|--------|-------|
CTX
)"

context_rows=""
if ((${#areas[@]} == 0)); then
  context_rows+="| - | analysis | ${WORK_ID} | ${PHASE} | ${timestamp} | analysis | ${entry_rel} |"$'\n'
else
  for _a in "${areas[@]}"; do
    context_rows+="| ${_a} | analysis | ${WORK_ID} | ${PHASE} | ${timestamp} | analysis | ${entry_rel} |"$'\n'
  done
fi
context_rows="${context_rows%$'\n'}"

existing_context=""
if [[ -f "${context_index}" ]]; then
  existing_context="$(awk '/^\| / && $0 !~ /^\| Area/' "${context_index}")"
fi
{
  printf '%s\n' "${context_header}"
  printf '%s\n' "${context_rows}"
  if [[ -n "${existing_context}" ]]; then
    printf '%s\n' "${existing_context}"
  fi
} > "${context_index}"

if [[ ! -f "${feature_analysis}" ]] && [[ -f "${analysis_file}" ]]; then
  mkdir -p "$(dirname "${feature_analysis}")"
  cp "${analysis_file}" "${feature_analysis}"
fi

echo "Indexed analysis for ${WORK_ID}:"
echo "  keywords (${#keywords[@]}): ${keywords[*]:-none}"
echo "  code areas (${#areas[@]}): ${areas[*]:-none}"
echo "  updated: ${domain_index}, ${context_index}"
if ((${#new_areas[@]} > 0)); then
  echo "  new code areas: ${new_areas[*]}"
fi
