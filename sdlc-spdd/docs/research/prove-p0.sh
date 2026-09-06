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

CHECKER="${HOME_DIR}/docs/research/check_p0_artifacts.py"

run_checker() {
  local id="$1"
  if python3 "${CHECKER}" --work-id "${id}"; then
    ok "structured checker ${id}"
  else
    err "structured checker ${id} failed"
  fi
}

prove_doc001() {
  echo "== Prove DOC-001 =="
  need_file "sdlc-spdd/docs/research/research-questions-and-constructs.md"
  need_file "sdlc-spdd/docs/research/check_p0_artifacts.py"
  need_file "sdlc-spdd/spdd/canvas/DOC-001-research-questions-and-constructs.md"
  need_file "sdlc-spdd/spdd/reviews/DOC-001-research-questions-and-constructs-review.md"
  run_checker DOC-001
}

prove_doc002() {
  echo "== Prove DOC-002 =="
  need_file "sdlc-spdd/docs/research/related-work-and-novelty.md"
  need_file "sdlc-spdd/docs/research/check_p0_artifacts.py"
  need_file "sdlc-spdd/spdd/canvas/DOC-002-related-work-map.md"
  need_file "sdlc-spdd/spdd/reviews/DOC-002-related-work-map-review.md"
  run_checker DOC-002
}

prove_test001() {
  echo "== Prove TEST-001 =="
  need_file "sdlc-spdd/docs/research/evaluation-protocol.md"
  need_file "sdlc-spdd/docs/research/check_p0_artifacts.py"
  need_file "sdlc-spdd/spdd/canvas/TEST-001-evaluation-protocol.md"
  need_file "sdlc-spdd/spdd/reviews/TEST-001-evaluation-protocol-review.md"
  run_checker TEST-001
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
