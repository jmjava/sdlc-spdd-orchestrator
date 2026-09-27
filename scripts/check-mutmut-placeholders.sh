#!/usr/bin/env bash
# Mutation ratchet for sdlc_engine.placeholders.
# mutmut 3 exits 0 when mutants survive. Fail on that output. Do not write a score file.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/engine" || exit 1
rm -rf mutants
run_log="$(mktemp)"
trap 'rm -f "$run_log"' EXIT
mutmut run | tee "$run_log"
if ! grep -E '\([1-9][0-9]* files mutated' "$run_log" >/dev/null; then
  echo "mutmut: placeholders.py was not mutated" >&2
  exit 1
fi
results="$(mutmut results)"
if [[ -n "${results//[[:space:]]/}" ]]; then
  printf '%s\n' "$results" >&2
  echo "mutmut: placeholders.py has mutants that were not killed" >&2
  exit 1
fi
echo "mutmut: placeholders.py mutants were killed"
