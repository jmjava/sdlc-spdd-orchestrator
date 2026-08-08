#!/usr/bin/env bash
# FEAT-001 T04 — fail if extracted lib helpers are redefined outside scripts/lib/.
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${_SCRIPT_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: verify-script-lib-duplicates.sh

Scan scripts/*.sh for duplicate definitions of helpers that belong in scripts/lib/.
Exits 0 when no stray duplicates are found; exits 1 otherwise.

Orchestrator-only lib helpers (framework-install, shipped-docs-boundary) are
checked only under scripts/, never shipped to installed targets.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

# Function names that must exist only in scripts/lib/*.sh (not consumer scripts).
LIB_FUNCTIONS=(
  sdlc_resolve_target
  sdlc_timestamp_iso
  sdlc_timestamp_file
  sdlc_timestamp_day
  sdlc_die
  sdlc_unknown_option
  sdlc_ensure_dir
  sdlc_ensure_file
  sdlc_oneline
  sdlc_require_lib
  normalize_token
  normalize_area
  parse_section_bullets
  slugify
  next_work_number
  work_type_prefix
  resolve_milestone
  normalize_readiness
  extract_readiness_raw
  canvas_readiness
  readiness_allows_coding
  framework_ensure_dir
  is_orchestrator_only_doc
  collect_shipped_doc_paths
)

failures=0

for fn in "${LIB_FUNCTIONS[@]}"; do
  while IFS= read -r hit; do
    [[ -z "${hit}" ]] && continue
    rel="${hit#${REPO_ROOT}/}"
    echo "Duplicate lib helper '${fn}' defined outside scripts/lib/: ${rel}" >&2
    failures=$((failures + 1))
  done < <(
    grep -R -l -E "^${fn}\(\)" "${REPO_ROOT}/scripts" --include='*.sh' 2>/dev/null \
      | grep -v '/scripts/lib/' \
      || true
  )
done

# Every consumer under scripts/ that sources a lib must use the standard _SCRIPT_DIR pattern.
while IFS= read -r script; do
  [[ -z "${script}" ]] && continue
  if ! grep -q '_SCRIPT_DIR=.*BASH_SOURCE' "${script}"; then
    rel="${script#${REPO_ROOT}/}"
    echo "Script sources lib but missing _SCRIPT_DIR convention: ${rel}" >&2
    failures=$((failures + 1))
  fi
done < <(
  grep -R -l 'source "${_SCRIPT_DIR}/lib/' "${REPO_ROOT}/scripts" --include='*.sh' 2>/dev/null \
    | grep -v '/scripts/lib/' \
    || true
)

if (( failures > 0 )); then
  echo
  echo "verify-script-lib-duplicates: ${failures} issue(s)." >&2
  exit 1
fi

echo "verify-script-lib-duplicates: no stray lib duplicates found."
