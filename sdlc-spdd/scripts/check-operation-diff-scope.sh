#!/usr/bin/env bash
# CASP-04 / Kasana I2 — review-time Files: vs git diff path-scope check.
#
# Not part of gate_check(code) and not an ENFORCED_GATES entry. /sdlc-spdd-review
# runs this so extra production paths cannot be Approved / Approved With Notes.
#
# Allow rule (in addition to canvas Files: on selected/completed T##, or all
# T## if none selected):
#   - paths under tests/, engine/tests_unit/, engine/tests_integration/,
#     or engine/tests_e2e/
#   - basename matching test_*.py or *_test.py
#   - the documented exception docs/review.spec.md (not any *.spec.md)
# Paths are repo-relative. Any ".." traversal is rejected.
# Renames/deletes are the names `git diff --name-only` reports.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check-operation-diff-scope.sh --work-id <WORK-ID> [options]
       check-operation-diff-scope.sh --canvas <path> [options]

Compare git changed paths to coded operations' Files: plus allowed test paths.

  --work-id ID     Resolve the REASONS canvas via Project.canvas_path
  --canvas PATH    Canvas file (overrides --work-id)
  --ops T01,T02    Limit Files: to these operations
  --base REF       Also include git diff --name-only <REF>...HEAD
  --root DIR       Repo root for git + canvas resolution (default: cwd)
  --changed PATH   Skip git; pass changed paths (repeatable)
  -h, --help       Show this help

Exit 0 when every changed path is in Files: or an allowed test path.
Exit 1 when extra production paths exist or a path traverses with "..".
Prints extra and allowed lists.

Working-tree collection is `git diff --name-only HEAD` (staged + unstaged
vs HEAD). Hunk-level C-DRIFT inside an allowed file remains a human check.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=""
if [[ -d "${SCRIPT_DIR}/../engine/src/sdlc_engine" ]]; then
  ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
elif [[ -d "${SCRIPT_DIR}/../../engine/src/sdlc_engine" ]]; then
  ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
fi

if [[ -n "${ROOT}" && -f "${ROOT}/scripts/lib/python.sh" ]]; then
  # shellcheck source=lib/python.sh
  source "${ROOT}/scripts/lib/python.sh"
  SDLC_ROOT="${ROOT}"
  resolve_engine_python || exit 1
  PY="${SDLC_PY}"
  export PYTHONPATH="${ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}"
else
  PY="${PYTHON:-python3}"
fi

if [[ $# -eq 0 ]]; then
  usage >&2
  exit 2
fi

for arg in "$@"; do
  case "${arg}" in
    -h|--help) usage; exit 0 ;;
  esac
done

# Invoke the function directly so `python -m sdlc_engine.canvas` does not
# re-exec a module already imported via sdlc_engine.__init__ → workflow.
exec "${PY}" -c "from sdlc_engine.canvas import check_diff_scope_main; raise SystemExit(check_diff_scope_main())" "$@"
