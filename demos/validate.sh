#!/usr/bin/env bash
# Validate recordings: stream presence, A/V drift, narration lint.
# Wraps: docgen validate --pre-push
set -euo pipefail
DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DEMOS_DIR/../.." && pwd)"
for _venv in "$DEMOS_DIR/.venv" "$REPO_ROOT/.venv"; do
    [ -f "$_venv/bin/activate" ] && { source "$_venv/bin/activate"; break; }
done
exec docgen --config "$DEMOS_DIR/docgen.yaml" validate --pre-push
