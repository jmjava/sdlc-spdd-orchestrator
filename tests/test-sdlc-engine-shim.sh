#!/usr/bin/env bash
# Smoke: scripts/sdlc.sh is a thin dispatcher onto the one Python engine
# (REF-003): no SDLC_ENGINE / SDLC_GATE_ENGINE switch, storage v3 paths only.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/harness.sh
source "${SCRIPT_DIR}/lib/harness.sh"

REPO_ROOT="${HARNESS_REPO_ROOT}"
SDLC="${REPO_ROOT}/scripts/sdlc.sh"
harness_export_engine
PY="${PYTHON:-python3}"

echo "== Python engine importable =="
if PYTHONPATH="${REPO_ROOT}/engine/src" "${PY}" -c 'import sdlc_engine; print(sdlc_engine.__version__)'; then
  ok "import sdlc_engine"
else
  bad "import sdlc_engine"
fi

echo "== sdlc.sh version / next with no engine env =="
ver="$("${SDLC}" version)"
if [[ "${ver}" == 2.0.0a* ]]; then
  ok "sdlc.sh version routes to python engine (${ver})"
else
  bad "unexpected version: ${ver}"
fi

out="$("${SDLC}" next)"
if grep -Fq 'Do now' <<< "${out}" || grep -Fq 'No active Work ID' <<< "${out}"; then
  ok "sdlc.sh next works with no env"
else
  bad "next output unexpected: ${out}"
fi

echo "== removed engine switches exit 2 and say so =="
for var in SDLC_ENGINE SDLC_GATE_ENGINE; do
  for val in shell python auto; do
    rc=0
    err="$(env "${var}=${val}" "${SDLC}" version 2>&1 >/dev/null)" || rc=$?
    if [[ "${rc}" -eq 2 ]] && grep -Fq 'removed' <<< "${err}"; then
      ok "${var}=${val} exits 2 with removed message"
    else
      bad "${var}=${val} rc=${rc}: ${err}"
    fi
  done
done
grep -Fq 'SDLC_ENGINE / SDLC_GATE_ENGINE were removed' <<< "${err}" && ok "removed message names both variables" || bad "message: ${err}"

echo "== dispatcher shape =="
grep -Fq 'python' "${SDLC}" && grep -Fq 'sdlc_engine' "${SDLC}" && ok "sdlc.sh execs python -m sdlc_engine" || bad "sdlc.sh does not target sdlc_engine"
for twin in sdlc-workflow.sh sdlc-team-registry.sh sdlc-pointer.sh; do
  if grep -Fq "${twin}" "${SDLC}"; then
    bad "sdlc.sh still references ${twin}"
  else
    ok "sdlc.sh does not reference ${twin}"
  fi
done
[[ ! -e "${REPO_ROOT}/templates/agent-context/sdlc-workflow.sh" \
  && ! -e "${REPO_ROOT}/templates/agent-context/sdlc-team-registry.sh" \
  && ! -e "${REPO_ROOT}/templates/agent-context/sdlc-pointer.sh" \
  && ! -e "${REPO_ROOT}/scripts/accept-lessons.sh" ]] \
  && ok "bash workflow twins are gone from the repo" || bad "a retired bash twin still exists"

echo "== sdlc.sh --target operates on the target =="
T="$(harness_new_target)"
trap 'rm -rf "${T}"' EXIT
HOME_DIR="$(harness_home "${T}")"
"${SDLC}" --target "${T}" pointer set FEAT-SHIM-001 >/dev/null
ptr="$("${SDLC}" --target "${T}" pointer get)"
if [[ "${ptr}" == "FEAT-SHIM-001" ]] && [[ "$(tr -d '[:space:]' < "${HOME_DIR}/.sdlc/pointer")" == "FEAT-SHIM-001" ]]; then
  ok "--target pointer set/get hits ${HOME_DIR}/.sdlc/pointer"
else
  bad "--target pointer: got '${ptr}'"
fi
ptr="$("${SDLC}" pointer get --target "${T}")"
[[ "${ptr}" == "FEAT-SHIM-001" ]] && ok "trailing --target is honored" || bad "trailing --target: '${ptr}'"
ptr="$("${SDLC}" --root "${T}" pointer get)"
[[ "${ptr}" == "FEAT-SHIM-001" ]] && ok "--root alias is honored" || bad "--root alias: '${ptr}'"
ptr="$("${SDLC}" --target="${T}" pointer get)"
[[ "${ptr}" == "FEAT-SHIM-001" ]] && ok "--target=DIR form is honored" || bad "--target=DIR: '${ptr}'"
if [[ "$("${SDLC}" pointer get)" != "FEAT-SHIM-001" ]]; then
  ok "orchestrator pointer untouched by --target run"
else
  bad "--target run leaked into orchestrator pointer"
fi
"${SDLC}" --target "${T}" pointer reset >/dev/null
rc=0
"${SDLC}" --target "${T}/does-not-exist" version >/dev/null 2>&1 || rc=$?
[[ "${rc}" -eq 2 ]] && ok "--target with missing dir exits 2" || bad "--target missing dir rc=${rc}"

echo "== installed target sdlc.sh is the same dispatcher =="
tver="$(harness_sdlc "${T}" version)"
[[ "${tver}" == "${ver}" ]] && ok "installed sdlc.sh reports same version (${tver})" || bad "installed version ${tver} != ${ver}"
rc=0
SDLC_ENGINE=shell "${HOME_DIR}/scripts/sdlc.sh" version >/dev/null 2>&1 || rc=$?
[[ "${rc}" -eq 2 ]] && ok "installed sdlc.sh also rejects SDLC_ENGINE" || bad "installed sdlc.sh SDLC_ENGINE rc=${rc}"

echo "== local sessions live under sdlc-spdd/.sdlc/local-sessions =="
out="$(SDLC_USER=shim-test "${SDLC}" --target "${T}" local start --name shim-local --intent "offline")"
if grep -Fq 'Started local session LOCAL-' <<< "${out}"; then
  ok "local start creates LOCAL session"
else
  bad "local start unexpected: ${out}"
fi
if find "${HOME_DIR}/.sdlc/local-sessions" -path '*/LOCAL-*/session.json' 2>/dev/null | grep -q .; then
  ok "local session artifacts under sdlc-spdd/.sdlc/local-sessions"
else
  bad "missing local session artifacts under ${HOME_DIR}/.sdlc/local-sessions"
fi
if [[ ! -d "${T}/.sdlc/local-sessions" && ! -d "${T}/_sdlc" ]]; then
  ok "no legacy root .sdlc/_sdlc local-session dirs"
else
  bad "local session written to a legacy root path"
fi
ptr="$("${SDLC}" --target "${T}" pointer get)"
[[ "${ptr}" == LOCAL-* ]] && ok "local start sets pointer (${ptr})" || bad "pointer after local start: '${ptr}'"
out="$("${SDLC}" --target "${T}" local-list)"
grep -Fq 'LOCAL-001-shim-local' <<< "${out}" && ok "local-list hyphen alias routes to local list" || bad "local-list: ${out}"
"${SDLC}" --target "${T}" shelf >/dev/null
[[ -z "$("${SDLC}" --target "${T}" pointer get)" ]] && ok "shelf clears local pointer" || bad "shelf did not clear local pointer"

echo "== work init-from-adf (python engine + sdlc.sh route) =="
mkdir -p "${T}/adf"
cat > "${T}/adf/ORCH-8.adf.json" <<'EOF'
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
out="$(
  "${SDLC}" --target "${T}" work init-from-adf \
    --path "${T}/adf/ORCH-8.adf.json" \
    --work-id FEAT-013-shim-adf-init \
    --no-claim
)"
if grep -Fq 'Created FEAT-013-shim-adf-init' <<< "${out}" \
  && [[ -f "${HOME_DIR}/spdd/canvas/FEAT-013-shim-adf-init.md" ]] \
  && [[ -f "${HOME_DIR}/requirements/milestones/FEAT-013-shim-adf-init.md" ]] \
  && grep -Fq 'Source System: ADF' "${HOME_DIR}/spdd/canvas/FEAT-013-shim-adf-init.md"; then
  ok "work init-from-adf creates canvas + requirement under sdlc-spdd/"
else
  bad "work init-from-adf unexpected: ${out}"
fi
if [[ ! -e "${T}/spdd" && ! -e "${T}/requirements" ]]; then
  ok "init-from-adf wrote no legacy root spdd/ or requirements/"
else
  bad "init-from-adf wrote to a legacy root path"
fi

# Exercise every sdlc.sh alias for this command. Use --dry-run so the
# dispatcher's default root (orchestrator checkout) does not write artifacts.
alias_ok=1
alias_n=0
while IFS=$'\t' read -r alias_line wid; do
  alias_n=$((alias_n + 1))
  # shellcheck disable=SC2086 # intentional word-splitting of alias tokens
  set -- ${alias_line}
  out="$(
    "${SDLC}" "$@" \
      --path "${T}/adf/ORCH-8.adf.json" \
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
  # Ensure dry-run did not write into the orchestrator checkout home.
  if [[ -f "${REPO_ROOT}/sdlc-spdd/spdd/canvas/${wid}.md" || -f "${REPO_ROOT}/spdd/canvas/${wid}.md" ]]; then
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

help_out="$("${SDLC}" work init-from-adf --help 2>&1)"
if grep -Fq -- '--path' <<< "${help_out}"; then
  ok "sdlc.sh work init-from-adf --help available"
else
  bad "sdlc.sh work init-from-adf help missing: ${help_out}"
fi

echo "== db index rebuild via python engine =="
# Seed a tiny work item so rebuild has something to index.
harness_seed_work "${T}" FEAT-000-shim Draft
out="$(
  PYTHONPATH="${REPO_ROOT}/engine/src" \
    "${PY}" -m sdlc_engine --root "${T}" db rebuild
)"
if grep -Fq 'Rebuilt SQLite index' <<< "${out}" && [[ -f "${HOME_DIR}/.sdlc/index.sqlite" ]]; then
  ok "db rebuild creates sdlc-spdd/.sdlc/index.sqlite"
else
  bad "db rebuild unexpected: ${out}"
fi
[[ ! -e "${T}/.sdlc/index.sqlite" ]] && ok "no legacy root .sdlc/index.sqlite" || bad "index written to legacy root .sdlc"

echo "== sdlc.sh --target db rebuild (not next / no pointer) =="
rm -f "${HOME_DIR}/.sdlc/index.sqlite"
out="$("${SDLC}" db rebuild --target "${T}")"
if grep -Fq 'Rebuilt SQLite index' <<< "${out}" && [[ -f "${HOME_DIR}/.sdlc/index.sqlite" ]]; then
  ok "sdlc.sh db rebuild --target hits the project"
else
  bad "sdlc.sh --target db rebuild unexpected: ${out}"
fi
if grep -Fiq 'no active' <<< "${out}"; then
  bad "sdlc.sh db rebuild --target ran next/pointer"
else
  ok "sdlc.sh db rebuild --target does not print pointer next"
fi
rm -f "${HOME_DIR}/.sdlc/index.sqlite"
out="$("${SDLC}" --target "${T}" db-rebuild)"
grep -Fq 'Rebuilt SQLite index' <<< "${out}" && [[ -f "${HOME_DIR}/.sdlc/index.sqlite" ]] \
  && ok "db-rebuild hyphen alias routes to db rebuild" || bad "db-rebuild alias: ${out}"

echo "== python -m sdlc alias =="
out="$(
  PYTHONPATH="${REPO_ROOT}/engine/src" \
    "${PY}" -m sdlc --root "${T}" db path
)"
if grep -Fq "${HOME_DIR}/.sdlc/index.sqlite" <<< "${out}"; then
  ok "python -m sdlc is sdlc_engine (db path under sdlc-spdd/.sdlc)"
else
  bad "python -m sdlc unexpected: ${out}"
fi

harness_finish
