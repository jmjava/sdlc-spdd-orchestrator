#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "${_SCRIPT_DIR}/lib/common.sh" ]]; then
  # shellcheck source=/dev/null
  source "${_SCRIPT_DIR}/lib/common.sh"
  # shellcheck source=/dev/null
  source "${_SCRIPT_DIR}/lib/milestone.sh"
elif [[ -f "${_SCRIPT_DIR}/sdlc-spdd/lib/common.sh" ]]; then
  # shellcheck source=/dev/null
  source "${_SCRIPT_DIR}/sdlc-spdd/lib/common.sh"
  # shellcheck source=/dev/null
  source "${_SCRIPT_DIR}/sdlc-spdd/lib/milestone.sh"
else
  echo "Error: cannot locate scripts/lib (run from orchestrator or installed sdlc-spdd/scripts/)." >&2
  exit 1
fi

usage() {
  cat <<'EOF'
Usage: validate-requirements-format.sh [--target <path>] [--require-frontmatter] [--strict]

Validate milestone requirements for Jira-compatible format and Work ID links.

Checks (format-only; does not call the Jira API):
  - Requirement files under requirements/milestones/ (flat and milestone-N/)
  - Optional YAML frontmatter fields (jira_key format, work_id)
  - ## Jira Key format when present
  - blocks / depends_on / related Work IDs resolve to existing requirement files
  - Each milestone-N/ directory has a definition file; warns if _milestone.yml missing

Options:
  --target <path>           Target project (default: .)
  --require-frontmatter     Fail when a requirement lacks YAML frontmatter
  --strict                  Treat warnings as failures
  --help                    Show this help

Exit 0 when no errors (and no warnings under --strict).
EOF
}

TARGET="."
REQUIRE_FRONTMATTER=0
STRICT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --require-frontmatter)
      REQUIRE_FRONTMATTER=1
      shift
      ;;
    --strict)
      STRICT=1
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

TARGET="$(cd "${TARGET}" && pwd)"
errors=0
warnings=0

err() {
  echo "ERROR: $*" >&2
  errors=$((errors + 1))
}

warn() {
  echo "WARN: $*" >&2
  warnings=$((warnings + 1))
}

# Collect requirement markdown paths (skip README and MILESTONE definitions).
collect_requirement_files() {
  local root="${TARGET}/requirements/milestones"
  local f base
  [[ -d "${root}" ]] || return 0
  shopt -s nullglob
  for f in "${root}"/*.md "${root}"/milestone-*/*.md; do
    [[ -f "${f}" ]] || continue
    base="$(basename "${f}" .md)"
    case "${base}" in
      README|readme) continue ;;
      MILESTONE-*|milestone-*) continue ;;
    esac
    printf '%s\n' "${f}"
  done
  shopt -u nullglob
}

requirement_exists() {
  local work_id="$1"
  resolve_requirement_path "${TARGET}" "${work_id}" absolute >/dev/null 2>&1
}

is_valid_jira_key() {
  local key="$1"
  [[ "${key}" =~ ^[A-Z][A-Z0-9]+-[0-9]+$ ]]
}

extract_frontmatter() {
  local file="$1"
  awk '
    NR==1 && /^---[[:space:]]*$/ { in_fm=1; next }
    in_fm && /^---[[:space:]]*$/ { exit }
    in_fm { print }
  ' "${file}"
}

has_frontmatter() {
  local file="$1"
  head -n 1 "${file}" | grep -q '^---[[:space:]]*$'
}

frontmatter_scalar() {
  local fm="$1"
  local key="$2"
  printf '%s\n' "${fm}" | awk -v k="${key}" '
    $0 ~ "^" k ":[[:space:]]*" {
      sub("^[^:]+:[[:space:]]*", "")
      gsub(/^["[:space:]]+|["[:space:]]+$/, "")
      print
      exit
    }
  '
}

frontmatter_list_items() {
  local fm="$1"
  local key="$2"
  printf '%s\n' "${fm}" | awk -v k="${key}" '
    $0 ~ "^" k ":[[:space:]]*\\[\\]" { exit }
    $0 ~ "^" k ":[[:space:]]*$" { in_list=1; next }
    $0 ~ "^" k ":[[:space:]]*\\[" {
      line=$0
      sub("^[^:]+:[[:space:]]*\\[", "", line)
      sub("\\].*$", "", line)
      n=split(line, a, ",")
      for (i=1;i<=n;i++) {
        gsub(/^[[:space:]]*["]+|["]+[[:space:]]*$/, "", a[i])
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", a[i])
        if (a[i] != "") print a[i]
      }
      exit
    }
    in_list && /^[a-z_]+:/ { exit }
    in_list && /^[[:space:]]*-[[:space:]]*/ {
      sub(/^[[:space:]]*-[[:space:]]*/, "")
      gsub(/^["[:space:]]+|["[:space:]]+$/, "")
      if ($0 != "") print
    }
  '
}

jira_key_from_section() {
  local file="$1"
  awk '
    /^## Jira/ { in_jira=1; next }
    /^## / { if (in_jira) exit }
    in_jira && /^[[:space:]]*(-[[:space:]]+)?[Kk]ey:[[:space:]]*/ {
      sub(/^[[:space:]]*(-[[:space:]]+)?[Kk]ey:[[:space:]]*/, "")
      gsub(/^[[:space:]]+|[[:space:]]+$/, "")
      print
      exit
    }
  ' "${file}"
}

validate_work_id_refs() {
  local file="$1"
  local fm="$2"
  local key ref
  for key in blocks depends_on related; do
    while IFS= read -r ref; do
      [[ -n "${ref}" ]] || continue
      if ! requirement_exists "${ref}"; then
        err "${file#${TARGET}/}: ${key} references missing Work ID '${ref}'"
      fi
    done < <(frontmatter_list_items "${fm}" "${key}")
  done
}

echo "Validating requirements format under ${TARGET}/requirements/milestones"
echo

mapfile -t req_files < <(collect_requirement_files | sort -u)

if ((${#req_files[@]} == 0)); then
  warn "No Work ID requirement files found under requirements/milestones/"
fi

for file in "${req_files[@]}"; do
  rel="${file#${TARGET}/}"
  base="$(basename "${file}" .md)"
  fm=""
  if has_frontmatter "${file}"; then
    fm="$(extract_frontmatter "${file}")"
    work_id="$(frontmatter_scalar "${fm}" work_id)"
    if [[ -n "${work_id}" && "${work_id}" != "${base}" ]]; then
      err "${rel}: work_id '${work_id}' does not match filename '${base}'"
    fi
    jira_key="$(frontmatter_scalar "${fm}" jira_key)"
    if [[ -n "${jira_key}" && "${jira_key}" != "TBD" ]]; then
      if ! is_valid_jira_key "${jira_key}"; then
        err "${rel}: invalid jira_key '${jira_key}' (expected PROJECT-123)"
      fi
    fi
    validate_work_id_refs "${file}" "${fm}"
  else
    if [[ "${REQUIRE_FRONTMATTER}" -eq 1 ]]; then
      err "${rel}: missing YAML frontmatter"
    else
      warn "${rel}: no YAML frontmatter (optional; see docs/jira-compatible-requirements-format.md)"
    fi
  fi

  section_key="$(jira_key_from_section "${file}")"
  if [[ -n "${section_key}" && "${section_key}" != "TBD" && "${section_key}" != "TODO" ]]; then
    if ! is_valid_jira_key "${section_key}"; then
      err "${rel}: ## Jira Key '${section_key}' is not PROJECT-123 format"
    fi
  fi

  if [[ -n "${jira_key:-}" && -n "${section_key}" && "${jira_key}" != "TBD" && "${section_key}" != "TBD" ]]; then
    if [[ "${jira_key}" != "${section_key}" ]]; then
      warn "${rel}: jira_key frontmatter (${jira_key}) != ## Jira Key (${section_key})"
    fi
  fi
  unset jira_key section_key work_id
done

# Milestone subdirectory structure
shopt -s nullglob
for dir in "${TARGET}"/requirements/milestones/milestone-*/; do
  [[ -d "${dir}" ]] || continue
  num="$(_milestone_number_from_path "${dir}" || true)"
  rel="${dir#${TARGET}/}"
  rel="${rel%/}"
  if [[ ! -f "${dir}_milestone.yml" ]]; then
    warn "${rel}: missing _milestone.yml"
  fi
  if [[ ! -f "${dir}MILESTONE-${num}.md" && ! -f "${dir}README.md" && ! -f "${dir}milestone-${num}.md" ]]; then
    err "${rel}: missing milestone definition (MILESTONE-${num}.md or README.md)"
  fi
done
shopt -u nullglob

echo
echo "Summary: ${errors} error(s), ${warnings} warning(s)"

if (( errors > 0 )); then
  exit 1
fi
if [[ "${STRICT}" -eq 1 && "${warnings}" -gt 0 ]]; then
  exit 1
fi
exit 0
