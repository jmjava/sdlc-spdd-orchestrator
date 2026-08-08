# scripts/lib — shared bash helpers

Sourced library files for SDLC-SPDD runtime scripts. Not executed directly.

## Layout

| File | Shipped to targets? | Purpose |
|------|---------------------|---------|
| `common.sh` | yes | Timestamps, target resolve, dry-run mkdir, oneline |
| `paths.sh` | yes | `sdlc_require_lib`, shipped lib manifest |
| `areas.sh` | yes | `normalize_area`, `normalize_token`, `parse_section_bullets` |
| `work-id.sh` | yes | `slugify`, `next_work_number`, `work_type_prefix` |
| `milestone.sh` | yes | `resolve_milestone` (absolute or relative paths) |
| `readiness.sh` | yes | Canvas readiness normalize/extract (FEAT-005) |
| `shipped-docs-boundary.sh` | no | Orchestrator doc install skip list |
| `framework-install.sh` | no | Shared `ensure_dir` for init/upgrade |

## Sourcing convention

**Orchestrator** (`scripts/<script>.sh`):

```bash
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/areas.sh"
```

**Installed target** (`sdlc-spdd/scripts/<script>.sh`):

```bash
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/areas.sh"
```

Same relative path — `init-project.sh` / `upgrade-project.sh` copy `scripts/lib/*.sh`
to `${TARGET}/sdlc-spdd/scripts/lib/`.

## Install

Shipped libs are installed by `init-project.sh` and upgraded by `upgrade-project.sh`
alongside runtime scripts under `sdlc-spdd/scripts/`.

## Verification

Run `./tests/test-scripts-lib.sh` for unit/edge coverage of every shipped and
orchestrator-only lib.

Run `./scripts/verify-script-lib-duplicates.sh` to confirm extracted helpers are not
redefined outside `scripts/lib/`. Included in the integration branch gate list.
