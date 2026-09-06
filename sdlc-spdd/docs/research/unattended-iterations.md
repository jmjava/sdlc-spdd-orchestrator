# Unattended P0 iteration queue

Three successive land-if-green iterations. Do not start the next Work ID until
the previous PR is merged to `main` and `prove-p0.sh` passed for that ID.

| # | Work ID | Branch pattern | Proof | Status |
|---|---------|----------------|-------|--------|
| 1 | DOC-001 (+ SPIKE-004 plan already on PR #219) | `cursor/academic-hardening-review-fdf7` | `./sdlc-spdd/docs/research/prove-p0.sh DOC-001` | merged (#220, `1d1c866`) |
| 2 | DOC-002-related-work-map | `cursor/doc-002-related-work-fdf7` | `python3 -m unittest tests.research.test_p0_artifacts -v` and `prove-p0.sh DOC-002` | merged (#221, `9a6b00a`) |
| 3 | TEST-001-evaluation-protocol | `cursor/test-001-eval-protocol-fdf7` | unittest live TEST-001 checks + `prove-p0.sh TEST-001` | merged (#222, `2529d06`) |

P0 and P1 (through DOC-003) are **Complete**. FEAT-017 (lexical retrieve IR) and TEST-002 (n=1 protocol-incomplete hello slice) are done. **Next action:** CHORE-003 (dogfood ledger — RQ4 retrieve is vacuous while `lessons.jsonl` is empty), then REF-001.
