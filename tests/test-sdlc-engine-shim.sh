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

echo "== default dispatcher uses mandatory Python engine =="
out="$( "${REPO_ROOT}/scripts/sdlc.sh" version )"
if [[ "${out}" == 2.0.0a* ]]; then
  ok "default routes version to Python engine (${out})"
else
  bad "default Python engine unexpected version: ${out}"
fi

echo "== retired shell engine overrides fail clearly =="
if out="$(SDLC_ENGINE=shell "${REPO_ROOT}/scripts/sdlc.sh" next 2>&1)"; then
  bad "SDLC_ENGINE=shell should fail"
elif grep -Fq 'SDLC_ENGINE=shell is no longer supported' <<< "${out}"; then
  ok "SDLC_ENGINE=shell rejected"
else
  bad "SDLC_ENGINE=shell rejection unclear: ${out}"
fi
if out="$(SDLC_GATE_ENGINE=shell "${REPO_ROOT}/scripts/sdlc.sh" next 2>&1)"; then
  bad "SDLC_GATE_ENGINE=shell should fail"
elif grep -Fq 'SDLC_GATE_ENGINE=shell is no longer supported' <<< "${out}"; then
  ok "SDLC_GATE_ENGINE=shell rejected"
else
  bad "SDLC_GATE_ENGINE=shell rejection unclear: ${out}"
fi

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

echo "== missing Python engine fails with install hint =="
no_engine="${tmp}/no-engine"
mkdir -p "${no_engine}/scripts/lib"
cp "${REPO_ROOT}/scripts/sdlc.sh" "${no_engine}/scripts/sdlc.sh"
cp "${REPO_ROOT}/scripts/lib/python.sh" "${no_engine}/scripts/lib/python.sh"
cat > "${no_engine}/fake-python" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "-c" && "${2:-}" == *"sys.version_info"* ]]; then
  echo "3 12"
  exit 0
fi
exit 1
EOF
chmod +x "${no_engine}/scripts/sdlc.sh" "${no_engine}/fake-python"
if out="$(PYTHON="${no_engine}/fake-python" "${no_engine}/scripts/sdlc.sh" next 2>&1)"; then
  bad "missing sdlc_engine should fail"
elif grep -Fq 'Python engine (sdlc_engine) is required' <<< "${out}" \
  && grep -Fq 'setup-engine-venv.sh' <<< "${out}"; then
  ok "missing engine reports Python 3.12 setup hint"
else
  bad "missing engine hint unclear: ${out}"
fi

echo "== local sessions use Python engine =="
out="$(
  SDLC_USER=shim-test \
    PYTHONPATH="${REPO_ROOT}/engine/src" \
    python3 -m sdlc_engine --root "${tmp}" local start --name shim-local --intent "offline"
)"
if grep -Fq 'Started local session LOCAL-' <<< "${out}"; then
  ok "local start creates LOCAL session"
else
  bad "local start unexpected: ${out}"
fi
if find "${tmp}/sdlc-spdd/.sdlc/local-sessions" -path '*/LOCAL-*/session.json' 2>/dev/null | grep -q .; then
  ok "local session artifacts under .sdlc/local-sessions"
else
  bad "missing local session artifacts"
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
  && [[ -f "${tmp}/sdlc-spdd/spdd/canvas/FEAT-013-shim-adf-init.md" ]] \
  && [[ -f "${tmp}/sdlc-spdd/requirements/milestones/FEAT-013-shim-adf-init.md" ]] \
  && grep -Fq 'Source System: ADF' "${tmp}/sdlc-spdd/spdd/canvas/FEAT-013-shim-adf-init.md"; then
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
  if [[ -f "${REPO_ROOT}/sdlc-spdd/spdd/canvas/${wid}.md" ]]; then
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
mkdir -p "${tmp}/sdlc-spdd/spdd/canvas" "${tmp}/sdlc-spdd/requirements/milestones"
cat > "${tmp}/sdlc-spdd/spdd/canvas/FEAT-000-shim.md" <<'EOF'
# REASONS Canvas: FEAT-000-shim - Shim

## Metadata

- Work ID: FEAT-000-shim
- Status: Draft
- Source Issue:

## Final Status

- Status: Draft
EOF
cp "${tmp}/sdlc-spdd/spdd/canvas/FEAT-000-shim.md" "${tmp}/sdlc-spdd/requirements/milestones/FEAT-000-shim.md"
out="$(
  PYTHONPATH="${REPO_ROOT}/engine/src" \
    python3 -m sdlc_engine --root "${tmp}" db rebuild
)"
if grep -Fq 'Rebuilt SQLite index' <<< "${out}" && [[ -f "${tmp}/sdlc-spdd/.sdlc/index.sqlite" ]]; then
  ok "db rebuild creates .sdlc/index.sqlite"
else
  bad "db rebuild unexpected: ${out}"
fi

echo "== sdlc.sh --target db rebuild (not next / no pointer) =="
rm -f "${tmp}/sdlc-spdd/.sdlc/index.sqlite"
out="$(
  PYTHONPATH="${REPO_ROOT}/engine/src" \
    "${REPO_ROOT}/scripts/sdlc.sh" db rebuild --target "${tmp}"
)"
if grep -Fq 'Rebuilt SQLite index' <<< "${out}" && [[ -f "${tmp}/sdlc-spdd/.sdlc/index.sqlite" ]]; then
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
