#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=lib/shipped-docs-boundary.sh
source "${SCRIPT_DIR}/lib/shipped-docs-boundary.sh"

usage() {
  cat <<'EOF'
Usage: verify-docgen-dev-boundary.sh [--smoke-install]

Enforce that docgen / narrated-demo work stays orchestrator-internal and does not
ship to target projects via init-project.sh or shipped docs/templates.

Checks:
  - Regenerable docgen outputs are gitignored and not tracked in git
  - Shipped surfaces (templates, docs/sdlc-spdd sources, copied agent-context)
    contain no docgen dev references
  - init-project.sh / upgrade-project.sh do not copy docs/demos/ or docgen scripts
  - Optional --smoke-install: dry-run init into a temp dir and assert no docgen paths

Examples:
  ./scripts/verify-docgen-dev-boundary.sh
  ./scripts/verify-docgen-dev-boundary.sh --smoke-install
EOF
}

SMOKE_INSTALL=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke-install) SMOKE_INSTALL=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

cd "${REPO_ROOT}"

violations=0
note_fail() {
  echo "DOCGEN DEV LEAK: $*"
  violations=$((violations + 1))
}

# Patterns that must not appear in surfaces installed into target projects.
# Append "docgen-dev-boundary-ok" on a line to suppress a genuine false positive.
DOCGEN_PATTERN='docs/demos|setup-docgen-venv|docgen-engine\.path|docgen\.yaml|--config docgen|documentation-generator'

# --- 1) Regenerable outputs must stay out of git --------------------------------

REGENERABLE_PATHS=(
  docs/demos/audio
  docs/demos/animations/media
  docs/demos/animations/timing.json
  docs/demos/media
  docs/demos/.docgen-state.json
  docs/demos/recordings
  .venv
  scripts/docgen-engine.path
  .env
)

for path in "${REGENERABLE_PATHS[@]}"; do
  if [[ -n "$(git ls-files -- "${path}" 2>/dev/null || true)" ]]; then
    note_fail "tracked in git (must be gitignored): ${path}"
  elif [[ -e "${path}" ]] && ! git check-ignore -q "${path}" 2>/dev/null; then
    note_fail "exists but is not gitignored: ${path}"
  fi
done

shopt -s nullglob
for mp4 in docs/demos/recordings/*.mp4; do
  if git check-ignore -q "${mp4}" 2>/dev/null; then
    : "ok"
  else
    note_fail "recording not gitignored: ${mp4}"
  fi
done
for mp3 in docs/demos/audio/*.mp3; do
  if ! git check-ignore -q "${mp3}" 2>/dev/null; then
    note_fail "audio not gitignored: ${mp3}"
  fi
done
shopt -u nullglob

# --- 2) Install scripts must not copy docgen bundle ------------------------------

for script in scripts/init-project.sh scripts/upgrade-project.sh; do
  if grep -qE 'docs/demos|setup-docgen-venv' "${script}"; then
    note_fail "${script} references docs/demos or setup-docgen-venv (must not install docgen)"
  fi
done

# --- 3) Shipped surfaces must not mention docgen dev tooling -------------------

shipped_files=()

if [[ -d templates ]]; then
  while IFS= read -r f; do shipped_files+=("$f"); done \
    < <(find templates -type f \( -name '*.md' -o -name '*.mdc' -o -name '*.prompt.md' \))
fi

shipped_docs=()
collect_shipped_doc_paths shipped_docs
shipped_files+=("${shipped_docs[@]}")

for f in \
  agent-context/memory/project-memory.md \
  agent-context/memory/architecture-decisions.md \
  agent-context/memory/known-pitfalls.md \
  agent-context/memory/reusable-patterns.md \
  agent-context/memory/session-history.md \
  agent-context/memory/phase-index.md \
  templates/agent-context/memory/domain-index.md \
  agent-context/harness/quality-gates.md \
  agent-context/harness/validation-rules.md; do
  [[ -e "$f" ]] && shipped_files+=("$f")
done
for f in agent-context/playbooks/*.md; do
  [[ -e "$f" ]] && shipped_files+=("$f")
done

for f in "${shipped_files[@]}"; do
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    if [[ "$line" == *docgen-dev-boundary-ok* ]]; then continue; fi
    note_fail "${f}:${line}"
  done < <(grep -nE "${DOCGEN_PATTERN}" "$f" 2>/dev/null || true)
done

# guide-rag doc must never ship
if ! is_orchestrator_only_doc "docs/guide-rag-research-and-dogfooding.md"; then
  note_fail "guide-rag-research-and-dogfooding.md is not marked orchestrator-only"
fi

# --- 4) Optional smoke install ---------------------------------------------------

if [[ "${SMOKE_INSTALL}" -eq 1 ]]; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp}"' EXIT
  echo "Smoke install (dry-run) into ${tmp}..."
  "${REPO_ROOT}/scripts/init-project.sh" --target "${tmp}" --dry-run >/dev/null

  forbidden=(
    docs/demos
    docs/sdlc-spdd/guide-rag-research-and-dogfooding.md
    scripts/setup-docgen-venv.sh
    scripts/docgen-engine.path
    .venv
  )
  for path in "${forbidden[@]}"; do
    if [[ -e "${tmp}/${path}" ]]; then
      note_fail "smoke install would create forbidden path: ${path}"
    fi
  done

  # Real install to verify absence of docgen paths in target tree.
  rm -rf "${tmp}"
  tmp="$(mktemp -d)"
  "${REPO_ROOT}/scripts/init-project.sh" --target "${tmp}" >/dev/null
  for path in "${forbidden[@]}"; do
    if [[ -e "${tmp}/${path}" ]]; then
      note_fail "install created forbidden path: ${path}"
    fi
  done
  if [[ -d "${tmp}/docs/sdlc-spdd" ]]; then
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      note_fail "installed docs/sdlc-spdd:${line}"
    done < <(grep -rnE "${DOCGEN_PATTERN}" "${tmp}/docs/sdlc-spdd" 2>/dev/null || true)
  fi
  if [[ -d "${tmp}/agent-context/memory" ]]; then
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      note_fail "installed agent-context/memory:${line}"
    done < <(grep -rnE "${DOCGEN_PATTERN}" "${tmp}/agent-context/memory" 2>/dev/null || true)
  fi
  rm -rf "${tmp}"
  trap - EXIT
fi

if (( violations > 0 )); then
  echo ""
  echo "Found ${violations} docgen dev boundary violation(s)."
  echo "Docgen bundle, recordings, audio, and operator docs must stay orchestrator-internal."
  echo "See docs/demos/README.md and CONTRIBUTING.md."
  exit 1
fi

echo "OK: docgen dev boundary intact (${#shipped_files[@]} shipped surfaces scanned)."
