#!/usr/bin/env bash
# Referee hermetic gate for the academic-review freeze (DOC-001 §1).
#
# This script proves storage modes 1–2 (git ledger + SQLite) and the Guide
# *client* contract (mocked HTTP). It does NOT prove the Neo4j graph store.
#
# Complete freeze (three storage modes) also requires live Guide+Neo4j:
#
#   SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh
#
# CI job: .github/workflows/test-guide-stack-experimental.yml (guide-neo4j-live).
#
# Hermetic path:
#
#   git clone https://github.com/jmjava/sdlc-spdd-orchestrator.git
#   cd sdlc-spdd-orchestrator
#   git checkout <commit>   # record `git rev-parse HEAD` beside the result
#   ./sdlc-spdd/docs/research/prove-academic-review.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT}"

export PYTHONPATH="${ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}"

fail=0
step() { echo ""; echo "== $*"; }
ok() { echo "PASS: $*"; }
err() { echo "FAIL: $*" >&2; fail=1; }

step "python"
if ! command -v python3 >/dev/null; then
  err "python3 not found"
else
  python3 -c 'import sys; print(sys.version)'
  ok "python3"
fi

step "prove-p0.sh all (DOC-001/002/003, TEST-001)"
if ./sdlc-spdd/docs/research/prove-p0.sh all; then
  ok "prove-p0.sh all"
else
  err "prove-p0.sh all"
fi

step "structured P0 artifact tests"
if python3 -m unittest tests.research.test_p0_artifacts -v; then
  ok "test_p0_artifacts"
else
  err "test_p0_artifacts"
fi

step "TEST-003 C-RETRIEVE hermetic (ledger + SQLite + mocked Guide client)"
if python3 -m unittest tests.research.test_cretrieve -v; then
  ok "test_cretrieve"
else
  err "test_cretrieve"
fi

step "REF-001 gate_check SUT"
if python3 -m unittest tests.research.test_ref001_sut -v; then
  ok "test_ref001_sut"
else
  err "test_ref001_sut"
fi

step "CHORE-003 dogfood ledger"
if python3 -m unittest tests.research.test_chore003_ledger -v; then
  ok "test_chore003_ledger"
else
  err "test_chore003_ledger"
fi

echo
if (( fail > 0 )); then
  echo "Academic-review hermetic proof FAILED"
  echo "Record: git rev-parse HEAD = $(git rev-parse HEAD 2>/dev/null || echo unknown)"
  exit 1
fi
echo "Academic-review hermetic proof PASSED (ledger + SQLite + Guide client)"
echo "Graph mode is NOT proven by this script. Required live:"
echo "  SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh"
echo "Record: git rev-parse HEAD = $(git rev-parse HEAD)"
exit 0
