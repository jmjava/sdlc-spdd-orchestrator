# SPIKE-086: Eliminate agent-context/features mirrors

GitHub: [#86](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/86)  
Status: **proposal accepted for implementation**

## Decision

Canonical only:

- `requirements/…`  
- `spdd/canvas/…` (+ analysis/review/sync)

`agent-context/features/<WORK-ID>/` is **deprecated**. Tools resolve canvas/requirement from stay-set paths. Upgrade (#80) archives feature dirs under `.sdlc/legacy-export/`.
