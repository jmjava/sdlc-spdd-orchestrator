#!/usr/bin/env bash
# Rebuild visuals and downstream stages after new audio (skips TTS).
# Wraps: docgen rebuild-after-audio
set -euo pipefail
DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DEMOS_DIR/../.." && pwd)"
for _venv in "$DEMOS_DIR/.venv" "$REPO_ROOT/.venv"; do
    [ -f "$_venv/bin/activate" ] && { source "$_venv/bin/activate"; break; }
done
echo "Rebuild after audio (skipping TTS, using existing audio/*.mp3)"
exec docgen --config "$DEMOS_DIR/docgen.yaml" rebuild-after-audio
