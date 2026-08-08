#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib/work-id.sh"

usage() {
  cat <<'EOF'
Usage: create-feature.sh --type <feature|bug|refactor|spike> --name <short-name> [--target <path>]

Create stay-set REASONS canvas + milestone requirement (no agent-context/features mirrors).
EOF
}

TYPE=""
NAME=""
TARGET="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --type)
      TYPE="${2:-}"
      shift 2
      ;;
    --name)
      NAME="${2:-}"
      shift 2
      ;;
    --target)
      TARGET="${2:-}"
      shift 2
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

if [[ -z "${TYPE}" || -z "${NAME}" ]]; then
  echo "Error: --type and --name are required" >&2
  usage >&2
  exit 1
fi

TARGET="$(cd "${TARGET}" && pwd)"

case "${TYPE}" in
  feature) TEMPLATE="feature-template.md" ;;
  bug) TEMPLATE="bugfix-template.md" ;;
  refactor) TEMPLATE="refactor-template.md" ;;
  spike) TEMPLATE="spike-template.md" ;;
  *)
    echo "Unsupported type: ${TYPE}" >&2
    exit 1
    ;;
esac

PREFIX="$(work_type_prefix "${TYPE}")"
slug="$(slugify "${NAME}" legacy)"
canvas_dir="${TARGET}/spdd/canvas"
req_dir="${TARGET}/requirements/milestones"
mkdir -p "${canvas_dir}" "${req_dir}" "${TARGET}/spdd/memory/entries"

next="$(next_work_number "${PREFIX}" "${TARGET}" "${canvas_dir}/${PREFIX}-"*.md)"
work_id="$(printf '%s-%03d-%s' "${PREFIX}" "${next}" "${slug}")"

template="${REPO_ROOT}/templates/reasons-canvas/${TEMPLATE}"
canvas_content="$(sed "s/<WORK-ID>/${work_id}/g; s/<Work Name>/${NAME}/g" "${template}")"

printf '%s\n' "${canvas_content}" > "${canvas_dir}/${work_id}.md"

cat > "${req_dir}/${work_id}.md" <<EOF
# Requirement: ${work_id}

## Summary

${NAME}

## Source

Add requirement details here.
EOF

# Lean progress ledger (not feature mirror).
progress="${TARGET}/spdd/memory/entries/progress.md"
if [[ ! -f "${progress}" ]]; then
  printf '# Progress Entries\n\n' > "${progress}"
fi
{
  echo ""
  echo "## ${work_id}"
  echo ""
  echo "- Created stay-set canvas + requirement (no feature mirror)."
} >> "${progress}"

echo "Created:"
echo "  ${canvas_dir}/${work_id}.md"
echo "  ${req_dir}/${work_id}.md"
echo "  ${progress} (appended)"
# Hard rule: do not create agent-context/features/<WORK-ID>/
