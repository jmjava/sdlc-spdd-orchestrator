#!/usr/bin/env bash
# Compose segments (audio + video via ffmpeg).
# Wraps: docgen compose
set -euo pipefail
DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DEMOS_DIR/../.." && pwd)"
for _venv in "$DEMOS_DIR/.venv" "$REPO_ROOT/.venv"; do
    [ -f "$_venv/bin/activate" ] && { source "$_venv/bin/activate"; break; }
done
exec docgen --config "$DEMOS_DIR/docgen.yaml" compose "$@"
