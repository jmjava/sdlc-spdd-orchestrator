# REASONS Canvas: SPIKE-002-local-llm-and-embedding-format - Local models + embedding format for the retrieval backend

## Metadata

- Work ID: SPIKE-002-local-llm-and-embedding-format
- Work Type: Spike
- Status: Draft
- Readiness: Needs Analysis
- Created: 2026-06-19
- Updated: 2026-06-19 (confirmational research via live MCP store)
- Owner:
- Target Project: sdlc-spdd-orchestrator (self / dogfood) + Embabel guide fork
- Stack: Bash + Markdown harness ↔ JVM (Embabel guide) + Neo4j + ONNX/Ollama, over MCP (SSE)
- Source System: Roadmap
- Roadmap: ROADMAP.md
- Milestone:
- Delivery stage: make it fast (optimization) — **spike, parked behind FEAT-004/005**
- Time-box: 1–2 focused sessions
- Related PR:
- Related Work: SPIKE-001-guide-rag-context-backend (shared retrieval A/B + FEAT-004 ledger)

## R - Requirements

### User Goal

Find out whether the make-it-fast retrieval backend can run on **local models** — a
local tool-capable LLM (Ollama/Docker, OpenAI-compatible) and a **changed embedding
format** — at lower/zero API cost and better-controlled retrieval, without losing the
tool-calling or retrieval quality the agentic flows need.

### Business / Product Goal

De-risk a self-hosted, low-cost retrieval/agent stack with evidence. Produce a go/no-go
and a recommended default (LLM + embedding format) for the optimization phase.

### Framing: two independent knobs

1. **Generation LLM** — guide resolves the chat/agent LLM per-user (BYOK) via
   `UserModelFactory`, which uses Embabel's `OpenAiCompatibleModelFactory(baseUrl, …)`.
   A local endpoint (Ollama `http://localhost:11434/v1`) is a base-url swap. Agentic
   flows need **tool calling + structured output**, so the model must support tools.
2. **Embedding format** — ingestion currently embeds with ONNX `all-MiniLM-L6-v2`
   (384-dim) into the Neo4j `Chunk.embedding` vector index. Changing the model (e.g.
   `nomic-embed-text`, 768-dim) changes index dimensions and forces a full re-ingest.

These are separable: the embedding model drives **retrieval quality**; the generation
LLM drives **answer/agent quality + cost**. The spike measures each.

### Hypothesis

A local tool-capable LLM (e.g. `qwen2.5-coder`) can drive guide's agentic flows at
acceptable quality/latency for near-zero cost; and a richer embedding format (e.g.
768-dim) improves retrieval enough on real queries to justify the re-ingest — making a
fully local, low-cost retrieval backend viable for the optimization direction.

### Decision Criteria (what "done" means)

- [ ] One local LLM verified driving guide's agentic flows (tool calls + structured output succeed); latency recorded vs. `gpt-4.1-mini`.
- [ ] Retrieval A/B: 384-dim ONNX vs. one candidate embedding format, scored for recall/precision + auditability on known queries (reuse SPIKE-001 method + FEAT-004 ledger).
- [ ] Cost/latency table: hosted vs. local LLM; ingest time + query latency per embedding model; hardware envelope (e.g. RTX 3060 12 GB vs. 32 GB Mac).
- [ ] Written go/no-go with a recommended default (model + embedding format) and trade-offs.

### Non-Goals

- No production integration; local models are **not** the default for target projects.
- No change to the orchestrator's markdown-first default path.
- Not an exhaustive model benchmark — just enough for a defensible default.

### Assumptions

- guide resolves the LLM via `OpenAiCompatibleModelFactory(baseUrl, …)` — confirmed in `UserModelFactory.kt` (OPENAI/MISTRAL/DEEPSEEK branches all pass a base-url).
- Ingestion embeds via local ONNX (`embabel.models.default-embedding-model: all-MiniLM-L6-v2`, 384-dim) — confirmed in guide `application.yml`; no LLM is used for plain embedding.
- Ollama is available locally (`v0.13`, endpoint `:11434/v1`); this host has an RTX 3060 (12 GB) + 62 GB RAM.
- Changing embedding dimensions requires dropping/recreating the `Chunk` vector index and a full re-ingest (observed: existing 1536-dim index vs. 384-dim ONNX mismatch this session).
- FEAT-004 ledger is available (or co-stubbed) as the retrieval scoreboard.

### Open Questions

- Which local LLMs clear Embabel's tool-calling/structured-output bar? (Lean: Qwen2.5 / Qwen2.5-Coder, Llama 3.1; DeepSeek-R1 likely fails tools.)
- Does the embedding gain (if any) come from dimension, model quality, or chunking params (`max-chunk-size`, `overlap-size`)? Isolate before recommending.
- Is an LLM-driven ingest enrichment step (entity/`__Entity__` graph extraction) worth running locally — connecting to SPIKE-001's DICE leg?
- Make the LLM base-url / embedding model **config-driven** (env/property) vs. fork code edits? **Research lean (2026-06-19):** try `embabel-agent-ollama-autoconfigure` before forking `UserModelFactory`.

### Confirmational Research (2026-06-19)

Full notes: `spdd/analysis/SPIKE-002-local-llm-and-embedding-format-research.md`

Design verification against live guide MCP + Embabel code corpus (same substrate as
SPIKE-001; 384-dim ONNX baseline on all chunks).

| Design element | Verdict |
|----------------|---------|
| Two independent knobs (LLM vs embedding) | ✅ Confirmed in `DrivineStore` / chat-store code |
| Dimension change → index drop + re-embed | ✅ Confirmed (`reembedAll`, `VectorIndexManager`) |
| `OpenAiCompatibleModelFactory` base-url seam | ✅ Confirmed via MCP code signature |
| `embabel-agent-ollama-autoconfigure` | ✅ First-class module — try before `UserModelFactory` fork |
| ONNX 384-dim ingest baseline | ✅ Confirmed on all chunks |
| Local LLM drives agentic flows | ⏳ Unproven — integration exists; quality needs smoke test |
| Richer embedding justifies re-ingest | ⏳ Unproven — isolate chunking vs dimension in A/B |
| Shared A/B with SPIKE-001 + FEAT-004 ledger | ✅ Confirmed |

**T01 refinement:** evaluate Ollama autoconfig before custom `UserModelFactory` changes.
**T03/T04 refinement:** vary chunking params (`max-chunk-size`, `overlap-size`) alongside
embedding model in the A/B.

## E - Entities

### Application Components

- guide `UserModelFactory` / `UserLlmResolver` (BYOK LLM resolution; base-url seam)
- Embabel `OpenAiCompatibleModelFactory` (OpenAI-compatible LLM factory)
- guide ONNX embedding service (`all-MiniLM-L6-v2`, 384-dim) + content chunker
- Ollama (local OpenAI-compatible server, `:11434/v1`) serving candidate LLMs/embedders

### External Systems

- Neo4j (guide's RAG store; `Chunk.embedding` vector index — dimension-sensitive)
- Ollama model registry (local)

### Data / Persistence

- Neo4j `Chunk`/`ContentElement` RAG store; vector index dimension tied to embedding model
- Reference corpus (curated reading) cataloged in `spdd/analysis/SPIKE-retrieval-reference-corpus.md`, ingested via guide profile `menke-2`
- Throwaway / local only for the spike

### Domain Entities

- Candidate LLMs (e.g. `qwen2.5-coder:7b/14b`, `deepseek-coder-v2:16b`)
- Candidate embedding models (e.g. `all-MiniLM-L6-v2` 384, `nomic-embed-text` 768)
- Metrics: tool-call success, retrieval recall/precision, ingest time, query latency, $/run

## A - Approach

### Proposed Approach (experiment)

1. Evaluate `embabel-agent-ollama-autoconfigure` and config-driven base-url first; fork `UserModelFactory` only if autoconfig is insufficient. Point chat LLM at Ollama (`:11434/v1`).
2. Pull 1–2 tool-capable local LLMs via Ollama; smoke-test guide's agentic flows (confirm tool calls + structured output succeed); record latency.
3. Swap the embedding model to a candidate format; adjust the `Chunk` vector index dimensions; re-ingest a representative subset of the corpus.
4. Retrieval A/B: current 384-dim ONNX vs. the candidate, on a fixed set of known queries — score recall/precision + auditability; vary chunking params as well as model/dimension (reuse SPIKE-001 harness + FEAT-004 ledger).
5. Record cost/latency: hosted vs. local LLM; ingest time + query latency per embedding model; note the hardware envelope.
6. Write go/no-go with a recommended default (LLM + embedding format) and trade-offs.

### Alternatives Considered

- Keep hosted LLM + 384-dim ONNX (the baseline / no-go).
- LLM-driven ingest enrichment (entity extraction) — deferred; only if it clearly helps the DICE leg (SPIKE-001).

### Risks

- Local tool-calling fidelity varies by model/template (Ollama) — agentic flows may degrade; verify explicitly.
- Embedding-format change forces a full re-ingest + index rebuild (time/cost); isolate the true source of any gain (dim vs. model vs. chunking).
- Resource contention: running a local LLM + Neo4j + ingest on one box.
- Small-sample A/B is directional, not conclusive.

## S - Structure

### Files To Add

- Confirmational research (done): `spdd/analysis/SPIKE-002-local-llm-and-embedding-format-research.md`
- A/B findings note (pending): `spdd/analysis/SPIKE-002-local-llm-and-embedding-format-analysis.md`

### Files To Modify

- None in the orchestrator framework (spike is exploratory). Fork-only, throwaway: a config-driven base-url/embedding switch in guide's `UserModelFactory` / `application.yml`.

### Documentation Structure

- Findings + decision recorded in the analysis note and this canvas's Sync Notes.

## O - Operations

### T01 - Make guide's LLM base-url configurable (local endpoint)

- Status: Not Started
- Description: Try `embabel-agent-ollama-autoconfigure` + config-driven base-url first; fork `UserModelFactory` only if needed. Route chat LLM through Ollama (`http://localhost:11434/v1`).
- Files: (guide fork; no orchestrator changes)
- Validation: guide boots and resolves a local model for chat

### T02 - Verify a tool-capable local LLM drives agentic flows

- Status: Not Started
- Description: Pull 1–2 models via Ollama (e.g. `qwen2.5-coder:14b`); run guide's agentic flow; confirm tool calls + structured output succeed; record latency.
- Files: (Ollama; guide config)
- Validation: Agentic flow completes with successful tool calls; latency noted

### T03 - Swap embedding format and re-ingest a subset

- Status: Not Started
- Description: Point ingestion at a candidate embedder (e.g. `nomic-embed-text`, 768-dim); recreate the `Chunk` vector index at the new dimension; re-ingest a representative subset.
- Files: (guide `application.yml`; Neo4j index)
- Validation: Subset ingested; vector index ONLINE at the new dimension

### T04 - Retrieval A/B on known queries

- Status: Not Started
- Description: Compare 384-dim ONNX vs. the candidate on a fixed query set; score recall/precision + auditability; record on the FEAT-004 ledger.
- Files: spdd/analysis/SPIKE-002-local-llm-and-embedding-format-analysis.md
- Validation: Both embedding formats scored on the same queries; results comparable

### T05 - Cost / latency / hardware measurements

- Status: Not Started
- Description: Measure hosted vs. local LLM latency + $; ingest time and query latency per embedding model; record the hardware envelope (RTX 3060 12 GB; 32 GB Mac).
- Files: spdd/analysis/SPIKE-002-local-llm-and-embedding-format-analysis.md
- Validation: Cost/latency table complete for each candidate

### T06 - Write go / no-go recommendation

- Status: Not Started
- Description: Summarize evidence + trade-offs; recommend a default (LLM + embedding format); note when local is worth it.
- Files: spdd/analysis/SPIKE-002-local-llm-and-embedding-format-analysis.md, this canvas Sync Notes
- Validation: Clear decision with rationale and a recommended default config

## N - Norms

### General

- Time-boxed: stop at the decision, do not slide into building the integration.
- No production dependency added during the spike; local models stay opt-in.
- Markdown-first default path stays intact; orchestrator framework unchanged.

## S - Safeguards

- Exploratory: do not make local models the default for target projects under this Work ID.
- Keep all guide/Ollama/Neo4j setup local/throwaway; no secrets committed.
- If "go", real integration is a separate FEAT with its own canvas.
- Posture/optimization framing stays internal; nothing ships to target projects from this spike.

## Review Checklist

- [ ] Question answered with evidence (local LLM + embedding format)
- [ ] Decision criteria met
- [ ] Trade-offs documented (quality vs. cost vs. latency vs. re-ingest)
- [ ] Go / no-go recorded with a recommended default
- [ ] Follow-on FEAT(s) sketched if go
- [ ] No production wiring left behind
- [ ] No secrets committed

## Sync Notes

Sibling to SPIKE-001: same retrieval substrate (guide/Neo4j) and scoring method
(FEAT-004 ledger), but focused on the **model layer** — local tool-capable LLM via
Ollama and embedding-format change (384-dim ONNX → candidate), which drives retrieval
quality and forces index rebuild + re-ingest.

**Confirmational research 2026-06-19:** two-knob separation and re-embed cost validated
in corpus; Ollama autoconfig may avoid `UserModelFactory` fork. Local LLM quality and
embedding upgrade value still require smoke test + A/B. Full notes in
`spdd/analysis/SPIKE-002-local-llm-and-embedding-format-research.md`.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
