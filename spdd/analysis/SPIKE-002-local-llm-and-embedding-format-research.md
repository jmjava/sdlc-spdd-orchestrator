# SPIKE-002 — Confirmational Research (2026-06-19)

Design verification against the live guide MCP store and Embabel code corpus.
Sibling to SPIKE-001 research; same substrate, focused on the **model layer**.

Related: `spdd/canvas/SPIKE-002-local-llm-and-embedding-format.md`

## Method

- Live MCP: vector/text search + `embabel_agent_findClassSignatureBySimpleName`
- Corpus code paths: `UserModelFactory`, `OpenAiCompatibleModelFactory`, Ollama autoconfig,
  `DrivineStore.reembedAll`, `VectorIndexManager`
- Baseline store: 384-dim ONNX `all-MiniLM-L6-v2` on all chunks

## Design claims — verdicts

| Claim | Verdict | Evidence from store |
|-------|---------|---------------------|
| Generation LLM and embedding are independent knobs | **Confirmed** | Separate code paths; chat LLM vs `EmbeddingService` / ONNX ingest |
| Dimension change forces index drop + re-embed | **Confirmed** | `DrivineStore.reembedAll()`: "dimension-bound… drop + reprovision unconditionally" |
| `OpenAiCompatibleModelFactory` base-url seam | **Confirmed** | MCP signature: `getBaseUrl()`, `openAiCompatibleLlm(...)`, `openAiCompatibleEmbeddingService(...)` |
| Ollama as first-class Embabel integration | **Confirmed** | `embabel-agent-ollama-autoconfigure`, `OllamaNodeConfig.baseUrl`, model discovery |
| Fork `UserModelFactory` required for local LLM | **Refined** | Try `embabel-agent-ollama-autoconfigure` **before** custom `UserModelFactory` fork |
| ONNX 384-dim baseline; no LLM for plain embed | **Confirmed** | All chunks `all-MiniLM-L6-v2`; guide `application.yml` default |
| Local tool-capable LLM drives agentic flows | **Unproven (high risk)** | Ollama tool-loop tests exist; 12-Factor Agents warns production agents are mostly deterministic code + LLM at key points — smoke test required |
| Richer embedding justifies re-ingest | **Unproven** | RAG eval corpus: chunking strategy often matters more than dimension; isolate in A/B |
| Shared A/B method with SPIKE-001 | **Confirmed** | Same query substrate + FEAT-004 ledger framing |

## MCP spot-checks

| Query | Result |
|-------|--------|
| Ollama + OpenAI-compatible + embedding | `OllamaNodeConfig`, `OllamaEmbeddingModel` builder, per-node `baseUrl` registration |
| `OpenAiCompatibleModelFactory` | Full signature via code-structure MCP tool |
| `UserModelFactory` | Not in code-signature index (guide source not in menke dirs) — confirmed via repo read |
| Evals / retrieval measurement | Hamel field guide, evals FAQ — supports ledger + binary eval approach |

## Design refinements recorded

1. **T01 reorder:** evaluate `embabel-agent-ollama-autoconfigure` before forking `UserModelFactory`.
2. **T03/T04:** embedding A/B must vary chunking params (`max-chunk-size`, `overlap-size`) as well as model/dimension.
3. Local LLM is spike verification only — store shows integration, not quality guarantee.
4. LLM-driven `__Entity__` enrichment (SPIKE-001 leg 3) — defer unless local LLM smoke test passes.

## Still open (requires experiment)

- Ollama smoke test: tool calls + structured output vs `gpt-4.1-mini` latency
- 384-dim ONNX vs candidate embedder on fixed query set
- Cost/latency table (RTX 3060 12 GB; 32 GB Mac envelope)
