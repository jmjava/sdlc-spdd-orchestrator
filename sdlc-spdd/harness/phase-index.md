# Phase Index

Static context files loaded by SDLC phase (not by code area). Phase-matching
skills under `agent-context/harness/skills/` load automatically; request
on-demand skills with `#SkillName`.

Cross-work memory is **not** listed here — use on-demand retrieval:

```bash
sdlc-engine context retrieve --work-id <ID> [--area A] [--kind K]
sdlc-engine context show <record-id>
```

When Guide is live, augment with `spdd_*` MCP tools. See [docs/storage-v3.md](../../docs/storage-v3.md).

| Phase | Path | Purpose |
|-------|------|---------|
| plan | `ROADMAP.md` | Current focus and milestone map |
| plan | `requirements/milestones/` | Requirement sources |
| analysis | `agent-context/harness/validation-rules.md` | Analysis scope and structure norms |
| architect | `agent-context/harness/validation-rules.md` | Canvas structure + readiness vocabulary |
| architect | `agent-context/harness/quality-gates.md` | Architecture quality gates |
| code | `agent-context/harness/quality-gates.md` | Implementation quality gates |
| api-test | `agent-context/harness/quality-gates.md` | API test quality gates |
| review | `agent-context/harness/quality-gates.md` | Review quality gates |
| retro / sync | `agent-context/harness/quality-gates.md` | Closure quality gates |

Work-id contracts (`spdd/canvas/`, `spdd/analysis/`, reviews, sync) resolve
via `--work-id` on `resolve-agent-context.sh`, not through this table.
