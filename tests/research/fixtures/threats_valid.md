# Threats to validity

This Work ID does **not collect study data**.

## Construct validity

C-DRIFT uses Files mapping plus a human hunk remainder.
C-COMPLY uses semantic gate minima.
C-CONTEXT uses structured context_files.
C-MEMORY uses C-REWORK on a follow-on.
C-PORT is not adapter-text parity.

## Internal validity

Dual engine is a confound. Use SDLC_ENGINE=python. `--force` invalidates C-COMPLY.

## External validity

n is this repository. First gold is tests/live-consumer/seed/src/hello.py.

## Conclusion validity

CLI green is not a method result. Do not report p-values.

## Reliability

Two raters are specified in TEST-001 and have not been executed.

## Chat nondeterminism

TEST-001 holds gold SHA and model id fixed, allows assistant sampling, and requires n ≥ 3 or **protocol incomplete**.

## Replication checklist

| Item | Freeze how | Location / command |
|------|------------|--------------------|
| Engine commit | `git rev-parse HEAD` | this repo |
| Engine version | `sdlc_engine.__version__` | python import |
| First-slice gold | file SHA | `tests/live-consumer/seed/src/hello.py` |
| Protocol | file SHA | `sdlc-spdd/docs/research/evaluation-protocol.md` |
| Model | vendor model id | record beside numbers |

## Live-consumer harness

The live-consumer matrix **does not prove** C-DRIFT versus unstructured chat. Do not cite it as TEST-002.

## What cannot be automated

Hunk-level C-DRIFT, rater agreement, and assistant sampling cannot be automated.
