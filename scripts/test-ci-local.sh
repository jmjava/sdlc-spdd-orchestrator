#!/usr/bin/env bash
# Local CI mirror — delegates to ./scripts/run-test-suites.sh (3 suites).
#
#   ./scripts/setup-engine-venv.sh --e2e
#   ./scripts/test-ci-local.sh              # unit + integration + e2e (no Guide stack)
#   ./scripts/test-ci-local.sh --guide      # e2e includes Guide + Neo4j harness
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXTRA=()

for arg in "$@"; do
  case "$arg" in
    --guide) EXTRA+=(--guide) ;;
    --help|-h)
      sed -n '1,8p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg (try --guide)" >&2
      exit 2
      ;;
  esac
done

chmod +x "$ROOT/scripts/run-test-suites.sh"
"$ROOT/scripts/run-test-suites.sh" all "${EXTRA[@]}"

step() { echo ""; echo "== $*"; }
step "CLI smoke via sdlc.sh"
export SDLC_ENGINE=python
"$ROOT/scripts/sdlc.sh" version
"$ROOT/scripts/sdlc.sh" next
"$ROOT/scripts/sdlc.sh" viewer --help

step "shim regression harness"
"$ROOT/tests/test-sdlc-engine-shim.sh"

echo ""
echo "PASS: local CI mirror complete"
