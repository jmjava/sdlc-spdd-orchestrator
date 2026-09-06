# Evaluation protocol

This Work ID does **not collect study data**. Protocol only.

## Baselines

- unstructured chat
- canvas-only
- lifecycle-only
- full SDLC-SPDD

## RQ1 procedure

Measure C-DRIFT on the gold task under unstructured chat vs full SDLC-SPDD.

## RQ2 procedure

Score existence-only vs semantic C-COMPLY on the same sessions.

## RQ3 procedure

Record context files loaded under bulk-read vs per-phase retrieve.

## RQ4 procedure

Two-session follow-on; C-REWORK on session 2. Out of first TEST-002 slice unless included.

## RQ5 procedure

Repeat RQ1/RQ2 on a second assistant if APIs allow; else document single-assistant limitation.

## Gold task

Primary gold files: `examples/spring-boot-order-api/` (must contain Java sources before TEST-002) and canvas `examples/spring-boot-order-api/spdd/canvas/`.

## Rater protocol

Two independent raters; disagreements resolved by a third. Report agreement.

## Nondeterminism plan

Fix model id and temperature; run n≥3 samples per condition; report all runs.

## Stop rule

Stop a session after two repair cycles or 90 minutes, whichever first. Do not start TEST-002 until gold task has real source.

## Current blockers

- Spring Boot example has **no Java sources**.
- Live consumer matrix is Cursor-oriented.
