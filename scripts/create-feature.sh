#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib/work-id.sh"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib/paths.sh"

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
export SDLC_ROOT="${TARGET}"
HOME="$(sdlc_home "${TARGET}")"

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
canvas_dir="${HOME}/spdd/canvas"
req_dir="${HOME}/requirements/milestones"
mkdir -p "${canvas_dir}" "${req_dir}"

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

timestamp="$(sdlc_timestamp_iso)"
stage_file="$(sdlc_stage "${TARGET}")"
record="$(sdlc_build_lesson_json session "${work_id}" "" "init" "${timestamp}" \
  "Created ${work_id}" "Created stay-set canvas + requirement for ${NAME}." "create-feature" "" "" "${TARGET}")"
mkdir -p "$(dirname "${stage_file}")"
sdlc_append_jsonl "${stage_file}" "${record}"

echo "Created:"
echo "  ${canvas_dir}/${work_id}.md"
echo "  ${req_dir}/${work_id}.md"
echo "  staged session record → ${stage_file#${TARGET}/}"
# Hard rule: do not create agent-context/features/<WORK-ID>/
