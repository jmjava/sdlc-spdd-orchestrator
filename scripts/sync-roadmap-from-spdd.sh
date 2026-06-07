#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: sync-roadmap-from-spdd.sh [--target <path>] [--roadmap <file>] [--dry-run]

Update a managed SDLC-SPDD summary section in ROADMAP.md from spdd/canvas/*.md.

The script preserves all roadmap content outside these markers:
  <!-- SDLC-SPDD-ROADMAP-SUMMARY:START -->
  <!-- SDLC-SPDD-ROADMAP-SUMMARY:END -->
EOF
}

TARGET="."
ROADMAP="ROADMAP.md"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --roadmap)
      ROADMAP="${2:-}"
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

TARGET="$(cd "${TARGET}" && pwd)"
if [[ "${ROADMAP}" != /* ]]; then
  ROADMAP="${TARGET}/${ROADMAP}"
fi

canvas_dir="${TARGET}/spdd/canvas"
start_marker="<!-- SDLC-SPDD-ROADMAP-SUMMARY:START -->"
end_marker="<!-- SDLC-SPDD-ROADMAP-SUMMARY:END -->"
tmp_summary="$(mktemp)"
tmp_roadmap="$(mktemp)"

field_value() {
  local label="$1"
  local file="$2"
  sed -n "s/^- ${label}:[[:space:]]*//p" "${file}" | sed -n '1p'
}

{
  echo
  echo "## SDLC-SPDD Work Summary"
  echo
  echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo
  echo "| Work ID | Title | Type | Status | Milestone | Source | Canvas |"
  echo "|---------|-------|------|--------|-----------|--------|--------|"
} > "${tmp_summary}"

shopt -s nullglob
canvas_files=("${canvas_dir}"/*.md)
shopt -u nullglob

if ((${#canvas_files[@]} == 0)); then
  echo "| none | - | - | - | - | - |" >> "${tmp_summary}"
else
  for file in "${canvas_files[@]}"; do
    work_id="$(field_value "Work ID" "${file}")"
    work_type="$(field_value "Work Type" "${file}")"
    status="$(field_value "Status" "${file}")"
    milestone="$(field_value "Milestone" "${file}")"
    source_url="$(field_value "Source URL" "${file}")"
    title="$(sed -n 's/^# REASONS Canvas: .* - //p' "${file}" | sed -n '1p')"
    rel="${file#${TARGET}/}"
    work_id="${work_id:-$(basename "${file}" .md)}"
    title="${title:-TBD}"
    work_type="${work_type:-TBD}"
    status="${status:-TBD}"
    milestone="${milestone:-TBD}"
    source_url="${source_url:-TBD}"
    echo "| ${work_id} | ${title} | ${work_type} | ${status} | ${milestone} | ${source_url} | ${rel} |" >> "${tmp_summary}"
  done
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "${start_marker}"
  cat "${tmp_summary}"
  echo "${end_marker}"
  rm -f "${tmp_summary}" "${tmp_roadmap}"
  exit 0
fi

if [[ ! -f "${ROADMAP}" ]]; then
  {
    echo "# Roadmap"
    echo
  } > "${ROADMAP}"
fi

if grep -Fq "${start_marker}" "${ROADMAP}" && grep -Fq "${end_marker}" "${ROADMAP}"; then
  awk -v start="${start_marker}" -v end="${end_marker}" -v summary="${tmp_summary}" '
    $0 == start {
      print
      while ((getline line < summary) > 0) {
        print line
      }
      in_block = 1
      next
    }
    $0 == end {
      in_block = 0
      print
      next
    }
    !in_block { print }
  ' "${ROADMAP}" > "${tmp_roadmap}"
  mv "${tmp_roadmap}" "${ROADMAP}"
else
  {
    echo
    echo "${start_marker}"
    cat "${tmp_summary}"
    echo "${end_marker}"
  } >> "${ROADMAP}"
fi

rm -f "${tmp_summary}" "${tmp_roadmap}"
echo "Updated roadmap summary: ${ROADMAP}"
echo
echo "Planning review prompt (see docs/sdlc-spdd/planning-prompt-standard.md):"
echo "  Read @ROADMAP.md. Review the SDLC-SPDD Work Summary table. Does Current Focus match the active Work ID and phase?"
