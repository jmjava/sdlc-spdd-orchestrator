# Threats to validity

## Construct validity

C-DRIFT, C-COMPLY, C-CONTEXT, and C-MEMORY are discussed. The fifth construct is omitted on purpose.

## Internal validity

Dual engine.

## External validity

One lab. Gold: tests/live-consumer/seed/src/hello.py

## Conclusion validity

No study data.

## Reliability

Raters not executed.

## Chat nondeterminism

TEST-001 requires n ≥ 3 or protocol incomplete. Assistant sampling varies.

## Replication checklist

| Item | Freeze how | Location / command |
|------|------------|--------------------|
| Engine commit | `git rev-parse HEAD` | this repo |
| Engine version | `sdlc_engine.__version__` | python import |
| First-slice gold | file SHA | `tests/live-consumer/seed/src/hello.py` |
| Protocol | file SHA | `sdlc-spdd/docs/research/evaluation-protocol.md` |

## Live-consumer harness

The live-consumer matrix **does not prove** C-DRIFT versus unstructured chat.

## What cannot be automated

Hunk mapping cannot be automated.
