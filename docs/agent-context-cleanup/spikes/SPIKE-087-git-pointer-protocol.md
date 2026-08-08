# SPIKE-087: Path-1 git pointer protocol

GitHub: [#87](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/87)  
Status: **implemented** (`PointerLedger` in `sdlc_engine/pointers.py`, wired into `ContextStore` fan-out per #90)

## Goal

Define lean **git pointers** so path 1 has full feature parity (#82) without committing noisy `agent-context/` runtime files.

Pointers are **small records** that reference:

- stay-set artifacts (requirements, REASONS, lean lessons), and/or  
- product commits that embody accepted work  

They are **not** session transcripts and not mirrors of canvas bodies.

## Record schema (v0)

JSON Lines file (one object per line), stable field names:

```json
{
  "id": "ptr_20260807T230000Z_FEAT-013_lesson_pitfall_1",
  "schema": 1,
  "ts": "2026-08-07T23:00:00Z",
  "work_id": "FEAT-013-guide-git-incremental-upstream",
  "kind": "lesson",
  "subtype": "pitfall",
  "intent": "Never open PRs against embabel/guide",
  "commit_sha": "abc123…",
  "paths": ["spdd/memory/lessons/pitfalls.md"],
  "links": {
    "areas": ["com.embabel.guide.spdd"],
    "lesson_id": "pitfall:FEAT-013-guide-git-incremental-upstream:com.embabel.guide.spdd:capture"
  }
}
```

### `kind` values (parity coverage)

| kind | Purpose |
|------|---------|
| `requirement` | Pointer to requirements stay-set path + commit |
| `reasons` | Pointer to `spdd/canvas/<WORK-ID>.md` revision |
| `lesson` | Accepted decision/pitfall/pattern (#83) |
| `claim` | Registry claim/release event (#84) |
| `resume` | Accepted phase/resume checkpoint (#85) — not hot session |
| `product` | Product-code commit tied to a Work ID / T## |

## Storage location (v0 recommendation)

| Location | Role |
|----------|------|
| `spdd/memory/pointers.jsonl` | **Committed** append-only ledger (lean, reviewable) |
| `.sdlc/pointers-staging.jsonl` | **Gitignored** drafts before accept |

Rationale: a tiny committed JSONL is still git, stays reviewable in PRs, and avoids git-notes tooling gaps in Cloud Agents. Bodies of lessons live in lean stay-set files (#83), not in the pointer line beyond `intent` + ids.

## Write triggers

| Event | Writes staging? | Commits pointer? |
|-------|-----------------|------------------|
| Session start | no | no |
| Capture draft | optional staging | no |
| Retro/sync **accept** lesson | yes → promote | **yes** (append JSONL + lesson stay-set) |
| Claim/release | staging or direct | **yes** when team-visible |
| Product commit with Work ID | optional auto `product` kind | yes if hook enabled (phase 2) |

## Reconstruct (retrieve)

Given `work_id` and/or `area`:

1. Read `spdd/memory/pointers.jsonl` (filter)  
2. Load linked stay-set paths / lesson ids  
3. Merge with SQLite + Guide results in assemble (#90)

Git-alone must answer the #82 matrix from stay-set + this ledger.

## Non-goals (this spike)

- Replacing REASONS/requirements bodies with pointers only  
- Auto-committing every capture metric/session row  
- Implementing fan-out code (see #90)

## Next implementation slice

1. Add `spdd/memory/` stay-set dirs + empty `pointers.jsonl` + README  
2. Gitignore `.sdlc/pointers-staging.jsonl`  
3. Helper: `sdlc_engine/pointers.py` append/list/filter  
4. Wire accept path later with #83/#90  

## Exit criteria for SPIKE-087

- [x] Schema + kinds documented  
- [x] Storage + write triggers documented  
- [x] Reconstruct story for git-alone documented  
- [x] `PointerLedger` implemented (`sdlc_engine/pointers.py`) + `engine/tests/test_pointers.py`  
- [x] Reviewed against #83/#84/#85 before wiring capture fan-out (#90) — fan-out is live in `ContextStore`
