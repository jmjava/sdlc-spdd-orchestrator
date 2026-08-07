# Known Pitfalls

Document project-specific mistakes to avoid in future agent runs.

## General

- Do not skip architect review before coding.
- Do not implement multiple canvas operations in one coding session.
- Do not let canvas drift without running sync.

## Guide / Embabel absorption

- Do not treat Cursor Cloud Agent `.cursor/environment.json` (or dual-repo install
  scripts) as Embabel-upstreamable product surface.
- Do not rename `spdd_*` MCP tools into a “generic” graph API without a separate FEAT
  and Embabel-shaped design (schema-agnostic label/id/rel walk).
- When inventorying `jmjava/guide` vs `embabel/guide`, record **pin** and **tip**
  diffs separately — tip may carry ops/docs that must not inflate the upstream slice.

## Java / Spring Boot

- Avoid putting business logic in controllers.
- Avoid silent dependency upgrades during feature work.
