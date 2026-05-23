#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: create-feature.sh --type <feature|bug|refactor|spike> --name <short-name> [--target <path>]

Create a feature workspace folder and REASONS Canvas from template.
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
  feature) PREFIX="FEAT"; TEMPLATE="feature-template.md" ;;
  bug) PREFIX="BUG"; TEMPLATE="bugfix-template.md" ;;
  refactor) PREFIX="REF"; TEMPLATE="refactor-template.md" ;;
  spike) PREFIX="SPIKE"; TEMPLATE="spike-template.md" ;;
  *)
    echo "Unsupported type: ${TYPE}" >&2
    exit 1
    ;;
esac

slug="$(echo "${NAME}" | tr '[:upper:]' '[:lower:]' | tr ' _' '-' | sed 's/[^a-z0-9-]//g')"
features_dir="${TARGET}/agent-context/features"
mkdir -p "${features_dir}"

max=0
shopt -s nullglob
for dir in "${features_dir}/${PREFIX}-"*; do
  id="$(basename "${dir}")"
  num="${id#${PREFIX}-}"
  num="${num%%-*}"
  if [[ "${num}" =~ ^[0-9]+$ ]] && (( 10#${num} > max )); then
    max=$((10#${num}))
  fi
done
shopt -u nullglob

next=$((max + 1))
work_id="$(printf '%s-%03d-%s' "${PREFIX}" "${next}" "${slug}")"

feature_dir="${features_dir}/${work_id}"
canvas_dir="${TARGET}/spdd/canvas"
tasks_dir="${feature_dir}/tasks"
mkdir -p "${feature_dir}" "${tasks_dir}" "${canvas_dir}"

template="${REPO_ROOT}/templates/reasons-canvas/${TEMPLATE}"
canvas_content="$(sed "s/<WORK-ID>/${work_id}/g; s/<Work Name>/${NAME}/g" "${template}")"

printf '%s\n' "${canvas_content}" > "${feature_dir}/reasons-canvas.md"
printf '%s\n' "${canvas_content}" > "${canvas_dir}/${work_id}.md"

cat > "${feature_dir}/requirement.md" <<EOF
# Requirement: ${work_id}

## Summary

${NAME}

## Source

Add requirement details here.
EOF

cat > "${feature_dir}/progress-log.md" <<EOF
# Progress Log: ${work_id}

## ${work_id}

- Created feature workspace and canvas.
EOF

echo "Created:"
echo "  ${feature_dir}/"
echo "  ${canvas_dir}/${work_id}.md"
