# Requirement: SPIKE-002-local-llm-and-embedding-format

## Summary

Time-boxed feasibility spike: evaluate running the make-it-fast retrieval backend
(Embabel **guide**) on **local models** — a local, tool-capable LLM served over an
OpenAI-compatible endpoint (Ollama / Docker) in place of a hosted model — and
**changing the embedding format** (e.g. the current 384-dim ONNX `all-MiniLM-L6-v2`
for a richer model such as 768-dim `nomic-embed-text`). Goal: lower/zero API cost and
better-controlled retrieval, without losing the tool-calling and retrieval quality the
agentic flows need.

## Source

- Roadmap: ROADMAP.md (make it fast — optimization; parked behind FEAT-004/005)
- Milestone: none (not part of milestone-1 / make it right)
- Sibling: SPIKE-001-guide-rag-context-backend (shares the retrieval A/B method + FEAT-004 ledger)

## Question to answer

1. Can a **local, tool-capable** LLM (via Ollama's OpenAI-compatible endpoint) drive
   guide's agentic/GOAP flows at acceptable quality + latency versus a hosted model
   (`gpt-4.1-mini`), at near-zero marginal cost?
2. Does **changing the embedding format** (e.g. 384-dim → 768-dim) measurably improve
   retrieval (recall/precision on known Work IDs) enough to justify the higher
   embedding cost/time and a vector-index rebuild + full re-ingest?

## Why a spike (not a feature)

Both choices have non-obvious trade-offs (local tool-calling fidelity; embedding-dim
changes force a full re-ingest and index migration) and touch the **guide fork**, not
the orchestrator's shipped surface. We want measured evidence and a recommended default
config before committing. The output is a **decision**, not production wiring.

## Success / decision criteria

- [ ] At least one local LLM (tool-capable, e.g. `qwen2.5-coder`) verified to drive guide's agentic flows (tool calls + structured output succeed), with latency noted.
- [ ] Retrieval A/B: current 384-dim ONNX vs. a candidate embedding format, scored for recall/precision/auditability on known queries (reuse SPIKE-001 method + FEAT-004 ledger).
- [ ] Cost/latency comparison: hosted vs. local LLM; ingest time and query latency per embedding model; hardware envelope recorded.
- [ ] Go / no-go with a recommended default (model + embedding format) and the trade-offs.

## Dependencies / sequencing

- Relates to SPIKE-001 (same retrieval substrate and scoring method); can share its harness.
- After FEAT-004 (ledger) exists — the scoreboard for retrieval quality.
- Independent of the make-it-right refactors except that they come first.

## Non-Goals

- No production integration; local models are **not** made the default for target projects.
- No change to the orchestrator's markdown-first default path.
- Not a benchmark of every model — just enough to make a defensible default choice.

## Next Step

When its turn comes (make it fast):

    /sdlc-spdd-architect @spdd/canvas/SPIKE-002-local-llm-and-embedding-format.md
