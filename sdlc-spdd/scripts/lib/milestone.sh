#!/usr/bin/env bash
# Milestone and milestone-requirement path helpers.
#
# Supported milestone definition locations (both valid):
#   1. Root (legacy):              milestone-N.md
#   2. Subdirectory (preferred):   requirements/milestones/milestone-N/MILESTONE-N.md
#                                  requirements/milestones/milestone-N/README.md
#
# When the same milestone number exists in both places, prefer the subdirectory
# and emit a warning on stderr.

# Collect candidate milestone definition files under TARGET (absolute paths).
# Order: subdirectory MILESTONE-*.md, subdirectory README.md, then root milestone-*.md.
_list_milestone_definition_candidates() {
  local target="$1"
  local dir base file
  shopt -s nullglob
  for dir in "${target}"/requirements/milestones/milestone-*/; do
    [[ -d "${dir}" ]] || continue
    base="$(basename "${dir}")"
    for file in \
      "${dir}MILESTONE-${base#milestone-}.md" \
      "${dir}MILESTONE-${base#milestone-}.MD" \
      "${dir}${base}.md" \
      "${dir}README.md"; do
      if [[ -f "${file}" ]]; then
        printf '%s\n' "${file}"
      fi
    done
  done
  for file in "${target}"/milestone-*.md; do
    [[ -f "${file}" ]] || continue
    printf '%s\n' "${file}"
  done
  shopt -u nullglob
}

# True when path is under requirements/milestones/milestone-N/ (not flat stub).
_is_subdir_milestone_definition() {
  local path="$1"
  [[ "${path}" == */requirements/milestones/milestone-*/* ]]
}

# Extract milestone number from a path or basename (milestone-2.md → 2).
_milestone_number_from_path() {
  local path="$1"
  local base
  base="$(basename "${path}" .md)"
  base="${base%.MD}"
  if [[ "${base}" =~ ^[Mm][Ii][Ll][Ee][Ss][Tt][Oo][Nn][Ee]-([0-9]+)$ ]]; then
    printf '%s' "${BASH_REMATCH[1]}"
    return 0
  fi
  if [[ "${path}" =~ /milestone-([0-9]+)/ ]]; then
    printf '%s' "${BASH_REMATCH[1]}"
    return 0
  fi
  return 1
}

# Prefer subdirectory definition over root when both exist for the same number.
_prefer_milestone_path() {
  local existing="$1"
  local candidate="$2"
  if _is_subdir_milestone_definition "${candidate}" && \
     ! _is_subdir_milestone_definition "${existing}"; then
    printf '%s' "${candidate}"
    return 0
  fi
  printf '%s' "${existing}"
}

# list_milestone_files TARGET [mode]
#   mode absolute|relative — print one path per line (unique by milestone number;
#   subdirectory preferred over root).
list_milestone_files() {
  local target="$1"
  local mode="${2:-relative}"
  local file num chosen
  local -A by_num=()
  local -A warned=()
  local -a nums=()

  while IFS= read -r file; do
    [[ -n "${file}" ]] || continue
    num="$(_milestone_number_from_path "${file}" || true)"
    [[ -n "${num}" ]] || continue
    if [[ -z "${by_num[${num}]:-}" ]]; then
      by_num["${num}"]="${file}"
      nums+=("${num}")
      continue
    fi
    chosen="$(_prefer_milestone_path "${by_num[${num}]}" "${file}")"
    if [[ "${chosen}" != "${by_num[${num}]}" || "${file}" != "${by_num[${num}]}" ]]; then
      if [[ -z "${warned[${num}]:-}" ]]; then
        echo "Warning: milestone-${num} exists at root and under requirements/milestones/; preferring subdirectory." >&2
        warned["${num}"]=1
      fi
    fi
    by_num["${num}"]="${chosen}"
  done < <(_list_milestone_definition_candidates "${target}")

  # Stable numeric-ish order (string sort is fine for typical 1..N).
  local sorted
  if ((${#nums[@]} > 0)); then
    mapfile -t sorted < <(printf '%s\n' "${nums[@]}" | sort -n -u)
    for num in "${sorted[@]}"; do
      file="${by_num[${num}]}"
      [[ -n "${file}" ]] || continue
      if [[ "${mode}" == "relative" ]]; then
        printf '%s\n' "${file#${target}/}"
      else
        printf '%s\n' "${file}"
      fi
    done
  fi
}

# resolve_milestone TARGET WORK_ID [candidate] [mode]
#   mode absolute — return absolute path (capture-session-memory default)
#   mode relative — return path relative to TARGET (start-agent-session default)
resolve_milestone() {
  local target="$1"
  local work_id="$2"
  local candidate="${3:-}"
  local mode="${4:-absolute}"

  if [[ -n "${candidate}" ]]; then
    if [[ "${candidate}" != *.md && "${candidate}" != *.MD ]]; then
      candidate="${candidate}.md"
    fi
    if [[ -f "${target}/${candidate}" ]]; then
      if [[ "${mode}" == "relative" ]]; then
        printf '%s' "${candidate}"
      else
        printf '%s' "${target}/${candidate}"
      fi
      return 0
    fi
    if [[ -f "${candidate}" ]]; then
      if [[ "${mode}" == "relative" ]]; then
        printf '%s' "${candidate#${target}/}"
      else
        printf '%s' "${candidate}"
      fi
      return 0
    fi
    # Allow --milestone milestone-1 to resolve to subdirectory definition.
    local num file
    if num="$(_milestone_number_from_path "${candidate}" 2>/dev/null)"; then
      while IFS= read -r file; do
        [[ -n "${file}" ]] || continue
        if [[ "$(_milestone_number_from_path "${file}" || true)" == "${num}" ]]; then
          if [[ "${mode}" == "relative" ]]; then
            printf '%s' "${file#${target}/}"
          else
            printf '%s' "${file}"
          fi
          return 0
        fi
      done < <(list_milestone_files "${target}" absolute)
    fi
    return 1
  fi

  if [[ -z "${work_id}" ]]; then
    return 1
  fi

  local file
  while IFS= read -r file; do
    [[ -n "${file}" ]] || continue
    if grep -q "${work_id}" "${file}" 2>/dev/null; then
      if [[ "${mode}" == "relative" ]]; then
        printf '%s' "${file#${target}/}"
      else
        printf '%s' "${file}"
      fi
      return 0
    fi
  done < <(list_milestone_files "${target}" absolute)
  return 1
}

# resolve_requirement_path TARGET WORK_ID [mode]
# Find requirements/milestones/<WORK-ID>.md (flat) or under milestone-N/ subdirs.
# Prefer subdirectory when both exist (with warning).
resolve_requirement_path() {
  local target="$1"
  local work_id="$2"
  local mode="${3:-relative}"
  local flat="${target}/requirements/milestones/${work_id}.md"
  local nested="" dir candidate
  local -a nested_hits=()

  shopt -s nullglob
  for dir in "${target}"/requirements/milestones/milestone-*/; do
    candidate="${dir}${work_id}.md"
    if [[ -f "${candidate}" ]]; then
      nested_hits+=("${candidate}")
    fi
  done
  shopt -u nullglob

  if ((${#nested_hits[@]} > 0)); then
    nested="${nested_hits[0]}"
    if [[ -f "${flat}" ]]; then
      echo "Warning: ${work_id} requirement exists flat and under ${nested#${target}/}; preferring subdirectory." >&2
    fi
    if [[ "${mode}" == "relative" ]]; then
      printf '%s' "${nested#${target}/}"
    else
      printf '%s' "${nested}"
    fi
    return 0
  fi

  if [[ -f "${flat}" ]]; then
    if [[ "${mode}" == "relative" ]]; then
      printf '%s' "requirements/milestones/${work_id}.md"
    else
      printf '%s' "${flat}"
    fi
    return 0
  fi
  return 1
}

# requirement_dir_for_milestone TARGET MILESTONE_PATH
# Directory where new requirement stubs should be written for this milestone.
# Prefers requirements/milestones/milestone-N/ when the milestone lives there
# or that directory already exists; otherwise flat requirements/milestones/.
requirement_dir_for_milestone() {
  local target="$1"
  local milestone_path="$2"
  local num subdir

  if _is_subdir_milestone_definition "${milestone_path}"; then
    printf '%s' "$(dirname "${milestone_path}")"
    return 0
  fi

  num="$(_milestone_number_from_path "${milestone_path}" || true)"
  if [[ -n "${num}" ]]; then
    subdir="${target}/requirements/milestones/milestone-${num}"
    if [[ -d "${subdir}" ]]; then
      printf '%s' "${subdir}"
      return 0
    fi
  fi

  printf '%s' "${target}/requirements/milestones"
}

# has_any_milestone TARGET — true if root or subdirectory milestone definitions exist.
has_any_milestone() {
  local target="$1"
  local count=0
  while IFS= read -r _; do
    count=$((count + 1))
  done < <(list_milestone_files "${target}" absolute)
  (( count > 0 ))
}
