#!/usr/bin/env bash
# Canvas readiness helpers (FEAT-005). Source from scripts/lib or sdlc-spdd/scripts/lib.

# Canonical readiness tokens. Missing is OK; unknown warns at validation time.
READINESS_CANONICAL=(
  needs-analysis
  needs-clarification
  needs-redesign
  ready-for-coding
  blocked
  reviewed
  complete
)

normalize_readiness() {
  local raw="$1"
  local lower
  lower="$(printf '%s' "${raw}" | tr '[:upper:]' '[:lower:]' | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
  # Drop parenthetical annotations: "Ready For Coding (implemented on integration)"
  lower="$(printf '%s' "${lower}" | sed -E 's/\([^)]*\)//g; s/^[[:space:]]+//; s/[[:space:]]+$//')"
  # Spaces/underscores → hyphens; drop other punctuation (e.g. em dash in "Reviewed — …")
  lower="$(printf '%s' "${lower}" | sed -E 's/[[:space:]_]+/-/g; s/[^a-z0-9-]+/-/g; s/-+/-/g; s/^-|-$//g')"
  case "${lower}" in
    needs-analysis|need-analysis) printf '%s' "needs-analysis" ;;
    needs-clarification|need-clarification) printf '%s' "needs-clarification" ;;
    needs-redesign|need-redesign) printf '%s' "needs-redesign" ;;
    ready-for-coding|ready-for-code) printf '%s' "ready-for-coding" ;;
    ready-for-coding-*) printf '%s' "ready-for-coding" ;;
    blocked) printf '%s' "blocked" ;;
    reviewed) printf '%s' "reviewed" ;;
    reviewed-*) printf '%s' "reviewed" ;;
    complete|done|completed) printf '%s' "complete" ;;
    complete-*) printf '%s' "complete" ;;
    *) printf '%s' "" ;;
  esac
}

extract_readiness_raw() {
  local file="$1"
  local raw=""
  # Optional YAML frontmatter readiness:
  if head -n1 "${file}" | grep -q '^---[[:space:]]*$'; then
    raw="$(awk '
      BEGIN { in_fm=0 }
      NR==1 && /^---[[:space:]]*$/ { in_fm=1; next }
      in_fm && /^---[[:space:]]*$/ { exit }
      in_fm && /^readiness:[[:space:]]*/ {
        sub(/^readiness:[[:space:]]*/, "")
        gsub(/^["'\'']+|["'\'']+$/, "")
        print
        exit
      }
    ' "${file}")"
  fi
  if [[ -z "${raw}" ]]; then
    raw="$(grep -m1 -E '^-[[:space:]]*[Rr]eadiness:[[:space:]]*' "${file}" 2>/dev/null | sed -E 's/^-[[:space:]]*[Rr]eadiness:[[:space:]]*//' || true)"
  fi
  printf '%s' "${raw}"
}

# Returns canonical readiness for a canvas file, or empty if absent/unknown.
canvas_readiness() {
  local file="$1"
  local raw
  [[ -f "${file}" ]] || return 0
  raw="$(extract_readiness_raw "${file}")"
  [[ -n "${raw}" ]] || return 0
  normalize_readiness "${raw}"
}

# True (exit 0) when coding should proceed: ready-for-coding, or readiness absent
# (backward compatible). False when needs-* / blocked.
readiness_allows_coding() {
  local canon="${1:-}"
  case "${canon}" in
    ""|ready-for-coding|reviewed|complete) return 0 ;;
    *) return 1 ;;
  esac
}
