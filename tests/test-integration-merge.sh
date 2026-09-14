#!/usr/bin/env bash
# End-to-end merge gate: install + workflow CLI + lib/skills/spec checks (sections A–F).
# Storage v3 only: every framework file lives under <target>/sdlc-spdd/ and the
# only workflow engine is Python sdlc_engine behind sdlc-spdd/scripts/sdlc.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/harness.sh
source "${SCRIPT_DIR}/lib/harness.sh"

REPO_ROOT="${HARNESS_REPO_ROOT}"
SETUP="${REPO_ROOT}/scripts/setup-agent-prompts.sh"
UPGRADE="${REPO_ROOT}/scripts/upgrade-project.sh"
VALIDATE="${REPO_ROOT}/scripts/validate-command-adapters.sh"
GEN="${REPO_ROOT}/scripts/generate-command-adapters.sh"
DUPES="${REPO_ROOT}/scripts/verify-script-lib-duplicates.sh"
RESOLVE="${REPO_ROOT}/scripts/resolve-agent-context.sh"
POSTURE="${REPO_ROOT}/scripts/check-posture-boundary.sh"

harness_export_engine
TARGET="$(mktemp -d)"
trap 'rm -rf "${TARGET}"' EXIT
TARGET_HOME="$(harness_home "${TARGET}")"

echo "== A. Orchestrator gates =="
if "${VALIDATE}" >/dev/null; then ok "validate-command-adapters"; else bad "validate-command-adapters"; fi
if "${GEN}" --check >/dev/null; then ok "generate-command-adapters --check"; else bad "generate-command-adapters --check"; fi
if "${DUPES}" >/dev/null; then ok "verify-script-lib-duplicates"; else bad "verify-script-lib-duplicates"; fi
if "${POSTURE}" >/dev/null; then ok "check-posture-boundary"; else bad "check-posture-boundary"; fi

echo "== B. Install --all into throwaway target =="
if "${SETUP}" --target "${TARGET}" --all >/dev/null; then
  ok "setup-agent-prompts --all"
else
  bad "setup-agent-prompts --all"
fi

for cmd in claim shelf advance next team; do
  if [[ -f "${TARGET}/.cursor/commands/sdlc-${cmd}.md" \
     && -f "${TARGET}/.github/prompts/sdlc-${cmd}.prompt.md" \
     && -f "${TARGET}/.claude/commands/sdlc-${cmd}.md" ]]; then
    ok "workflow command installed: ${cmd}"
  else
    bad "missing workflow command: ${cmd}"
  fi
done

if [[ -f "${TARGET_HOME}/scripts/lib/common.sh" \
   && -f "${TARGET_HOME}/scripts/lib/work-id.sh" \
   && -f "${TARGET_HOME}/scripts/lib/skills.sh" \
   && -f "${TARGET_HOME}/harness/skills/bugfix.md" ]]; then
  ok "shared lib + harness/skills installed under sdlc-spdd/"
else
  bad "lib/skills install incomplete"
fi

if [[ -x "${TARGET_HOME}/scripts/sdlc.sh" ]] \
  && grep -Fq 'sdlc_engine' "${TARGET_HOME}/scripts/sdlc.sh"; then
  ok "sdlc.sh dispatcher installed (targets Python engine)"
else
  bad "sdlc.sh dispatcher missing or not the engine dispatcher"
fi

twin_found=0
for twin in sdlc-workflow.sh sdlc-team-registry.sh sdlc-pointer.sh accept-lessons.sh; do
  [[ -e "${TARGET_HOME}/scripts/${twin}" ]] && twin_found=1
done
if [[ "${twin_found}" -eq 0 ]]; then
  ok "no retired bash twins installed"
else
  bad "a retired bash twin was installed"
fi

if [[ ! -e "${TARGET}/spdd" && ! -e "${TARGET}/requirements" \
   && ! -e "${TARGET}/.sdlc" && ! -e "${TARGET}/agent-context" ]]; then
  ok "no legacy root-level spdd/ requirements/ .sdlc/ agent-context/"
else
  bad "install created legacy root-level framework paths"
fi

if "${VALIDATE}" --target "${TARGET}" >/dev/null; then
  ok "target adapter validation"
else
  bad "target adapter validation"
fi

echo "== C. Workflow CLI claim/next/team/shelf/archive =="
harness_seed_work "${TARGET}" DEMO-001-integration-smoke
list_out="$(SDLC_USER="merge-bot" harness_sdlc "${TARGET}" list-work)"
if grep -Fq 'DEMO-001-integration-smoke' <<< "${list_out}"; then
  ok "list-work discovers demo"
else
  bad "list-work missing demo"
fi
if SDLC_USER="merge-bot" harness_sdlc "${TARGET}" claim DEMO-001-integration-smoke >/dev/null; then
  ok "claim succeeds"
else
  bad "claim failed"
fi
if [[ "$(harness_sdlc "${TARGET}" pointer get)" == "DEMO-001-integration-smoke" ]] \
  && [[ -f "${TARGET_HOME}/.sdlc/workflows/DEMO-001-integration-smoke.state" ]]; then
  ok "claim sets sdlc-spdd/.sdlc pointer + workflow state"
else
  bad "pointer/state not under sdlc-spdd/.sdlc"
fi
if grep -Fq '"work_id": "DEMO-001-integration-smoke"' "${TARGET_HOME}/spdd/memory/registry.jsonl" \
  && grep -Fq '"owner": "merge-bot"' "${TARGET_HOME}/spdd/memory/registry.jsonl"; then
  ok "claim appends to sdlc-spdd/spdd/memory/registry.jsonl"
else
  bad "registry event missing"
fi
next_out="$(SDLC_USER="merge-bot" harness_sdlc "${TARGET}" next)"
if grep -Fq 'Do now' <<< "${next_out}"; then
  ok "next is actionable"
else
  bad "next output weak"
fi
status_json="$(harness_sdlc "${TARGET}" status --json | tr -d ' \n')"
if grep -Fq '"pointer":"DEMO-001-integration-smoke"' <<< "${status_json}" \
  && grep -Fq '"active":true' <<< "${status_json}"; then
  ok "status --json reflects claim"
else
  bad "status --json: ${status_json}"
fi
team_out="$(SDLC_USER="merge-bot" harness_sdlc "${TARGET}" team)"
if grep -Fq 'DEMO-001-integration-smoke' <<< "${team_out}"; then
  ok "team shows claim"
else
  bad "team missing claim"
fi
if SDLC_USER="merge-bot" harness_sdlc "${TARGET}" shelf --reason "integration test" >/dev/null; then
  ok "shelf succeeds"
else
  bad "shelf failed"
fi
if [[ -z "$(harness_sdlc "${TARGET}" pointer get)" ]]; then
  ok "shelf clears pointer"
else
  bad "shelf left pointer set"
fi

# Complete + archive path
harness_seed_work "${TARGET}" DEMO-002-done Complete
if harness_sdlc "${TARGET}" archive DEMO-002-done >/dev/null \
  && [[ ! -f "${TARGET_HOME}/spdd/canvas/DEMO-002-done.md" ]]; then
  ok "archive completed demo work"
else
  bad "archive completed demo work"
fi

echo "== D. Upgrade path refreshes managed files =="
rm -f "${TARGET}/.cursor/commands/sdlc-claim.md"
if "${UPGRADE}" --target "${TARGET}" --all >/dev/null \
  && [[ -f "${TARGET}/.cursor/commands/sdlc-claim.md" ]]; then
  ok "upgrade restores missing workflow command"
else
  bad "upgrade did not restore workflow command"
fi
if [[ -f "${TARGET_HOME}/spdd/canvas/DEMO-001-integration-smoke.md" \
   && -f "${TARGET_HOME}/spdd/memory/registry.jsonl" ]]; then
  ok "upgrade preserves project canvas + registry"
else
  bad "upgrade lost project artifacts"
fi

echo "== E. Skills resolve on installed target =="
paths="$("${RESOLVE}" --target "${TARGET}" --phase code --format paths)"
if grep -Fq "harness/skills/bugfix.md" <<< "${paths}"; then
  ok "resolve finds code-phase bugfix skill"
else
  bad "resolve missing bugfix skill on target"
fi

echo "== F. Nested harnesses =="
for t in \
  test-scripts-lib.sh \
  test-resolve-agent-context.sh \
  test-archive-work.sh \
  test-sdlc-pointer.sh \
  test-sdlc-workflow.sh \
  test-sdlc-engine-shim.sh \
  test-upgrade-layout.sh; do
  if [[ ! -f "${REPO_ROOT}/tests/${t}" ]]; then
    bad "nested harness missing: ${t}"
    continue
  fi
  if bash "${REPO_ROOT}/tests/${t}" >/dev/null 2>&1; then
    ok "nested ${t}"
  else
    bad "nested ${t}"
  fi
done

harness_finish && echo "All integration-merge tests passed."
