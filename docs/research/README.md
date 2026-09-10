# Research notes

This folder is **not** a paper. It holds investigation notes that support either product integration or the academic program.

| Document | Kind | Use it when |
|----------|------|-------------|
| [Academic contribution bar (SPIKE-004 analysis)](../../sdlc-spdd/spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md) | Journal-style review of *this* repo as a research project | Raising claims from engineering/hobby to referee-safe |
| [Program plan (SPIKE-004 canvas)](../../sdlc-spdd/spdd/canvas/SPIKE-004-academic-contribution-bar.md) | REASONS canvas for Milestone 2 sequence | What to iterate, in what order |
| [Research questions and constructs (DOC-001)](../../sdlc-spdd/docs/research/research-questions-and-constructs.md) | Frozen RQs + construct spec + **academic review goal** | **Three storage modes** (ledger, SQLite, live Guide/Neo4j); mocked HTTP is not the graph; not reduced-drift; `embabel-dif` later |
| [C-RETRIEVE suite (TEST-003)](../../sdlc-spdd/docs/research/cretrieve-suite.md) | Persist→retrieve same id | Hermetic ledger + SQLite + mocked client; live graph required separately |
| [Related-work and novelty (DOC-002)](../../sdlc-spdd/docs/research/related-work-and-novelty.md) | Claim × system matrix | Positioning vs Fowler, SDLC Agents, Spec Kit, agents, classics |
| [Evaluation protocol (TEST-001)](../../sdlc-spdd/docs/research/evaluation-protocol.md) | Method eval protocol (no study data) | How to run slices: gold, raters, baselines, stop rules |
| [TEST-002 first slice log](../../tests/eval/test-002-hello/SLICE-LOG.md) | n=1 hello gold, protocol incomplete | C-DRIFT symbol-proxy 0 vs 0.333; C-PORT not reported; do not treat as evidence the method works |
| [Dogfood ledger policy (CHORE-003)](../../sdlc-spdd/docs/research/dogfood-ledger-policy.md) | Archive vs lessons.jsonl | Seeded decision/pitfall/pattern; retrieve is non-vacuous; not RQ4 usefulness |
| [Engine SUT (REF-001)](../../sdlc-spdd/docs/research/engine-sut.md) | Named gate semantics | Python `WorkflowEngine.gate_check`; `SDLC_GATE_ENGINE=shell` is not an eval condition |
| [Threats and replication (DOC-003)](../../sdlc-spdd/docs/research/threats-to-validity-and-replication.md) | Threats + **referee one-shot** | `./sdlc-spdd/docs/research/prove-academic-review.sh` (no Docker/Neo4j) |
| [Retrieve algorithm (FEAT-017)](../../sdlc-spdd/docs/research/retrieve-algorithm.md) | Lexical keyword-list vs title-body | C-CONTEXT relevance proxy; DICE still unmeasured |
| [Capture metrics queries (FEAT-015)](../../sdlc-spdd/docs/research/capture-metrics-queries.md) | `context metrics` construct queries | C-COMPLY / C-CONTEXT / C-REWORK / C-MEMORY |
| [code_maps_to_ops rule (FEAT-016)](../../sdlc-spdd/docs/research/code-maps-to-ops.md) | Automated Files: mapping + human C-DRIFT remainder | What gate_check enforces vs raters |
| [P0 structured checker](../../sdlc-spdd/docs/research/check_p0_artifacts.py) | Parser-based gate (not token grep) | `python3 -m unittest tests.research.test_p0_artifacts -v` |
| [P0 proof script](../../sdlc-spdd/docs/research/prove-p0.sh) | Machine gate per Work ID | Run before merging the next P0 item |
| [Academic-review proof](../../sdlc-spdd/docs/research/prove-academic-review.sh) | Referee replication | One command: P0 + TEST-003 + REF-001 + CHORE-003 |
| [Milestone 2 task list](../../sdlc-spdd/spdd/tasks/milestone-2-academic-hardening.md) | Iteration backlog | Picking the next Work ID |
| [Jira ADF and requirements sync](jira-adf-and-requirements-sync.md) | Product/integration research | Jira Cloud description payloads |
| [Kasana Agent Harness 2.0](kasana-agent-harness-2-0.md) | Product/integration research | Coding-agent harness vs SDLC-SPDD: match / differ / adopt. Not a DOC-002 matrix row |

TEST-002 recorded an n=1 protocol-incomplete comparison under `tests/eval/test-002-hello/`. Do not treat README language ("fixes" drift) as an evaluated result. Academic review of this repo is **three storage modes** + retrievability (DOC-001 §1). Live Guide+Neo4j is required for the graph mode. See the [claims-allowed table](../../sdlc-spdd/docs/research/research-questions-and-constructs.md#5-claims-allowed-today-vs-after-milestone-2).
