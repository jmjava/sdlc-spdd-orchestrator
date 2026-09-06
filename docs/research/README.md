# Research notes

This folder is **not** a paper. It holds investigation notes that support either product integration or the academic program.

| Document | Kind | Use it when |
|----------|------|-------------|
| [Academic contribution bar (SPIKE-004 analysis)](../../sdlc-spdd/spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md) | Journal-style review of *this* repo as a research project | Raising claims from engineering/hobby to referee-safe |
| [Program plan (SPIKE-004 canvas)](../../sdlc-spdd/spdd/canvas/SPIKE-004-academic-contribution-bar.md) | REASONS canvas for Milestone 2 sequence | What to iterate, in what order |
| [Research questions and constructs (DOC-001)](../../sdlc-spdd/docs/research/research-questions-and-constructs.md) | Frozen RQs + construct spec | Citing C-DRIFT / C-COMPLY / … in later Work IDs |
| [Related-work and novelty (DOC-002)](../../sdlc-spdd/docs/research/related-work-and-novelty.md) | Claim × system matrix | Positioning vs Fowler, SDLC Agents, Spec Kit, agents, classics |
| [Evaluation protocol (TEST-001)](../../sdlc-spdd/docs/research/evaluation-protocol.md) | Method eval protocol (no study data) | TEST-002 slice: gold, raters, baselines, stop rules |
| [P0 structured checker](../../sdlc-spdd/docs/research/check_p0_artifacts.py) | Parser-based gate (not token grep) | `python3 -m unittest tests.research.test_p0_artifacts -v` |
| [P0 proof script](../../sdlc-spdd/docs/research/prove-p0.sh) | Machine gate per Work ID | Run before merging the next P0 item |
| [Milestone 2 task list](../../sdlc-spdd/spdd/tasks/milestone-2-academic-hardening.md) | Iteration backlog | Picking the next Work ID |
| [Jira ADF and requirements sync](jira-adf-and-requirements-sync.md) | Product/integration research | Jira Cloud description payloads |

Until TEST-002 records a comparison, do not treat README language ("fixes" drift) as an evaluated result. See the [claims-allowed table](../../sdlc-spdd/docs/research/research-questions-and-constructs.md#4-claims-allowed-today-vs-after-milestone-2).
