#!/usr/bin/env bash
# Shared helpers for docs that must NOT install into target projects.
# Keep in sync with init-project.sh and upgrade-project.sh skip lists.

# Returns 0 when the doc is orchestrator-internal only (must not ship).
is_orchestrator_only_doc() {
  local base
  base="$(basename "$1")"
  case "${base}" in
    README.md | guide-rag-research-and-dogfooding.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

# Append shipped doc paths (repo-relative) to the array named by $1.
collect_shipped_doc_paths() {
  local -n _out=$1
  local f
  for f in docs/*.md; do
    [[ -e "${f}" ]] || continue
    is_orchestrator_only_doc "${f}" && continue
    _out+=("${f}")
  done
}
