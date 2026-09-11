#!/usr/bin/env bash
set -euo pipefail

# Leftover #15 proving test: the human-ticked harness list must match GATE_LABELS.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

labels_from_gate_labels() {
  PYTHONPATH="${REPO_ROOT}/engine/src" python3 - <<'PY'
from sdlc_engine.phases import GATE_LABELS

print("\n".join(GATE_LABELS.values()))
PY
}

checklist_from() {
  local file="$1"
  python3 - "$file" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
head = text.split("Instruction vs constraint", 1)[0]
for match in re.finditer(r"^- \[[ xX]\] (.+)$", head, re.M):
    print(match.group(1))
PY
}

echo "== test_human_ticked_list_matches_gate_labels =="
expected="$(labels_from_gate_labels)"
for rel in \
  sdlc-spdd/harness/quality-gates.md \
  templates/agent-context/harness/quality-gates.md
do
  got="$(checklist_from "${REPO_ROOT}/${rel}")"
  if [[ "${got}" == "${expected}" ]]; then
    ok "${rel} checkboxes match GATE_LABELS"
  else
    bad "${rel} checkboxes do not match GATE_LABELS"
    printf 'expected:\n%s\n' "${expected}" >&2
    printf 'got:\n%s\n' "${got}" >&2
  fi
done

echo "== test_advisory_markers_present_above_instruction_vs_constraint =="
for rel in \
  sdlc-spdd/harness/quality-gates.md \
  templates/agent-context/harness/quality-gates.md
do
  head="$(python3 - "${REPO_ROOT}/${rel}" <<'PY'
from pathlib import Path
import sys
print(Path(sys.argv[1]).read_text(encoding="utf-8").split("Instruction vs constraint", 1)[0])
PY
)"
  if grep -q 'Architect review completed (advisory)' <<< "${head}" \
    && grep -q 'Operations are task-sized (advisory)' <<< "${head}" \
    && grep -q 'Tests added or updated (advisory)' <<< "${head}" \
    && grep -q 'Canvas synced with implementation (advisory)' <<< "${head}"; then
    ok "${rel} marks architect/ops/tests/canvas advisory above instruction vs constraint"
  else
    bad "${rel} is missing advisory markers above instruction vs constraint"
  fi
done

echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
