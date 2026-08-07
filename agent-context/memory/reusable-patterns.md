# Reusable Patterns

Capture patterns that worked well and should be reused.

## Planning

- Break operations into task-sized steps with explicit files and tests.
- Record assumptions in the canvas instead of hiding them in code comments.

## Review

- Compare changed files directly against canvas Operations and Safeguards.
- Prefer review reports in both feature workspace and `spdd/reviews/`.

## Sync

- Reconcile feature workspace canvas and canonical `spdd/canvas` copy after major changes.

## Guide fork absorption

- Classify fork deltas into layers (SPDD-coupled package, Embabel-general ingest/ops,
  version pins, Cursor-only env) before proposing upstream PRs.
- Prefer small upstreamable slices (e.g. git-incremental directory ingest) over one
  giant fork PR; keep SPDD markdown conventions on `jmjava/guide`.
