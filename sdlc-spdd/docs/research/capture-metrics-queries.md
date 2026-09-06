# Capture metrics queries (FEAT-015)

**Work ID:** FEAT-015-first-class-metrics  
**Construct spec:** [DOC-001](research-questions-and-constructs.md)

Process metrics are a structured `metrics` object on ledger records (schema 2).
`sdlc-engine context metrics` reads **only** that object. Body tags such as
`Metrics: rework=2` are a human-readable copy and are **not** the query source.

Ledger kinds stay `decision|pitfall|pattern|session|analysis`. This Work ID does
not restore `kind=metric`. SQLite `lessons` columns are unchanged; JSONL is the
system of record.

```bash
sdlc-engine context persist-lesson --kind session --work-id WID --phase code \
  --body "summary" --readiness "Ready For Coding" --review-result pass \
  --rework 2 --context-files 15 --validate-cycles 1 --review-cycles 1

sdlc-engine context metrics --construct C-REWORK --work-id WID
```

Capture script flags write the same object:

```bash
./scripts/capture-session-memory.sh --target . --work-id WID --phase code \
  --summary "..." --readiness "Ready For Coding" --review-result pass \
  --rework 2 --context-files 15 --validate-cycles 1 --review-cycles 1
```

## Queries per capture construct

| Construct | CLI | Fields | What the JSON answers |
|-----------|-----|--------|------------------------|
| **C-COMPLY** | `--construct C-COMPLY` | `readiness`, `review_result` | Counts of structured readiness / review-result by phase |
| **C-CONTEXT** | `--construct C-CONTEXT` | `context_files` | ContextLoad (self-reported file count) by phase |
| **C-REWORK** | `--construct C-REWORK` | `rework`, `validate_cycles`, `review_cycles` | Rework by phase (`by_phase.<phase>.rework_sum`) |
| **C-MEMORY** | `--construct C-MEMORY` | same as C-REWORK | Follow-on rework (RQ4 uses C-REWORK on session 2) |

Omit `--construct` to return all four capture constructs.

## Not capture-metric constructs

| Construct | CLI result | Where it is measured |
|-----------|------------|----------------------|
| **C-DRIFT** | `source: not_capture_metrics`, empty rows | FEAT-016 Files mapping + human hunk remainder |
| **C-PORT** | `source: not_capture_metrics`, empty rows | TEST-002 assistant comparison |

## Proxy weakness (unchanged)

Flags are self-reported. Omitted flags mean the measure is undefined for that
session — the query skips records that lack the construct's fields. `--context-files`
does not prove what the model attended to.
