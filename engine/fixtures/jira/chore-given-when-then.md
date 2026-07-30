## Summary

Standardize chore Jira sync from requirements

## Description

Requirements markdown is the source of truth. Engine renders Jira descriptions via Jinja → ADF.

## Business value

Operators stop paste-mangling markdown into Jira Cloud.

## Scope in

CHORE requirements under requirements/; create+update; Jinja templates; ADF Cloud + wiki Server fallback

## Scope out

Guide spike; custom field mapping beyond description/summary/labels/components/issuetype

## Acceptance criteria

- Given a chore requirement with Acceptance Criteria
- When the engine pushes or updates the linked Jira issue
- Then the description uses ADF headings and a Given/When/Then bullet list
- Given an existing Jira Key on the requirement
- When acceptance criteria change in the requirement
- Then a subsequent push updates the issue description (not create)

## Traceability

- Work ID: `CHORE-010-example`
- Requirement: `requirements/milestones/CHORE-010-example.md`
