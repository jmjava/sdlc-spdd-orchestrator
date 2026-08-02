#!/usr/bin/env bash
# Full pipeline. Default Manim path: animations/specs/*.scene.yaml
# (auto scene-spec-generate when missing; retime thereafter).
# Wraps: docgen generate-all
set -euo pipefail
DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DEMOS_DIR/../.." && pwd)"
for _venv in "$DEMOS_DIR/.venv" "$REPO_ROOT/.venv"; do
    [ -f "$_venv/bin/activate" ] && { source "$_venv/bin/activate"; break; }
done
ARGS=()
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        exec docgen --config "$DEMOS_DIR/docgen.yaml" tts --dry-run
    fi
    ARGS+=("$arg")
done
exec docgen --config "$DEMOS_DIR/docgen.yaml" generate-all "${ARGS[@]}"
