# Requirement: FEAT-018-kasana-code-command-overlay

## Summary

`/sdlc-spdd-code` must refuse to mark one approved operation complete until its
validation has run, a failure is reported with the command output and the Norm
or Safeguard it maps to, the same verification failure stops on the second
occurrence, and changed paths stay inside that operation's `Files:` plus
explicitly allowed tests. Extra paths are incomplete work.

PR 355 already stores the exit of the verify command that actually ran.
`gate_check` stays an enter-phase check. This requirement sits on that receipt.

## Acceptance Criteria

- [x] The canonical code-command spec and the generated Cursor, Copilot, and Claude adapters state the four exit checks in the same words.
- [x] Semantic tests fail when any one of those four checks disappears from an adapter.
- [x] Extra paths outside `Files:` and explicitly allowed tests are incomplete work, not a warning.
- [x] The executed verify receipt remains: capture runs `--verify-command` and stores the observed exit. Complete still requires a passing result.
- [x] `WorkflowEngine.gate_check`, `ENFORCED_GATES`, and enter-code semantics are unchanged.
- [x] No model retry loop is added.

## Provenance

- Promoted from local session `LOCAL-001-kasana-code-command-overlay`
- Local title: kasana-code-command-overlay
- Depends on the merged verify receipt in pull request 355

## Jira

- Key: TBD
- Summary: kasana-code-command-overlay

## GitHub

- Number: TBD
- Title: kasana-code-command-overlay
