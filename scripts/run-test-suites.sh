#!/usr/bin/env bash
# Run SDLC engine test suites (3-package layout).
#
#   ./scripts/run-test-suites.sh preflight [unit|integration|e2e|all] [--guide]
#   ./scripts/run-test-suites.sh unit [--lf] [--force] [-- clean-stale]
#   ./scripts/run-test-suites.sh unit -- engine/tests_unit/foo.py::test_bar
#   ./scripts/run-test-suites.sh integration
#   ./scripts/run-test-suites.sh e2e [--guide]
#   ./scripts/run-test-suites.sh all [--from integration] [--force] [--guide]
#
# Requires .venv from ./scripts/setup-engine-venv.sh (--e2e for suite 3).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/test-preflight.sh
source "${ROOT}/scripts/lib/test-preflight.sh"
# shellcheck source=scripts/lib/python.sh
source "${ROOT}/scripts/lib/python.sh"

VENV="$ROOT/.venv"
BIN="$VENV/bin"
PY="$BIN/python"
PIP="$BIN/pip"
PYTEST="$BIN/pytest"

RUN_GUIDE=0
CLEAN_STALE=0
LAST_FAILED=0
FORCE_RUN=0
FROM_SUITE=""
SUITE="${1:-}"
shift || true

if [[ "$SUITE" == "--state" ]]; then
  test_suite_state_print "${ROOT}"
  exit 0
fi
if [[ "$SUITE" == "--clear-state" ]]; then
  test_suite_state_clear "${ROOT}"
  echo "cleared suite pass state (.sdlc/test-suite-state.tsv)"
  exit 0
fi

PREFLIGHT_TARGET="all"
if [[ "$SUITE" == "preflight" ]]; then
  if [[ $# -gt 0 && "$1" != --* ]]; then
    PREFLIGHT_TARGET="$1"
    shift
  fi
fi

PYTEST_EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --guide) RUN_GUIDE=1; shift ;;
    --clean-stale) CLEAN_STALE=1; shift ;;
    --lf|--last-failed) LAST_FAILED=1; shift ;;
    --force) FORCE_RUN=1; shift ;;
    --from)
      FROM_SUITE="${2:-}"
      [[ -n "${FROM_SUITE}" ]] || { echo "error: --from requires unit|integration|e2e|1|2|3" >&2; exit 2; }
      shift 2
      ;;
    --clear-state)
      test_suite_state_clear "${ROOT}"
      echo "cleared suite pass state (.sdlc/test-suite-state.tsv)"
      exit 0
      ;;
    --state)
      test_suite_state_print "${ROOT}"
      exit 0
      ;;
    --help|-h)
      SUITE="--help"
      break
      ;;
    --)
      shift
      PYTEST_EXTRA=("$@")
      break
      ;;
    *)
      echo "Unknown option: $1 (try --help)" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$SUITE" || "$SUITE" == "--help" || "$SUITE" == "-h" ]]; then
  sed -n '1,18p' "$0"
  cat <<'EOF'

Options:
  --lf, --last-failed   Re-run only tests that failed last time (per-suite cache)
  --from SUITE         With 'all', skip earlier suites (unit|integration|e2e or 1|2|3)
  --force              Re-run even if suite already passed at current commit
  --clean-stale        Kill hung curl /sse and pytest on removed engine/tests/
  --clear-state        Forget green-suite markers for this repo
  --state              Show which suites are green at HEAD
  --                   Pass remaining args to pytest (single test / file)

Examples:
  ./scripts/run-test-suites.sh unit --lf
  ./scripts/run-test-suites.sh unit -- engine/tests_unit/test_workflow.py::test_foo
  ./scripts/run-test-suites.sh all --from integration
EOF
  exit 0
fi

if [[ "$SUITE" == "preflight" ]]; then
  resolve_engine_python || PY="$(pick_bootstrap_python)"
  [[ -n "${PY:-}" ]] || PY="${SDLC_PY:-}"
  test_preflight_print "${PREFLIGHT_TARGET}"
  test_preflight_suite_layout "${ROOT}" || exit 1
  test_preflight_python "${SDLC_PY:-${PY}}" || exit 1
  test_preflight_warn_stale_jobs || true
  test_suite_state_print "${ROOT}" || true
  case "${PREFLIGHT_TARGET}" in
    e2e|3|all) test_preflight_playwright "${PY}"; test_preflight_gh_e2e ;;
  esac
  if [[ "$RUN_GUIDE" == "1" ]] || [[ "${PREFLIGHT_TARGET}" == "all" && "${RUN_GUIDE}" == "1" ]]; then
    test_preflight_guide_stack || exit 1
  fi
  echo "preflight: ready"
  exit 0
fi

if [[ ! -x "$PY" ]]; then
  echo "error: $VENV not found — run ./scripts/setup-engine-venv.sh --e2e (requires Python 3.12)" >&2
  exit 1
fi
if ! test_preflight_python "$PY"; then
  echo "hint: sudo apt install python3.12 python3.12-venv && ./scripts/setup-engine-venv.sh --e2e" >&2
  exit 1
fi

cd "$ROOT"
export SDLC_ENGINE=python
export PYTHONPATH="$ROOT/engine/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ "$CLEAN_STALE" == "1" ]]; then
  test_preflight_kill_stale
fi

echo "== preflight (auto before suite run) =="
test_preflight_print "${SUITE}"
test_preflight_suite_layout "${ROOT}" || exit 1
if test_preflight_warn_stale_jobs; then
  echo "hint: re-run with --clean-stale or kill stale jobs above" >&2
  if pgrep -f "pytest.*engine/tests[^_]" >/dev/null 2>&1; then
    echo "preflight FAIL: stale pytest on removed engine/tests/ — run: $0 ${SUITE} --clean-stale" >&2
    exit 1
  fi
fi
case "${SUITE}" in
  e2e|3|all)
    test_preflight_playwright "$PY"
    test_preflight_gh_e2e
    if [[ "$RUN_GUIDE" == "1" ]]; then
      test_preflight_guide_stack || exit 1
    fi
    ;;
esac

SKIP_GREEN=0
case "${SUITE}" in
  all) SKIP_GREEN=1 ;;
esac

step() {
  echo ""
  echo "== suite $*"
}

skip_suite() {
  echo "SKIP: $1 (green at HEAD — use --force to re-run)"
}

should_run_suite() {
  local name="$1"
  if [[ "${SUITE}" == "all" && -n "${FROM_SUITE}" ]]; then
    case "${FROM_SUITE}" in
      integration|2)
        [[ "${name}" == "unit" ]] && return 1
        ;;
      e2e|3)
        [[ "${name}" == "unit" || "${name}" == "integration" ]] && return 1
        ;;
      unit|1) ;;
      *)
        echo "error: unknown --from '${FROM_SUITE}' (use unit|integration|e2e)" >&2
        exit 2
        ;;
    esac
  fi
  if [[ "${SKIP_GREEN}" == "1" ]] && ! test_suite_state_should_run "${ROOT}" "${name}" "${FORCE_RUN}"; then
    skip_suite "${name}"
    return 1
  fi
  return 0
}

pytest_suite() {
  local cache_key="$1"
  shift
  local cache_path="${ROOT}/.sdlc/pytest-cache/${cache_key}"
  mkdir -p "${cache_path}"
  local -a args=(-o "cache_dir=${cache_path}")
  if [[ "${LAST_FAILED}" == "1" ]]; then
    args+=(--lf)
  fi
  args+=("$@")
  if [[ ${#PYTEST_EXTRA[@]} -gt 0 ]]; then
    args+=("${PYTEST_EXTRA[@]}")
  fi
  "$PYTEST" "${args[@]}"
}

run_unit() {
  should_run_suite unit || return 0
  step "1 — unit (engine/tests_unit)"
  pytest_suite unit -q engine/tests_unit
  test_suite_state_mark "${ROOT}" unit
}

run_integration() {
  should_run_suite integration || return 0
  step "2 — local integration (engine/tests_integration + installer runtime cov)"
  "$PIP" install -q -e "./engine[dev,viewer]"
  pytest_suite integration -q \
    engine/tests_integration \
    engine/tests_unit/test_installer_runtime_units.py \
    engine/tests_unit/test_installer_templates_api.py \
    engine/tests_unit/test_vue3_console_serve.py \
    --cov=sdlc_engine.installer \
    --cov-report=term-missing:skip-covered \
    --cov-fail-under=90
  test_suite_state_mark "${ROOT}" integration
}

run_e2e() {
  should_run_suite e2e || return 0
  step "3 — e2e integration (engine/tests_e2e)"
  test_preflight_playwright "$PY"
  test_preflight_gh_e2e
  "$PIP" install -q -e "./engine[dev,viewer-e2e]"
  if ! "$PY" -m playwright install --dry-run chromium 2>/dev/null | grep -q "is already installed"; then
    echo "Installing Playwright Chromium (one-time)..."
    "$PY" -m playwright install chromium
  fi
  if [[ -n "${GH_TOKEN:-}${GITHUB_TOKEN:-}" ]] || { command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; }; then
    export SDLC_GITHUB_INTEGRATION=1
    export SDLC_GITHUB_ISSUE_CREATE="${SDLC_GITHUB_ISSUE_CREATE:-1}"
    export SDLC_GITHUB_REPO="${SDLC_GITHUB_REPO:-jmjava/sdlc-spdd-orchestrator}"
  fi
  if [[ "$RUN_GUIDE" == "1" ]]; then
    if test_preflight_guide_health "${GUIDE_PORT:-21337}"; then
      echo "Guide already healthy — boot skipped inside test-guide-stack-live.sh"
      export SDLC_GUIDE_ALREADY_UP=1
    else
      test_preflight_guide_stack || exit 1
    fi
    export SDLC_GUIDE_STACK_LIVE=1
    export GUIDE_HOME="${GUIDE_HOME:-$HOME/github/jmjava/orch-guide}"
    export GUIDE_GIT_REF="${GUIDE_GIT_REF:-sdlc-spdd-projection-v2}"
    ./tests/test-guide-stack-live.sh
  fi
  if [[ ${#PYTEST_EXTRA[@]} -gt 0 ]]; then
    pytest_suite e2e -q "${PYTEST_EXTRA[@]}" --screenshot=only-on-failure
  else
    pytest_suite e2e -q \
      engine/tests_e2e/test_viewer_playwright.py \
      engine/tests_e2e/test_vue3_console_playwright.py \
      engine/tests_e2e/test_issues_github_integration.py \
      --screenshot=only-on-failure
  fi
  test_suite_state_mark "${ROOT}" e2e
}

case "$SUITE" in
  unit|1) run_unit ;;
  integration|2) run_integration ;;
  e2e|3) run_e2e ;;
  all)
    run_unit
    run_integration
    run_e2e
    ;;
  *)
    echo "unknown suite: $SUITE (use preflight, unit, integration, e2e, or all)" >&2
    exit 2
    ;;
esac

echo ""
echo "PASS: suite ${SUITE} complete"
