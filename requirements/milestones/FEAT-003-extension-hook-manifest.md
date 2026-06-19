# Requirement: FEAT-003-extension-hook-manifest

## Summary

Add a declarative manifest under `agent-context/extensions/` that describes the
framework's extension points — phase extensions, skills, and hooks — so they are
discovered from an explicit, documented contract rather than only by directory
convention. Extensibility refactor: it makes the existing extension mechanism
legible and safe to extend.

## Source

- Roadmap: ROADMAP.md (make it right — extensibility)
- Milestone: milestone-1.md (item 3)

## Motivation

`resolve-agent-context.sh` already loads `agent-context/extensions/_all-agents`,
`*-agent` phase folders, and `extensions/skills/*.md` by convention. The rules live
in script logic, so extending the framework means reverse-engineering that behavior.
A manifest makes the extension points explicit, self-documenting, and validated.

## Acceptance Criteria

- [ ] A manifest file declares the extension points: phase extensions, skills, and hooks (path, phase/trigger, description).
- [ ] `resolve-agent-context.sh` reads the manifest (falling back to current convention) without changing today's resolution results.
- [ ] An example extension demonstrates the manifest end to end.
- [ ] The manifest format is documented for contributors.
- [ ] Existing resolution behavior is unchanged for projects with no manifest (backward compatible).

## Non-Goals

- No new runtime/hook execution engine beyond declaring hook points (keep MVP declarative).
- No change to how skills are authored.

## Next Step

Run:

    /sdlc-spdd-analysis @requirements/milestones/FEAT-003-extension-hook-manifest.md
    /sdlc-spdd-plan @spdd/analysis/FEAT-003-extension-hook-manifest-analysis.md
