#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/work-id.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/milestone.sh"

usage() {
  cat <<'EOF'
Usage: create-work-from-milestone.sh --milestone <file> (--all|--item <text>) [options]

Create SDLC-SPDD work artifacts from milestone checklist items.

Options:
  --target <path>       Target project path (default: .)
  --milestone <file>    Milestone definition: root milestone-1.md or
                        requirements/milestones/milestone-1/MILESTONE-1.md (required)
  --all                 Create work for all unchecked milestone checklist items
  --item <text>         Create work for one milestone item
  --type <type>         feature, bug, refactor, or spike (default: feature)
  --roadmap <file>      Roadmap path recorded in canvas metadata (default: ROADMAP.md)
  --dry-run             Show planned work without writing files
  --help                Print this help message

Examples:
  ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all
  ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . \
    --milestone requirements/milestones/milestone-2/MILESTONE-2.md --item "Add order status API"
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

TARGET="$(sdlc_resolve_target "${TARGET}")"
milestone_arg="${MILESTONE}"
if [[ "${MILESTONE}" != /* ]]; then
  if [[ -f "${TARGET}/${MILESTONE}" ]]; then
    MILESTONE="${TARGET}/${MILESTONE}"
  elif resolved="$(resolve_milestone "${TARGET}" "" "${milestone_arg}" absolute 2>/dev/null)"; then
    MILESTONE="${resolved}"
  else
    MILESTONE="${TARGET}/${MILESTONE}"
  fi
fi
if [[ ! -f "${MILESTONE}" ]]; then
  echo "Milestone file not found: ${milestone_arg}" >&2
  echo "Tried: ${MILESTONE}" >&2
  exit 1
fi

milestone_rel="${MILESTONE#${TARGET}/}"
roadmap_rel="${ROADMAP#${TARGET}/}"
requirement_parent="$(requirement_dir_for_milestone "${TARGET}" "${MILESTONE}")"
requirement_parent_rel="${requirement_parent#${TARGET}/}"

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
  if ! grep -Fq "## Linked Work" "${MILESTONE}" && ! grep -Fq "## SDLC-SPDD Work Map" "${MILESTONE}"; then
    {
      echo
      echo "## Linked Work"
      echo
      echo "| Work ID | Canvas | Requirement | Status | Notes |"
      echo "|---------|--------|-------------|--------|-------|"
    } >> "${MILESTONE}"
  fi
}

create_work() {
  local title="$1"
  local number slug work_id canvas_path milestone_requirement_path
  local progress_log status_date milestone_requirement_rel
  # Number from stay-set canvases only — no agent-context/features (#86).
  number="$(next_work_number "${PREFIX}" "${TARGET}" \
    "${TARGET}/spdd/canvas/${PREFIX}-"*.md)"
  slug="$(slugify "${title}" strict)"
  if [[ -z "${slug}" ]]; then
    slug="milestone-work"
  fi
  work_id="$(printf '%s-%03d-%s' "${PREFIX}" "${number}" "${slug}")"
  canvas_path="${TARGET}/spdd/canvas/${work_id}.md"
  milestone_requirement_path="${requirement_parent}/${work_id}.md"
  milestone_requirement_rel="${requirement_parent_rel}/${work_id}.md"
  progress_log="${TARGET}/spdd/memory/entries/progress.md"
  status_date="$(sdlc_timestamp_iso)"
  milestone_number="$(_milestone_number_from_path "${MILESTONE}" || true)"
  milestone_frontmatter_id="milestone-${milestone_number:-1}"

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would create ${work_id} from milestone item: ${title}"
    echo "[dry-run] would write ${canvas_path}"
    echo "[dry-run] would write ${milestone_requirement_path}"
    echo "[dry-run] would append ${progress_log}"
    echo "[dry-run] would update ${milestone_rel}"
    echo "${work_id}"
    return
  fi

  mkdir -p "${TARGET}/spdd/canvas" "${requirement_parent}" "${TARGET}/spdd/memory/entries"

  cat > "${canvas_path}" <<EOF
# REASONS Canvas: ${work_id} - ${title}

## Metadata

- Work ID: ${work_id}
- Work Type: ${WORK_TYPE}
- Status: Draft
- Readiness: Needs Analysis
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

  cat > "${milestone_requirement_path}" <<EOF
---
work_id: "${work_id}"
jira_key: ""
jira_epic: ""
jira_type: "Story"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "${milestone_frontmatter_id}"
blocks: []
depends_on: []
related: []
---

# Requirement: ${work_id}

## Summary

${title}

## Source

- Roadmap: ${roadmap_rel}
- Milestone: ${milestone_rel}
- Derived from milestone checklist item

## Scope

### IN SCOPE

- ${title}

### NOT IN SCOPE

- TBD (name deferred Work IDs during \`/sdlc-spdd-analysis\`)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | (none) | — | — |

## Acceptance Criteria

- [ ] Define acceptance criteria before coding.

## Jira

Draft for issue creation — paste the fields below into Jira UI, MCP, or your approved API.
After the issue exists, set **Key** (and matching \`jira_key\` frontmatter) and commit;
\`claim\` auto-links \`jira:<KEY>\` in the team registry.

- Key: TBD
- Issue type: Story
- Summary: ${title}
- Labels: sdlc-spdd
- Components:

### Description

${title}

Derived from ${milestone_rel}.

### Acceptance criteria (Given/When/Then)

- Given ... When ... Then ...

## Next Step

Run:

    /sdlc-spdd-analysis @${milestone_requirement_rel}
    /sdlc-spdd-plan @${milestone_requirement_rel} @${roadmap_rel} @${milestone_rel}
EOF

  if [[ ! -f "${progress_log}" ]]; then
    printf '# Progress Entries\n\n' > "${progress_log}"
  fi
  {
    echo ""
    echo "## ${work_id}"
    echo ""
    echo "- ${status_date}: Created from milestone item in ${milestone_rel}."
  } >> "${progress_log}"

  append_milestone_map_header
  echo "| ${work_id} | spdd/canvas/${work_id}.md | ${milestone_requirement_rel} | Draft | Created from milestone item |" >> "${MILESTONE}"

  echo "Created ${work_id}"
  echo "  ${canvas_path}"
  echo "  ${milestone_requirement_path}"
  echo "  ${progress_log} (appended)"
  echo "${work_id}"
}

created_work_ids=()
for item in "${items[@]}"; do
  while IFS= read -r line; do
    if [[ "${line}" =~ ^[A-Z]+-[0-9]{3}- ]]; then
      created_work_ids+=("${line}")
    fi
  done < <(create_work "${item}")
done

if ((${#created_work_ids[@]} > 0)); then
  echo
  echo "Next SPDD prompts (see docs/sdlc-spdd/spdd-prompt-standard.md):"
  for work_id in "${created_work_ids[@]}"; do
    req_ref="@${requirement_parent_rel}/${work_id}.md"
    echo
    echo "  ${work_id}:"
    echo "    /sdlc-spdd-analysis ${req_ref}"
    echo "    ./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id ${work_id}"
    if [[ -f "${TARGET}/${roadmap_rel}" ]]; then
      echo "    /sdlc-spdd-plan @spdd/analysis/${work_id}-analysis.md @${roadmap_rel} @${milestone_rel}"
    else
      echo "    /sdlc-spdd-plan @spdd/analysis/${work_id}-analysis.md @${milestone_rel}"
    fi
    echo "    /sdlc-spdd-architect @spdd/canvas/${work_id}.md"
  done
fi
