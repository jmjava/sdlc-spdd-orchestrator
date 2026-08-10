#!/usr/bin/env bash
# Work-ID slug and numbering helpers.

# slugify TEXT [mode]
#   strict — create-work-from-milestone behavior (default)
#   legacy — create-feature behavior
slugify() {
  local text="$1"
  local mode="${2:-strict}"
  local s
  s="$(printf '%s' "${text}" | tr '[:upper:]' '[:lower:]')"
  case "${mode}" in
    strict)
      s="$(printf '%s' "${s}" | tr ' _/' '---' | sed 's/[^a-z0-9-]//g; s/--*/-/g; s/^-//; s/-$//')"
      ;;
    legacy)
      s="$(printf '%s' "${s}" | tr '_ ' '-' | sed 's/[^a-z0-9-]//g')"
      ;;
    *)
      echo "slugify: unknown mode '${mode}' (use strict or legacy)" >&2
      return 2
      ;;
  esac
  printf '%s' "${s}"
}

# next_work_number PREFIX TARGET GLOB [GLOB...]
# Returns the next 1-based sequence number for Work IDs with the given prefix.
next_work_number() {
  local prefix="$1"
  local target="$2"
  shift 2
  local max=0
  local path id num
  shopt -s nullglob
  for path in "$@"; do
    id="$(basename "${path}")"
    id="${id%.md}"
    num="${id#${prefix}-}"
    num="${num%%-*}"
    if [[ "${num}" =~ ^[0-9]+$ ]] && ((10#${num} > max)); then
      max=$((10#${num}))
    fi
  done
  shopt -u nullglob
  echo $((max + 1))
}

# work_type_prefix TYPE
# Maps feature/bug/refactor/spike (and bugfix alias) to FEAT/BUG/REF/SPIKE.
work_type_prefix() {
  local type
  type="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "${type}" in
    feature|feat) printf '%s' "FEAT" ;;
    bug|bugfix) printf '%s' "BUG" ;;
    refactor|ref) printf '%s' "REF" ;;
    spike) printf '%s' "SPIKE" ;;
    doc) printf '%s' "DOC" ;;
    test) printf '%s' "TEST" ;;
    chore) printf '%s' "CHORE" ;;
    *) printf '%s' "FEAT" ;;
  esac
}
