---
docgen:
  segment:
    create: true
    id: "03"
    stem: 03-guide-rag-dogfood
  wiring:
    narration:
      hints:
        - >-
          Explain why this repo uses Embabel Guide + Neo4j as a local research backend during
          /sdlc-spdd-analysis instead of pasting large external docs into every prompt.
        - >-
          Summarize the layered menke profiles: menke (code repos), menke-2 (SPDD and context
          engineering URLs), menke-3 (framework depth), menke-4 (docgen + course-builder docs)
          — each an append pass on the same store.
        - >-
          Describe MCP usage: docs_vectorSearch for concepts, docs_textSearch for exact CLI
          flags; cite chunk URIs in spdd/analysis artifacts.
        - >-
          Present the dogfood table: SPDD on self, docgen on self (this bundle), Guide on self,
          posture guard keeping templates clean.
        - >-
          State clearly what does not ship to target projects: Guide YAML, Neo4j, MCP wiring,
          .venv, regenerable docgen outputs.
      context:
        paths:
          - docs/guide-rag-research-and-dogfooding.md
          - spdd/analysis/SPIKE-retrieval-reference-corpus.md
          - spdd/canvas/SPIKE-001-guide-rag-context-backend.md
          - docs/context-loading-and-scaling.md
    visual:
      type: manim
      class: GuideRagDogfoodScene
    manim_scene:
      hints:
        - >-
          Title "Guide RAG & Dogfooding" at top. Horizontal row of four profile pills:
          menke, menke-2, menke-3, menke-4 (green for code, blue for reference layers).
        - >-
          Below: box for MCP vector + text search, then box for SPDD + docgen + Guide dogfood on self.
        - >-
          One FadeIn per mobject; teal accent for title. Pace to timing.json when present.
---

# Segment 03 — Guide RAG and dogfooding (editorial notes, not narrated)

Meta-documentation for framework contributors. Manim visual: GuideRagDogfoodScene.
