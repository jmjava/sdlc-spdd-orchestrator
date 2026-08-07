# Known Pitfalls

Document project-specific mistakes to avoid in future agent runs.

## General

- Do not skip architect review before coding.
- Do not implement multiple canvas operations in one coding session.
- Do not let canvas drift without running sync.

## Guide / Embabel absorption

- **Never** open a PR, push, or merge to `embabel/guide`. Pull/fetch into
  `jmjava/guide` only. (Always-on agent rule; see `.cursor/rules`.)
- Do not treat Cursor Cloud Agent `.cursor/environment.json` (or dual-repo install
  scripts) as something to contribute to Embabel.
- Do not rename `spdd_*` MCP tools into a “generic” graph API without a separate FEAT
  and an explicit human decision.
- When inventorying `jmjava/guide` vs `embabel/guide`, record **pin** and **tip**
  diffs for fork maintainability — not as an Embabel PR packing list.
- Ignore stale SPIKE-003 / FEAT-013 text that still says “upstream Layer B to Embabel”.

## Java / Spring Boot

- Avoid putting business logic in controllers.
- Avoid silent dependency upgrades during feature work.
