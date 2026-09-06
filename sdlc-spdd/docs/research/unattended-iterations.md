# Unattended P0 iteration queue

Three successive land-if-green iterations. Do not start the next Work ID until
the previous PR is merged to `main` and `prove-p0.sh` passed for that ID.

| # | Work ID | Branch pattern | Proof | Status |
|---|---------|----------------|-------|--------|
| 1 | DOC-001 (+ SPIKE-004 plan already on PR #219) | `cursor/academic-hardening-review-fdf7` | `./sdlc-spdd/docs/research/prove-p0.sh DOC-001` | merged (#220, `1d1c866`) |
| 2 | DOC-002-related-work-map | `cursor/doc-002-related-work-fdf7` | `python3 -m unittest tests.research.test_p0_artifacts -v` and `prove-p0.sh DOC-002` | in progress |
| 3 | TEST-001-evaluation-protocol | `cursor/test-001-eval-protocol-fdf7` | unittest live TEST-001 checks + `prove-p0.sh TEST-001` | blocked on #2 |

On CI success for the current branch: merge to `main`, fetch, branch the next ID, implement, prove locally, push, open PR, wait CI. Stop the chain on any failed proof or failed CI. Do not start P1 (FEAT-014+) in this queue.
