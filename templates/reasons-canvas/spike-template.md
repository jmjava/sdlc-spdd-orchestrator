# REASONS Canvas: <WORK-ID> - <Work Name>

## Metadata

- Work ID:
- Work Type: Spike
- Status: Draft
- Readiness: Needs Analysis
- Created:
- Updated:
- Owner:
- Target Project:
- Stack:
- Source System:
- Source Issue:
- Source URL:
- Docs URL:
- Roadmap:
- Milestone:
- Related PR:

## R - Requirements

### User Goal

Describe the question or uncertainty to investigate.

### Business / Product Goal

Describe why the answer matters for future work.

### Acceptance Criteria

- [ ] Question answered with evidence
- [ ] Recommendation documented
- [ ] Follow-up work identified if needed

### Non-Goals

- Production-ready implementation
- Full feature delivery

### Assumptions

- Assumption 1

### Open Questions

- Primary question to answer

## E - Entities

### Systems / Tools To Evaluate

- Tool or approach 1
- Tool or approach 2

### Files Likely Touched

- Prototype or experiment paths only

## A - Approach

### Proposed Approach

Describe experiment design and time box.

### Alternatives Considered

1. Alternative 1

### Trade-Offs

- Trade-off 1

### Risks

- Spike scope creep into production code

### Failure Modes

- Inconclusive results without next steps

## S - Structure

### Artifacts To Produce

- Notes, prototype, benchmark results

### Documentation Structure

Spike summary and recommendation.

## O - Operations

### T01 - Define Experiment

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

### T02 - Run Experiment

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

### T03 - Document Recommendation

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

## V - Verification (freeform agent probes)

Optional. Freeform checks to verify the research question, inventory, or
environment without advancing a spike Operation (`T##`).

### How to use

1. State the question; run the probe; append **Probe log** (newest last).
2. Longer transcripts: `spdd/tasks/<WORK-ID>-agent-probes.md`.
3. Intent change → update Requirements / recommendation before more work.

### Suggested probes

| ID | Probe | When | Pass looks like |
|----|-------|------|-----------------|
| V01 | Re-diff fork tip vs upstream | Mid-spike / before recommend | Counts match research table |
| V02 | Dual-repo orientation (paths, branches, pins) | Cloud / dual-env sessions | Agent can name active Work ID + both checkouts |

### Probe log

| When | Probe | Result | Notes |
|------|-------|--------|-------|
| | | | |

## N - Norms

### General

- Time-box the spike.
- Do not merge throwaway code into production paths without a follow-up feature.
- Document findings clearly for future agents.
- Freeform probes (section V) may run anytime; they do not count as a coding
  Operation and must not silently expand scope.

## S - Safeguards

- Do not change production behavior without a separate feature canvas.
- Do not add permanent dependencies from spike code without review.
- Do not implement behavior changes until this canvas is updated with `/sdlc-spdd-prompt-update`.
- Do not let implementation drift from this canvas without running `/sdlc-spdd-sync`.

## Review Checklist

- [ ] Question answered
- [ ] Recommendation clear
- [ ] Follow-up tasks identified
- [ ] Spike artifacts isolated or removed

## Sync Notes

Use this section to track changes between original plan and final implementation.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
