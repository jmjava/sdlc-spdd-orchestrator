#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: create-work-from-milestone.sh --milestone <file> (--all|--item <text>) [options]

Create SDLC-SPDD work artifacts from milestone checklist items.

Options:
  --target <path>       Target project path (default: .)
  --milestone <file>    Milestone file, such as milestone-1.md (required)
  --all                 Create work for all unchecked milestone checklist items
  --item <text>         Create work for one milestone item
  --type <type>         feature, bug, refactor, or spike (default: feature)
  --roadmap <file>      Roadmap path recorded in canvas metadata (default: ROADMAP.md)
  --dry-run             Show planned work without writing files
  --help                Print this help message

Examples:
  ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all
  ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-2.md --item "Add order status API" --type feature
EOF
}

TARGET="."
MILESTONE=""
ITEM=""
CREATE_ALL=0
TYPE="feature"
ROADMAP="ROADMAP.md"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --milestone)
      MILESTONE="${2:-}"
      shift 2
      ;;
    --all)
      CREATE_ALL=1
      shift
      ;;
    --item)
      ITEM="${2:-}"
      shift 2
      ;;
    --type)
      TYPE="${2:-}"
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

if [[ -z "${MILESTONE}" ]]; then
  echo "Error: --milestone is required" >&2
  usage >&2
  exit 1
fi

if [[ "${CREATE_ALL}" -eq 1 && -n "${ITEM}" ]]; then
  echo "Error: use either --all or --item, not both" >&2
  exit 1
fi

if [[ "${CREATE_ALL}" -eq 0 && -z "${ITEM}" ]]; then
  echo "Error: one of --all or --item is required" >&2
  usage >&2
  exit 1
fi

case "${TYPE}" in
  feature) PREFIX="FEAT"; WORK_TYPE="Feature" ;;
  bug|bugfix) PREFIX="BUG"; WORK_TYPE="Bugfix" ;;
  refactor) PREFIX="REF"; WORK_TYPE="Refactor" ;;
  spike) PREFIX="SPIKE"; WORK_TYPE="Spike" ;;
  *)
    echo "Unsupported type: ${TYPE}" >&2
    exit 1
    ;;
esac

TARGET="$(cd "${TARGET}" && pwd)"
if [[ "${MILESTONE}" != /* ]]; then
  MILESTONE="${TARGET}/${MILESTONE}"
fi
if [[ ! -f "${MILESTONE}" ]]; then
  echo "Milestone file not found: ${MILESTONE}" >&2
  exit 1
fi

milestone_rel="${MILESTONE#${TARGET}/}"
roadmap_rel="${ROADMAP#${TARGET}/}"

slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' _/' '---' | sed 's/[^a-z0-9-]//g; s/--*/-/g; s/^-//; s/-$//'
}

next_number() {
  local max=0
  local path id num
  shopt -s nullglob
  for path in "${TARGET}/agent-context/features/${PREFIX}-"* "${TARGET}/spdd/canvas/${PREFIX}-"*.md; do
    id="$(basename "${path}")"
    id="${id%.md}"
    num="${id#${PREFIX}-}"
    num="${num%%-*}"
    if [[ "${num}" =~ ^[0-9]+$ ]] && ((10#${num} > max)); then
      max=$((10#${num}))
    fi
  done
  shopt -u nullglob
  echo $((max + 1))
}

items=()
if [[ "${CREATE_ALL}" -eq 1 ]]; then
  while IFS= read -r line; do
    if [[ "${line}" =~ ^[[:space:]]*[-*][[:space:]]+\[[[:space:]]\][[:space:]]+(.+) ]]; then
      items+=("${BASH_REMATCH[1]}")
    fi
  done < "${MILESTONE}"
else
  items+=("${ITEM}")
fi

if ((${#items[@]} == 0)); then
  echo "No unchecked milestone items found in ${milestone_rel}" >&2
  exit 1
fi

append_milestone_map_header() {
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    return
  fi
  if ! grep -Fq "## SDLC-SPDD Work Map" "${MILESTONE}"; then
    {
      echo
      echo "## SDLC-SPDD Work Map"
      echo
      echo "| Work ID | Canvas | Requirement | Status | Notes |"
      echo "|---------|--------|-------------|--------|-------|"
    } >> "${MILESTONE}"
  fi
}

create_work() {
  local title="$1"
  local number slug work_id feature_dir canvas_path requirement_path progress_log status_date
  number="$(next_number)"
  slug="$(slugify "${title}")"
  if [[ -z "${slug}" ]]; then
    slug="milestone-work"
  fi
  work_id="$(printf '%s-%03d-%s' "${PREFIX}" "${number}" "${slug}")"
  feature_dir="${TARGET}/agent-context/features/${work_id}"
  canvas_path="${TARGET}/spdd/canvas/${work_id}.md"
  requirement_path="${feature_dir}/requirement.md"
  progress_log="${feature_dir}/progress-log.md"
  status_date="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would create ${work_id} from milestone item: ${title}"
    echo "[dry-run] would write ${canvas_path}"
    echo "[dry-run] would write ${requirement_path}"
    echo "[dry-run] would update ${milestone_rel}"
    return
  fi

  mkdir -p "${feature_dir}/tasks" "${TARGET}/spdd/canvas" "${TARGET}/requirements/milestones"

  cat > "${canvas_path}" <<EOF
# REASONS Canvas: ${work_id} - ${title}

## Metadata

- Work ID: ${work_id}
- Work Type: ${WORK_TYPE}
- Status: Draft
- Created: ${status_date}
- Updated: ${status_date}
- Owner:
- Target Project:
- Stack:
- Source System: Milestone
- Source Issue:
- Source URL:
- Docs URL:
- Roadmap: ${roadmap_rel}
- Milestone: ${milestone_rel}
- Related PR:

## R - Requirements

### User Goal

${title}

### Business / Product Goal

Derived from ${milestone_rel}.

### Acceptance Criteria

- [ ] Define acceptance criteria before coding.

### Non-Goals

- TBD

### Assumptions

- Created from milestone item: ${title}

### Open Questions

- What acceptance criteria are required for this work?

## E - Entities

### Domain Entities

- TBD

### Application Components

- TBD

### External Systems

- TBD

### Data / Persistence

- TBD

### Files Likely Affected

- TBD

## A - Approach

### Proposed Approach

TBD during \`/sdlc-spdd-plan\` and \`/sdlc-spdd-architect\`.

### Alternatives Considered

- TBD

### Trade-Offs

- TBD

### Risks

- TBD

### Failure Modes

- TBD

## S - Structure

### Files To Add

- TBD

### Files To Modify

- TBD

### Package / Module Structure

TBD

### Test Structure

TBD

### Documentation Structure

TBD

## O - Operations

### T01 - Clarify and plan

- Status: Not Started
- Description: Convert the milestone item into a complete REASONS Canvas.
- Files: ${canvas_path#${TARGET}/}
- Tests: Not applicable
- Validation: Canvas review

## N - Norms

### General

- Follow existing project conventions.
- Keep implementation aligned with this canvas.
- Do not invent requirements that were not requested.
- Update the canvas before behavior changes.

### Testing

- Add or update tests for behavior changes.
- Document tests that could not be run.

## S - Safeguards

- Do not code until the canvas is Ready For Coding.
- Do not implement behavior changes until this canvas is updated with \`/sdlc-spdd-prompt-update\`.
- Do not let implementation drift from this canvas without running \`/sdlc-spdd-sync\`.

## Review Checklist

- [ ] Requirements satisfied
- [ ] Entities updated correctly
- [ ] Approach followed or synced
- [ ] Structure followed or synced
- [ ] Operations completed
- [ ] Norms followed
- [ ] Safeguards respected
- [ ] Tests added or updated
- [ ] No unrelated refactors
- [ ] Documentation updated if needed

## Sync Notes

Created from ${milestone_rel}. Use sync notes to track drift between the milestone, canvas, and implementation.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
EOF

  cp "${canvas_path}" "${feature_dir}/reasons-canvas.md"

  cat > "${requirement_path}" <<EOF
# Requirement: ${work_id}

## Summary

${title}

## Source

- Roadmap: ${roadmap_rel}
- Milestone: ${milestone_rel}

## Next Step

Run:

    /sdlc-spdd-plan @${requirement_path#${TARGET}/} @${milestone_rel}
EOF

  cat > "${progress_log}" <<EOF
# Progress Log: ${work_id}

## ${work_id}

- ${status_date}: Created from milestone item in ${milestone_rel}.
EOF

  append_milestone_map_header
  echo "| ${work_id} | spdd/canvas/${work_id}.md | ${requirement_path#${TARGET}/} | Draft | Created from milestone item |" >> "${MILESTONE}"

  echo "Created ${work_id}"
  echo "  ${canvas_path}"
  echo "  ${requirement_path}"
}

for item in "${items[@]}"; do
  create_work "${item}"
done
