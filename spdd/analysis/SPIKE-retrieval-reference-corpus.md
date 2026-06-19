# Reference Corpus — Retrieval Spikes (SPIKE-001 / SPIKE-002)

Catalog of the external reference material ingested into the guide/Neo4j RAG store to
support the make-it-fast retrieval spikes. This is the **reference half** of the corpus
(curated reading); the **code half** is the local fork repos in guide's `menke` profile.

- **Supports:** `spdd/canvas/SPIKE-001-guide-rag-context-backend.md` (DICE hybrid retrieval),
  `spdd/canvas/SPIKE-002-local-llm-and-embedding-format.md` (local models + embedding format).
- **Ingested via:** guide profile `menke-2` (`guide/scripts/user-config/application-menke-2.yml`),
  as a second **append** pass on top of the main `menke` ingest:

      GUIDE_PROFILE=menke-2 ./scripts/append-ingest.sh

- **Stage:** make it fast (optimization). Local/throwaway; nothing ships to target projects.

## Why these sources

Two themes drive the selection, mirroring the orchestrator's own work:

1. **SPDD & AI-assisted delivery** — the method this framework implements (Structured
   Prompt-Driven Development) and the broader practice of governing AI-assisted coding.
2. **Context engineering, agents, and evals** — the make-it-fast direction: selecting the
   right context, building reliable agents, and *measuring* improvement (ties to FEAT-004).

A third, smaller theme covers **software-quality craft** (readability/maintainability —
the make-it-right canon), echoing Chelsea Troy's testing/maintenance writing.

## Catalog

### SPDD — Structured Prompt-Driven Development (the method this framework implements)

| Source | What it is | Why referenced |
|--------|-----------|----------------|
| martinfowler.com/articles/structured-prompt-driven/ | Fowler/Thoughtworks — canonical SPDD article | Defines SPDD + the REASONS Canvas this repo is built on |
| engineered.at/articles/structured-prompt-driven-development-spdd | SPDD summary / takeaways | Concise framing of prompts-as-artifacts |
| mgks.dev/blog/2026-04-29-treating-ai-prompts-like-code-… | Practitioner walkthrough of the SPDD method | Real example of the `/spdd-*` workflow loop |
| github.com/gszhangwei/open-spdd | OpenSPDD CLI (reference implementation) | Tooling that implements the SPDD lifecycle (backlog: OpenSPDD compatibility) |

### Chelsea Troy — LLMs, context, testing, maintenance

| Source | What it is | Why referenced |
|--------|-----------|----------------|
| chelseatroy.com/2025/07/14/what-can-we-expect-of-llms-as-software-engineers/ | LLMs as engineers; lost-in-the-middle | Grounds the context-selection rationale for make-it-fast |
| chelseatroy.com/2021/01/18/avoiding-technical-debt/ | Tech-debt / "maintenance load" series | make-it-right: maintainability mindset |
| chelseatroy.com/2023/02/07/on-code-coverage-tools/ | Coverage as a sentinel metric | Measurement discipline (ties to FEAT-004/005) |
| chelseatroy.com/2020/01/06/posd-2-debugging-tactics/ | Debugging tactics (Philosophy of Software Design) | Craft / systematic analysis |

### AI-assisted delivery — Birgitta Böckeler / Thoughtworks "Exploring Gen AI"

| Source | What it is | Why referenced |
|--------|-----------|----------------|
| martinfowler.com/articles/exploring-gen-ai.html | Series index (context engineering, spec-driven dev, internal quality with an agent) | Closest match to all three Beck stages at once |
| martinfowler.com/articles/exploring-gen-ai/i-still-care-about-the-code.html | Risk-assessment mindset for AI-generated code | The "review wet cement" posture in our README |

### Context engineering & coding agents — Simon Willison

| Source | What it is | Why referenced |
|--------|-----------|----------------|
| simonwillison.net/2025/Mar/11/using-llms-for-code/ | Practical coding-agent workflow | How practitioners actually drive coding agents |
| simonwillison.net/2025/Jun/16/the-lethal-trifecta/ | Agent security (data + untrusted content + exfil) | Safeguards for any live retrieval/agent wiring |
| simonwillison.net/2025/Jul/3/faqs-about-ai-evals/ | Evals FAQ (link post) | Reinforces evals as the reliability lever |

### Agents / context budget — Dex Horthy

| Source | What it is | Why referenced |
|--------|-----------|----------------|
| github.com/humanlayer/12-factor-agents | "12-Factor Agents" + frequent intentional compaction | Context-budget / "dumb zone" model for make-it-fast |

### Evals / measuring optimization (ties to FEAT-004 ledger) — Hamel Husain

| Source | What it is | Why referenced |
|--------|-----------|----------------|
| hamel.dev/blog/posts/evals/ | "Your AI Product Needs Evals" | Canonical case for measuring before optimizing |
| hamel.dev/blog/posts/field-guide/ | "A Field Guide to Rapidly Improving AI Products" | Error analysis + data flywheel = the ledger's purpose |
| hamel.dev/blog/posts/evals-faq/ | Evals FAQ | Practical eval design |

### Context engineering reading

| Source | What it is | Why referenced |
|--------|-----------|----------------|
| henryvu.blog/series/ai-engineering/part1.html | "What fills the context window" — 7 components | Decomposition of context assembly |
| sourcegraph.com/blog/context-engineering | Context engineering practical guide (2026) | Prompt vs. context engineering layering |

### Software quality / craft (make-it-right canon)

| Source | What it is | Why referenced |
|--------|-----------|----------------|
| tidyfirst.substack.com | Kent Beck — "Tidy First?" | Source of the make-it-work/right/fast posture |
| martinfowler.com | Refactoring / evolutionary design (landing) | make-it-right reference canon |

### Broader AI engineering (landing pages — verify ingest depth)

| Source | What it is | Why referenced |
|--------|-----------|----------------|
| eugeneyan.com | LLM systems, evals, RAG patterns | Systems view of RAG/evals |
| anthropic.com/engineering | "Building effective agents," context engineering | Vendor guidance on agents/context |
| philschmid.de | Agents, context engineering | Practitioner agent/context posts |

## Caveats

- **Landing/index pages** (`eugeneyan.com`, `anthropic.com/engineering`, `philschmid.de`,
  `martinfowler.com`, `tidyfirst.substack.com`): ingestion may capture the index rather
  than every article. Swap in specific post URLs if a source proves high-value.
- **Fetch blocks:** some hosts (Medium-style, Substack, Cloudflare-fronted) may refuse the
  fetcher. Ingestion fails-and-continues per URL, so a block won't break the run — check the
  ingest summary for skipped URLs.
- **Embeddings:** local ONNX `all-MiniLM-L6-v2` (384-dim), consistent with the main ingest.

## Maintenance

The source of truth for the actual ingest list is
`guide/scripts/user-config/application-menke-2.yml` (`guide.content.supplementary`). Keep
this catalog in sync when adding/removing URLs there.
