#!/usr/bin/env bash
# Smoke: scripts/sdlc.sh can delegate to the Python engine.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

echo "== Python engine importable =="
if PYTHONPATH="${REPO_ROOT}/engine/src" python3 -c 'import sdlc_engine; print(sdlc_engine.__version__)'; then
  ok "import sdlc_engine"
else
  bad "import sdlc_engine"
fi

echo "== SDLC_ENGINE=python via sdlc.sh =="
ver="$(SDLC_ENGINE=python "${REPO_ROOT}/scripts/sdlc.sh" version)"
if [[ "${ver}" == 2.0.0a* ]]; then
  ok "sdlc.sh version via python engine (${ver})"
else
  bad "unexpected version: ${ver}"
fi

out="$(SDLC_ENGINE=python "${REPO_ROOT}/scripts/sdlc.sh" next)"
if grep -Fq 'Do now' <<< "${out}" || grep -Fq 'No active Work ID' <<< "${out}"; then
  ok "sdlc.sh next via python engine"
else
  bad "python next output unexpected"
fi

echo "== default remains shell =="
out="$(SDLC_ENGINE=shell "${REPO_ROOT}/scripts/sdlc.sh" next)"
if grep -Fq 'No active Work ID' <<< "${out}" || grep -Fq 'SDLC:' <<< "${out}" || grep -Fq 'resume' <<< "${out}"; then
  ok "shell engine still works"
else
  bad "shell next unexpected"
fi

echo "== local sessions route even when SDLC_ENGINE=shell =="
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT
# Use --root via python engine; sdlc.sh local* always hits python.
out="$(
  SDLC_ENGINE=shell SDLC_USER=shim-test \
    PYTHONPATH="${REPO_ROOT}/engine/src" \
    python3 -m sdlc_engine --root "${tmp}" local start --name shim-local --intent "offline"
)"
if grep -Fq 'Started local session LOCAL-' <<< "${out}"; then
  ok "local start creates LOCAL session"
else
  bad "local start unexpected: ${out}"
fi
if [[ -f "${tmp}/.sdlc/local-sessions/"LOCAL-*/session.json ]]; then
  ok "local session artifacts under .sdlc/local-sessions"
else
  # glob may not expand in [[ -f ]]; check via find
  if find "${tmp}/.sdlc/local-sessions" -name session.json | grep -q .; then
    ok "local session artifacts under .sdlc/local-sessions"
  else
    bad "missing local session artifacts"
  fi
fi

echo "== work init-from-adf (python engine + sdlc.sh route) =="
mkdir -p "${tmp}/adf"
cat > "${tmp}/adf/ORCH-8.adf.json" <<'EOF'
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "heading",
      "attrs": {"level": 1},
      "content": [{"type": "text", "text": "Shim ADF init"}]
    },
    {
      "type": "paragraph",
      "content": [{"type": "text", "text": "Created by shim test"}]
    }
  ]
}
EOF
# Isolated engine create (sdlc.sh pins --root to the orchestrator checkout).
out="$(
  PYTHONPATH="${REPO_ROOT}/engine/src" \
    python3 -m sdlc_engine --root "${tmp}" work init-from-adf \
      --path "${tmp}/adf/ORCH-8.adf.json" \
      --work-id FEAT-013-shim-adf-init \
      --no-claim
)"
if grep -Fq 'Created FEAT-013-shim-adf-init' <<< "${out}" \
  && [[ -f "${tmp}/spdd/canvas/FEAT-013-shim-adf-init.md" ]] \
  && [[ -f "${tmp}/requirements/milestones/FEAT-013-shim-adf-init.md" ]] \
  && grep -Fq 'Source System: ADF' "${tmp}/spdd/canvas/FEAT-013-shim-adf-init.md"; then
  ok "work init-from-adf creates canvas + requirement"
else
  bad "work init-from-adf unexpected: ${out}"
fi

# Exercise every sdlc.sh shell entrypoint for this command. Use --dry-run so the
# wrapper's pinned --root (orchestrator checkout) does not write artifacts.
alias_ok=1
alias_n=0
while IFS=$'\t' read -r alias_line wid; do
  alias_n=$((alias_n + 1))
  # shellcheck disable=SC2086 # intentional word-splitting of alias tokens
  set -- ${alias_line}
  out="$(
    SDLC_ENGINE=shell \
      PYTHONPATH="${REPO_ROOT}/engine/src" \
      "${REPO_ROOT}/scripts/sdlc.sh" "$@" \
        --path "${tmp}/adf/ORCH-8.adf.json" \
        --work-id "${wid}" \
        --no-claim \
        --dry-run 2>&1
  )" || {
    bad "sdlc.sh alias failed: ${alias_line} (${out})"
    alias_ok=0
    continue
  }
  if grep -Fq "[dry-run] would create ${wid}" <<< "${out}"; then
    ok "sdlc.sh alias works: ${alias_line}"
  else
    bad "sdlc.sh alias unexpected output (${alias_line}): ${out}"
    alias_ok=0
  fi
  # Ensure dry-run did not write into the orchestrator checkout.
  if [[ -f "${REPO_ROOT}/spdd/canvas/${wid}.md" ]]; then
    bad "sdlc.sh dry-run wrote canvas for ${wid}"
    alias_ok=0
  fi
done <<'ALIASES'
work init-from-adf	FEAT-013-alias-spaced
work-init-from-adf	FEAT-013-alias-hyphen
init-from-adf	FEAT-013-alias-short
ALIASES
if (( alias_ok == 1 && alias_n == 3 )); then
  ok "all 3 sdlc.sh init-from-adf aliases routed"
fi

help_out="$(
  SDLC_ENGINE=shell \
    PYTHONPATH="${REPO_ROOT}/engine/src" \
    "${REPO_ROOT}/scripts/sdlc.sh" work init-from-adf --help 2>&1
)"
if grep -Fq -- '--path' <<< "${help_out}"; then
  ok "sdlc.sh work init-from-adf --help available"
else
  bad "sdlc.sh work init-from-adf help missing: ${help_out}"
fi

echo "== db index rebuild via python engine =="
# Seed a tiny work item so rebuild has something to index.
mkdir -p "${tmp}/spdd/canvas" "${tmp}/requirements/milestones"
cat > "${tmp}/spdd/canvas/FEAT-000-shim.md" <<'EOF'
# REASONS Canvas: FEAT-000-shim - Shim

## Metadata

- Work ID: FEAT-000-shim
- Status: Draft
- Source Issue:

## Final Status

- Status: Draft
EOF
cp "${tmp}/spdd/canvas/FEAT-000-shim.md" "${tmp}/requirements/milestones/FEAT-000-shim.md"
out="$(
  SDLC_ENGINE=shell \
    PYTHONPATH="${REPO_ROOT}/engine/src" \
    python3 -m sdlc_engine --root "${tmp}" db rebuild
)"
if grep -Fq 'Rebuilt SQLite index' <<< "${out}" && [[ -f "${tmp}/.sdlc/index.sqlite" ]]; then
  ok "db rebuild creates .sdlc/index.sqlite"
else
  bad "db rebuild unexpected: ${out}"
fi

echo "== sdlc.sh --target db rebuild (not next / no pointer) =="
rm -f "${tmp}/.sdlc/index.sqlite"
out="$(
  SDLC_ENGINE=shell \
    PYTHONPATH="${REPO_ROOT}/engine/src" \
    "${REPO_ROOT}/scripts/sdlc.sh" db rebuild --target "${tmp}"
)"
if grep -Fq 'Rebuilt SQLite index' <<< "${out}" && [[ -f "${tmp}/.sdlc/index.sqlite" ]]; then
  ok "sdlc.sh db rebuild --target hits the project"
else
  bad "sdlc.sh --target db rebuild unexpected: ${out}"
fi
if grep -Fiq 'no active' <<< "${out}"; then
  bad "sdlc.sh db rebuild --target ran next/pointer"
else
  ok "sdlc.sh db rebuild --target does not print pointer next"
fi

echo "== python -m sdlc alias =="
out="$(
  PYTHONPATH="${REPO_ROOT}/engine/src" \
    python3 -m sdlc --root "${tmp}" db path
)"
if grep -Fq "${tmp}" <<< "${out}"; then
  ok "python -m sdlc is sdlc_engine"
else
  bad "python -m sdlc unexpected: ${out}"
fi

echo
echo "Results: ${pass} passed, ${fail} failed"
if (( fail > 0 )); then exit 1; fi
