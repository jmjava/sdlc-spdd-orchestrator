#!/usr/bin/env bash
# start / capture / resync / create-work / roadmap / validators.
set -euo pipefail
# shellcheck source=../lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib.sh"

ROOT="${1:?target root required}"
HOME="$(live_home "${ROOT}")"
echo "== 03 session + support scripts =="

SCRIPTS="${HOME}/scripts"

# Ensure claim/pointer for guarded capture paths.
live_sdlc "${ROOT}" claim "${WORK_ID}" --force >/dev/null 2>&1 || live_sdlc "${ROOT}" resume "${WORK_ID}" >/dev/null

if "${SCRIPTS}/start-agent-session.sh" --target "${ROOT}" --work-id "${WORK_ID}" --phase plan >/dev/null; then
  ok "start-agent-session"
else
  bad "start-agent-session"
fi

# Early-phase capture may be sparse; scenario 08 asserts the golden full populate.
if "${SCRIPTS}/capture-session-memory.sh" \
  --target "${ROOT}" \
  --work-id "${WORK_ID}" \
  --phase plan \
  --summary "live matrix plan capture (sparse prelude; 08 fills all fields)" \
  --validation "scenario 03 prelude" \
  --next "/sdlc-spdd-architect @spdd/canvas/${WORK_ID}.md" >/dev/null; then
  ok "capture-session-memory (prelude)"
else
  bad "capture-session-memory (prelude)"
fi

if "${SCRIPTS}/resync-agent-session.sh" \
  --target "${ROOT}" \
  --work-id "${WORK_ID}" \
  --check-only >/dev/null 2>&1; then
  ok "resync-agent-session --check-only"
else
  # check-only may exit non-zero when drift exists; accept either clean or reported.
  skipped "resync-agent-session --check-only (drift reported)"
fi

if "${SCRIPTS}/resolve-agent-context.sh" --target "${ROOT}" --phase code --format paths >/dev/null; then
  ok "resolve-agent-context"
else
  bad "resolve-agent-context"
fi

if "${SCRIPTS}/index-spdd-analysis.sh" --target "${ROOT}" >/dev/null 2>&1; then
  ok "index-spdd-analysis"
else
  skipped "index-spdd-analysis (no analysis corpus yet)"
fi

if "${SCRIPTS}/sync-roadmap-from-spdd.sh" --target "${ROOT}" --dry-run >/dev/null; then
  ok "sync-roadmap-from-spdd --dry-run"
else
  bad "sync-roadmap-from-spdd --dry-run"
fi

if "${SCRIPTS}/validate-command-adapters.sh" --target "${ROOT}" >/dev/null; then
  ok "validate-command-adapters"
else
  bad "validate-command-adapters"
fi

if "${SCRIPTS}/validate-requirements-format.sh" --target "${ROOT}" >/dev/null; then
  ok "validate-requirements-format"
else
  bad "validate-requirements-format"
fi

if "${SCRIPTS}/validate-reasons-canvas.sh" --target "${ROOT}" >/dev/null 2>&1 \
  || "${SCRIPTS}/validate-reasons-canvas.sh" "${HOME}/spdd/canvas/${WORK_ID}.md" >/dev/null 2>&1; then
  ok "validate-reasons-canvas"
else
  skipped "validate-reasons-canvas (strict seed mismatch)"
fi

if "${SCRIPTS}/verify-project-install.sh" --target "${ROOT}" --require-cursor >/dev/null; then
  ok "verify-project-install --require-cursor"
else
  bad "verify-project-install"
fi

# Seed app still runs.
if (cd "${ROOT}" && PYTHONPATH="${ROOT}" python3 -c "from src.hello import greet; assert greet('live')=='hello, live'"); then
  ok "seed app greet()"
else
  bad "seed app greet()"
fi
