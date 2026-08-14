#!/usr/bin/env bash
# Bootstrap canonical command specs from existing adapter templates (one-time / refresh).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SPEC_DIR="${REPO_ROOT}/spec/commands"

lifecycle_commands=(
  init analysis plan architect code api-test review commit-message prompt-update retro accept sync sunset whereami
)
workflow_commands=(
  claim shelf advance next team
)

strip_front_matter() {
  awk 'BEGIN { fm=0 }
    NR==1 && /^---$/ { fm=1; next }
    fm && /^---$/ { fm=0; next }
    fm { next }
    { print }' "$1"
}

first_heading() {
  strip_front_matter "$1" | awk '/^# / { sub(/^# /, ""); print; exit }'
}

section_body() {
  local file="$1"
  local section="$2"
  strip_front_matter "${file}" | awk -v section="${section}" '
    $0 ~ "^## " section "$" { in_section = 1; next }
    /^## / { in_section = 0 }
    in_section { print }
  ' | sed -e :a -e '/^\s*$/N; s/\n$//' -e ta
}

preamble_body() {
  local file="$1"
  strip_front_matter "${file}" | awk '
    /^## Required Behavior/ { exit }
    !found && /^# / { found = 1; next }
    found { print }
  ' | sed -e :a -e '/^\s*$/N; s/\n$//' -e ta
}

front_matter_value() {
  local file="$1"
  local key="$2"
  awk -v key="${key}" '
    BEGIN { in_fm=0 }
    NR==1 && /^---$/ { in_fm=1; next }
    in_fm && /^---$/ { exit }
    in_fm {
      if ($0 ~ "^" key ":") {
        sub("^" key ":[[:space:]]*", "")
        print
        exit
      }
    }
  ' "${file}"
}

write_block() {
  local id="$1"
  local body="$2"
  printf '%s\n' "---BLOCK:${id}---"
  if [[ -n "${body}" ]]; then
    printf '%s\n' "${body}"
  fi
  printf '%s\n' "---END---"
}

write_spec() {
  local family="$1"
  local slug="$2"
  local cursor_file="$3"
  local copilot_file="$4"
  local claude_file="$5"
  local out="${SPEC_DIR}/${family}-${slug}.spec.md"

  local rb_c rb_p rb_cl out_c out_p out_cl cb_c cb_p cb_cl
  rb_c="$(section_body "${cursor_file}" "Required Behavior")"
  rb_p="$(section_body "${copilot_file}" "Required Behavior")"
  rb_cl="$(section_body "${claude_file}" "Required Behavior")"
  out_c="$(section_body "${cursor_file}" "Output")"
  out_p="$(section_body "${copilot_file}" "Output")"
  out_cl="$(section_body "${claude_file}" "Output")"
  cb_c="$(section_body "${cursor_file}" "Context Backend \\(runtime-resolved\\)")"
  cb_p="$(section_body "${copilot_file}" "Context Backend \\(runtime-resolved\\)")"
  cb_cl="$(section_body "${claude_file}" "Context Backend \\(runtime-resolved\\)")"

  {
    echo "---"
    echo "family: ${family}"
    echo "slug: ${slug}"
    if [[ -f "${copilot_file}" ]]; then
      local cp_desc mode
      cp_desc="$(front_matter_value "${copilot_file}" description)"
      [[ -n "${cp_desc}" ]] && echo "copilot_description: ${cp_desc}"
      mode="$(front_matter_value "${copilot_file}" mode)"
      [[ -n "${mode}" ]] && echo "copilot_mode: ${mode}"
    fi
    if [[ -f "${claude_file}" ]]; then
      local cl_desc hint
      cl_desc="$(front_matter_value "${claude_file}" description)"
      [[ -n "${cl_desc}" ]] && echo "claude_description: ${cl_desc}"
      hint="$(front_matter_value "${claude_file}" argument-hint)"
      [[ -n "${hint}" ]] && echo "claude_argument_hint: ${hint}"
    fi
    echo "---"
    echo
    write_block "cursor:title" "$(first_heading "${cursor_file}")"
    write_block "copilot:title" "$(first_heading "${copilot_file}")"
    write_block "claude:title" "$(first_heading "${claude_file}")"
    write_block "cursor:preamble" "$(preamble_body "${cursor_file}")"
    write_block "copilot:preamble" "$(preamble_body "${copilot_file}")"
    write_block "claude:preamble" "$(preamble_body "${claude_file}")"

    if [[ "${rb_c}" == "${rb_p}" && "${rb_p}" == "${rb_cl}" ]]; then
      write_block "shared:Required Behavior" "${rb_c}"
    else
      write_block "cursor:Required Behavior" "${rb_c}"
      write_block "copilot:Required Behavior" "${rb_p}"
      write_block "claude:Required Behavior" "${rb_cl}"
    fi

    # Optional section; the generator emits it only when the block exists.
    if [[ -n "${cb_c}" || -n "${cb_p}" || -n "${cb_cl}" ]]; then
      if [[ "${cb_c}" == "${cb_p}" && "${cb_p}" == "${cb_cl}" ]]; then
        write_block "shared:Context Backend (runtime-resolved)" "${cb_c}"
      else
        write_block "cursor:Context Backend (runtime-resolved)" "${cb_c}"
        write_block "copilot:Context Backend (runtime-resolved)" "${cb_p}"
        write_block "claude:Context Backend (runtime-resolved)" "${cb_cl}"
      fi
    fi

    if [[ "${out_c}" == "${out_p}" && "${out_p}" == "${out_cl}" ]]; then
      write_block "shared:Output" "${out_c}"
    else
      write_block "cursor:Output" "${out_c}"
      write_block "copilot:Output" "${out_p}"
      write_block "claude:Output" "${out_cl}"
    fi
  } > "${out}"
  echo "Wrote ${out#${REPO_ROOT}/}"
}

mkdir -p "${SPEC_DIR}"

for slug in "${lifecycle_commands[@]}"; do
  write_spec lifecycle "${slug}" \
    "${REPO_ROOT}/templates/cursor/sdlc-spdd-${slug}.md" \
    "${REPO_ROOT}/templates/copilot/prompts/sdlc-spdd-${slug}.prompt.md" \
    "${REPO_ROOT}/templates/claude/commands/sdlc-spdd-${slug}.md"
done

for slug in "${workflow_commands[@]}"; do
  write_spec workflow "${slug}" \
    "${REPO_ROOT}/templates/cursor/sdlc-${slug}.md" \
    "${REPO_ROOT}/templates/copilot/prompts/sdlc-${slug}.prompt.md" \
    "${REPO_ROOT}/templates/claude/commands/sdlc-${slug}.md"
done

echo "Extracted $(find "${SPEC_DIR}" -name '*.spec.md' | wc -l) command specs."
