# Design Decisions

## SDLC owns process, OpenSPDD owns artifacts

SDLC agent roles define lifecycle phases. REASONS Canvas defines the design contract per work item.

## Cursor-first MVP

The first version is templates and scripts, not a compiled CLI or agent runtime.

## Duplicate canvas copies

Feature workspace and `spdd/canvas/` hold the same content in MVP. Sync tooling reconciles drift.

## Safe installation

Scripts never overwrite existing files unless `--force` is passed. `--dry-run` is supported for init.

## Markdown as primary format

All contracts, memory, and commands are inspectable Markdown files.
