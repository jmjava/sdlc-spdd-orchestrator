# Issue closeout after `v2.0.0a6` / #109

Cloud Agent tokens cannot close GitHub issues (HTTP 403). Close these manually
(or with a human-owned token) — they are delivered on `main`.

## Close as done

| Issue | Title | Evidence |
|------:|-------|----------|
| #77 | High-noise dual-repo sessions | Hot sessions + lean stay-set |
| #78 | Persist agent-context outside git | ContextStore + `.sdlc/` |
| #79 | Triple-path context store | `context_store.py` + Persistence tab |
| #80 | Clean upgrade / re-init | `agent_context_upgrade.py` |
| #81 | Define git stay-set | `docs/agent-context-cleanup/STAY-SET.md` |
| #82 | Triple-path feature parity | schema v4 + coverage tests |
| #83 | Lean-git lessons | `spdd/memory/lessons/` |
| #84 | Registry lean encoding | `spdd/memory/registry.jsonl` |
| #85 | Sessions without committing | `.sdlc/sessions/` |
| #86 | Eliminate feature mirrors | verifier lean-first |
| #87 | Git pointer protocol | `pointers.py` |
| #88 | SQLite schema v2+ | schema v4 |
| #90 | Persist fan-out orchestration | Persistence + `CONTEXT_BACKENDS` |
| #91 | Quiet / product-test mode | `quiet.py` / `SDLC_QUIET` |
| #92 | Program issue index | this program |
| #93 | End-state triple projection | orchestrator side shipped |

Release commit on `main` already listed `Closes #…` for the above (`5b8eb3a`);
GitHub did not auto-close them for this integration.

## Close as done (Guide follow-on)

| Issue | Title | Evidence |
|------:|-------|----------|
| #89 | Guide dual-read lean + legacy context-index | [jmjava/guide#7](https://github.com/jmjava/guide/pull/7) on `main`; pin `sdlc-spdd-projection-v2` |

## Keep open

| Issue | Why |
|------:|-----|
| #103 | PR Playback / report — separate feature |

## One-liner for bulk close

```bash
for n in 77 78 79 80 81 82 83 84 85 86 87 88 90 91 92 93; do
  gh issue close "$n" --comment "Delivered in v2.0.0a6 (#109)."
done
```
