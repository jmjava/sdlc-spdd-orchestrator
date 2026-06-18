# Phase Index

Static context files loaded by SDLC phase (not by code area). Use this when you
know the phase but not yet which code areas apply. Dynamic, area-keyed context
(sessions, decisions, pitfalls, patterns) lives in `context-index.md`.

| Phase | Path | Purpose |
|-------|------|---------|
| plan | `ROADMAP.md` | Current focus and milestone map |
| plan | `milestone-*.md` | Active milestone scope |
| plan | `requirements/milestones/` | Requirement sources |
| analysis | `spdd/analysis/` | Fowler Step 3 analysis context (index with `index-spdd-analysis.sh`) |
| analysis | `agent-context/memory/domain-index.md` | Domain keyword → area → artifact lookup |
| analysis | `agent-context/memory/code-areas.md` | Canonical code-area categories |
| analysis | `agent-context/memory/context-index.md` | Area-keyed session, decision, pitfall, and pattern index |
| architect | `agent-context/harness/validation-rules.md` | Canvas and structure checks |
| architect | `agent-context/memory/architecture-decisions.md` | Prior decisions (also in `context-index.md` by area) |
| code | `agent-context/playbooks/java-feature-playbook.md` | Java feature workflow |
| code | `agent-context/playbooks/bugfix-playbook.md` | Bugfix workflow |
| code | `agent-context/playbooks/refactor-playbook.md` | Refactor workflow |
| code | `agent-context/memory/known-pitfalls.md` | Pitfalls (also in `context-index.md` by area) |
| api-test | `spdd/tasks/` | Fowler Step 5 API verification scripts |
| api-test | `agent-context/harness/quality-gates.md` | API test quality gates |
| review | `agent-context/playbooks/pr-review-playbook.md` | PR review checklist |
| review | `agent-context/harness/quality-gates.md` | Review quality gates |
| retro / sync | `agent-context/playbooks/session-handoff-playbook.md` | Session handoff |
| retro / sync | `agent-context/memory/reusable-patterns.md` | Patterns (also in `context-index.md` by area) |
