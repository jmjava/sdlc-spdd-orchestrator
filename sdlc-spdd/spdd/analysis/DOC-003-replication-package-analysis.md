# Analysis: DOC-003 — Threats to validity and replication notes

## Metadata

- Work ID: DOC-003-replication-package
- Date: 2026-09-06
- Depends on: TEST-001, FEAT-015 (merged)

## Scope Lock

### In Scope

- Threats (construct, internal, external, conclusion, reliability) updated from SPIKE-004 using FEAT-014/015/016 instruments
- Replication checklist: commands, versions, gold-task locations
- How TEST-001 handles chat nondeterminism (n≥3 or protocol incomplete)
- What live-consumer proves (engineering) vs does not prove (method)
- Structured checker so a token stub fails

### NOT in Scope

- Collecting study data
- Packaging Guide/Neo4j as required
- IRB / human-subject datasets
- Starting FEAT-017 / TEST-002
- Embabel upstream

## Recommendation

One citable markdown pack plus parser tests. Freeze rules inherit TEST-001 §6; do not invent a second n.
