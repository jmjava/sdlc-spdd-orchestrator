#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check-posture-boundary.sh [--target <path>]

Enforce the development-posture boundary: the make-it-work/right/fast posture is
how we develop the orchestrator and must never ship to target projects.

This fails if posture language appears in any surface that installs into a target
project (templates, the docs that ship as docs/sdlc-spdd/, and the agent-context
files that init-project.sh copies). The posture is allowed only in the
orchestrator-internal files ROADMAP.md (repo root) and CONTRIBUTING.md.

If a match is a genuine, non-posture use of the words, append the marker
"posture-boundary-ok" on that line to suppress it.

Examples:
  ./scripts/check-posture-boundary.sh
EOF
}

TARGET="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

cd "${TARGET}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/shipped-docs-boundary.sh
source "${SCRIPT_DIR}/lib/shipped-docs-boundary.sh"

# Posture-specific patterns. The hyphenated forms, the "Kent Beck" attribution,
# and "Delivery posture/stage" are unambiguous; the spaced "make it work/right/fast"
# is included too, with the posture-boundary-ok escape hatch for prose false matches.
PATTERN='make[ -]it[ -](work|right|fast)|[Kk]ent [Bb]eck|[Dd]elivery (posture|stage)'

# Surfaces that install into a target project. Keep this list in sync with
# init-project.sh / upgrade-project.sh.
shipped_files=()

# 1) Everything under templates/ ships (commands, grounding, canvas templates).
if [[ -d templates ]]; then
  while IFS= read -r f; do shipped_files+=("$f"); done \
    < <(find templates -type f \( -name '*.md' -o -name '*.mdc' -o -name '*.prompt.md' \))
fi

# 2) Top-level docs/*.md ship as docs/sdlc-spdd/ (orchestrator-only docs excluded).
for f in docs/*.md; do
  [[ -e "$f" ]] || continue
  is_orchestrator_only_doc "${f}" && continue
  shipped_files+=("$f")
done

# 3) The specific agent-context files init-project.sh copies into targets.
for f in \
  agent-context/memory/project-memory.md \
  agent-context/memory/architecture-decisions.md \
  agent-context/memory/known-pitfalls.md \
  agent-context/memory/reusable-patterns.md \
  agent-context/memory/session-history.md \
  agent-context/memory/phase-index.md \
  agent-context/memory/domain-index.md \
  agent-context/harness/quality-gates.md \
  agent-context/harness/validation-rules.md; do
  [[ -e "$f" ]] && shipped_files+=("$f")
done
for f in agent-context/playbooks/*.md; do
  [[ -e "$f" ]] && shipped_files+=("$f")
done

violations=0
for f in "${shipped_files[@]}"; do
  # Match the pattern, then drop any line carrying the escape-hatch marker.
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    if [[ "$line" == *posture-boundary-ok* ]]; then continue; fi
    echo "POSTURE LEAK: ${f}:${line}"
    violations=$((violations + 1))
  done < <(grep -nE "${PATTERN}" "$f" 2>/dev/null || true)
done

if (( violations > 0 )); then
  echo ""
  echo "Found ${violations} posture reference(s) in shipped surfaces."
  echo "The make-it-work/right/fast posture is orchestrator-internal; keep it in"
  echo "ROADMAP.md and CONTRIBUTING.md only. See CONTRIBUTING.md → 'Boundary: the"
  echo "development posture never ships'."
  exit 1
fi

echo "OK: no development-posture language found in shipped surfaces (${#shipped_files[@]} files scanned)."
