# Phase Index

Static context files loaded by SDLC phase (not by code area). Phase-matching
skills under `harness/skills/` load automatically; request on-demand skills with
`#SkillName`. Dynamic, area-keyed context (sessions, decisions, pitfalls,
patterns, metrics) lives in `context-index.md`.

| Phase | Path | Purpose |
|-------|------|---------|
| plan | `ROADMAP.md` | Current focus and milestone map |
| plan | `milestone-*.md` | Active milestone scope |
| plan | `requirements/milestones/` | Requirement sources |
| analysis | `spdd/analysis/` | Fowler Step 3 analysis context (index with `index-spdd-analysis.sh`) |
| analysis | `agent-context/memory/domain-index.md` | Domain keyword → area → artifact lookup |
| analysis | `agent-context/memory/code-areas.md` | Canonical code-area categories |
| analysis | `agent-context/memory/context-index.md` | Area-keyed session, decision, pitfall, pattern, and metric index |
| architect | `harness/validation-rules.md` | Canvas structure + optional readiness vocabulary |
| architect | `agent-context/memory/architecture-decisions.md` | Prior decisions (also in `context-index.md` by area) |
| code | `agent-context/memory/known-pitfalls.md` | Pitfalls (also in `context-index.md` by area) |
| api-test | `spdd/tasks/` | Fowler Step 5 API verification scripts |
| api-test | `harness/quality-gates.md` | API test quality gates |
| review | `harness/quality-gates.md` | Review quality gates |
| prompt-update | `agent-context/memory/prompt-optimization-log.md` | Prompt/canvas change ledger (FEAT-004) |
| retro / sync | `agent-context/memory/reusable-patterns.md` | Patterns (also in `context-index.md` by area) |
| retro / sync | `agent-context/memory/prompt-optimization-log.md` | Ledger outcomes after retro (FEAT-004) |
