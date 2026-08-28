#!/usr/bin/env bash
# Maven-free stub for orch CI. Prints the one-line gate contract.
# DIF_STUB_EXIT=0|1  DIF_STUB_STATUS=ready|blocked
set -euo pipefail
cmd="${1:-}"
status="${DIF_STUB_STATUS:-ready}"
code="${DIF_STUB_EXIT:-0}"
case "${cmd}" in
  architect|review|fold)
    echo "dif=${status} workId=STUB"
    exit "${code}"
    ;;
  *)
    echo "dif-fold-stub: unknown command ${cmd}" >&2
    exit 2
    ;;
esac
