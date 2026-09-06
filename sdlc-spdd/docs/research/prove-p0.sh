#!/usr/bin/env bash
# Machine proof gate for Milestone 2 P0 Work IDs.
# Usage: prove-p0.sh [DOC-001|DOC-002|TEST-001|all]
# Exit 0 only if the named Work ID (or all completed ones requested) passes.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HOME_DIR="${ROOT}/sdlc-spdd"
TARGET="${1:-DOC-001}"
fail=0

err() { echo "FAIL: $*" >&2; fail=1; }
ok() { echo "PASS: $*"; }

need_file() {
  local f="$1"
  if [[ -f "${ROOT}/${f}" ]] || [[ -f "${HOME_DIR}/${f}" ]]; then
    ok "exists ${f}"
  else
    err "missing ${f}"
  fi
}

prove_doc001() {
  echo "== Prove DOC-001 =="
  need_file "sdlc-spdd/docs/research/research-questions-and-constructs.md"
  need_file "sdlc-spdd/spdd/canvas/DOC-001-research-questions-and-constructs.md"
  need_file "sdlc-spdd/spdd/reviews/DOC-001-research-questions-and-constructs-review.md"
  local spec="${HOME_DIR}/docs/research/research-questions-and-constructs.md"
  for token in "RQ1" "RQ5" "C-DRIFT" "C-COMPLY" "C-CONTEXT" "C-MEMORY" "C-PORT" "Claims allowed today"; do
    if grep -Fq "${token}" "${spec}"; then
      ok "spec has ${token}"
    else
      err "spec missing ${token}"
    fi
  done
  if grep -Fq "fixes that" "${ROOT}/README.md"; then
    err "README.md still contains 'fixes that'"
  else
    ok "README.md has no 'fixes that'"
  fi
  if grep -Fq "designed to make that drift" "${ROOT}/README.md"; then
    ok "README design-intent sentence"
  else
    err "README missing design-intent sentence"
  fi
  "${ROOT}/scripts/validate-reasons-canvas.sh" \
    "${HOME_DIR}/spdd/canvas/DOC-001-research-questions-and-constructs.md" >/dev/null
  ok "DOC-001 canvas validates"
}

prove_doc002() {
  echo "== Prove DOC-002 =="
  local doc="${HOME_DIR}/docs/research/related-work-and-novelty.md"
  if [[ ! -f "${doc}" ]]; then
    err "missing sdlc-spdd/docs/research/related-work-and-novelty.md"
    return
  fi
  for token in "Novelty" "Fowler" "SDLC Agents" "Spec Kit" "SWE-agent" "C-DRIFT"; do
    if grep -Fq "${token}" "${doc}"; then
      ok "related-work has ${token}"
    else
      err "related-work missing ${token}"
    fi
  done
  need_file "sdlc-spdd/spdd/canvas/DOC-002-related-work-map.md"
  need_file "sdlc-spdd/spdd/reviews/DOC-002-related-work-map-review.md"
  "${ROOT}/scripts/validate-reasons-canvas.sh" \
    "${HOME_DIR}/spdd/canvas/DOC-002-related-work-map.md" >/dev/null
  ok "DOC-002 canvas validates"
}

prove_test001() {
  echo "== Prove TEST-001 =="
  local doc="${HOME_DIR}/docs/research/evaluation-protocol.md"
  if [[ ! -f "${doc}" ]]; then
    err "missing sdlc-spdd/docs/research/evaluation-protocol.md"
    return
  fi
  for token in "RQ1" "RQ2" "RQ3" "RQ4" "RQ5" "unstructured" "gold task" "Stop rule"; do
    if grep -Fiq "${token}" "${doc}"; then
      ok "protocol has ${token}"
    else
      err "protocol missing ${token}"
    fi
  done
  need_file "sdlc-spdd/spdd/canvas/TEST-001-evaluation-protocol.md"
  need_file "sdlc-spdd/spdd/reviews/TEST-001-evaluation-protocol-review.md"
  "${ROOT}/scripts/validate-reasons-canvas.sh" \
    "${HOME_DIR}/spdd/canvas/TEST-001-evaluation-protocol.md" >/dev/null
  ok "TEST-001 canvas validates"
}

case "${TARGET}" in
  DOC-001) prove_doc001 ;;
  DOC-002) prove_doc002 ;;
  TEST-001) prove_test001 ;;
  all)
    prove_doc001
    prove_doc002
    prove_test001
    ;;
  *)
    echo "Usage: $0 [DOC-001|DOC-002|TEST-001|all]" >&2
    exit 2
    ;;
esac

echo
if (( fail > 0 )); then
  echo "Proof FAILED for ${TARGET}"
  exit 1
fi
echo "Proof PASSED for ${TARGET}"
exit 0
